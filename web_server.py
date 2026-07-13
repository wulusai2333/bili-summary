"""bili-summary Web UI 后端"""

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

# 确保 ffmpeg 在 PATH 中
_FFMPEG_DIRS = [
    r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Links",
    r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin",
]
for _d in _FFMPEG_DIRS:
    if _d not in os.environ.get("PATH", ""):
        os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")
        os.add_dll_directory(_d)

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

PROJECT_DIR = Path(__file__).parent
OUTPUT_DIR = PROJECT_DIR / "output"
AUDIO_DIR = OUTPUT_DIR / "audio"
TRANSCRIPT_DIR = OUTPUT_DIR / "transcript"
SUMMARY_DIR = OUTPUT_DIR / "summary"
TEMP_DIR = PROJECT_DIR / "temp_uploads"

for d in [AUDIO_DIR, TRANSCRIPT_DIR, SUMMARY_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="bili-summary")

_jobs: dict[str, dict] = {}
_job_logs: dict[str, list[str]] = {}


def _load_env():
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key not in os.environ:
            os.environ[key] = val


_load_env()

# --- 把项目路径加入 sys.path ---
sys.path.insert(0, str(PROJECT_DIR))
from download import download, download_playlist
from transcribe import transcribe
from summarize import summarize_file


def _log(job_id: str, msg: str):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    _job_logs.setdefault(job_id, []).append(line)
    print(line)


def run_pipeline(
    job_id: str,
    url: str | None,
    file_path: str | None,
    preset: str,
    model: str,
    no_summary: bool,
):
    try:
        _jobs[job_id]["status"] = "running"

        # 1. 音频准备
        if file_path:
            _log(job_id, "准备本地音频...")
            _jobs[job_id]["stage"] = "准备音频"
            if file_path.endswith(".mp4"):
                audio_path = TEMP_DIR / f"{job_id}.m4a"
                subprocess.run(
                    ["ffmpeg", "-i", file_path, "-vn", "-acodec", "aac", str(audio_path), "-y"],
                    capture_output=True, check=True,
                )
            else:
                ext = Path(file_path).suffix
                audio_path = TEMP_DIR / f"{job_id}{ext}"
                shutil.copy(file_path, audio_path)
            audio_files = [audio_path]
            _log(job_id, "音频准备完成")
        el        if url:
            _log(job_id, f"下载音频: {url}")
            _jobs[job_id]["stage"] = "下载音频"
            audio_files = download(url, str(AUDIO_DIR))
            _log(job_id, f"下载完成 ({len(audio_files)} 个)")
        else:
            raise ValueError("请提供视频链接或上传文件")

        # 2. 转录
        _jobs[job_id]["stage"] = "语音转文字"
        _jobs[job_id]["total"] = len(audio_files)
        txt_files = []
        for i, audio in enumerate(audio_files):
            _jobs[job_id]["progress"] = i
            _log(job_id, f"转录 ({i+1}/{len(audio_files)}): {Path(audio).name}")
            result = transcribe(str(audio), model, device="auto")
            txt_files.append(Path(result["output_path"]))
            _log(job_id, f"  -> {result['output_path']}")

        # 3. 总结
        if not no_summary:
            _jobs[job_id]["stage"] = "AI 总结"
            for i, txt in enumerate(txt_files):
                _jobs[job_id]["progress"] = len(audio_files) + i
                _log(job_id, f"总结 ({i+1}/{len(txt_files)}): {txt.name}")
                summarize_file(str(txt), preset=preset)

        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["stage"] = "完成"
        _log(job_id, "全部完成!")

        # 收集结果
        result_files = {
            "audio": [{"name": f.name, "size": f.stat().st_size} for f in AUDIO_DIR.glob("*.m4a")],
            "transcript": [{"name": f.name, "size": f.stat().st_size} for f in TRANSCRIPT_DIR.glob("*.txt")],
            "summary": [{"name": f.name, "size": f.stat().st_size} for f in SUMMARY_DIR.glob("*.md")],
        }
        _jobs[job_id]["results"] = result_files
    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        _log(job_id, f"错误: {e}")


@app.get("/")
def index():
    return HTMLResponse((PROJECT_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/api/run")
def api_run(
    url: str = Form(""),
    preset: str = Form("notes"),
    model: str = Form("large-v3"),
    no_summary: bool = Form(False),
    file: UploadFile | None = File(None),
):
    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {"status": "pending", "progress": 0, "total": 0, "stage": "初始化"}
    _job_logs[job_id] = []

    fpath = None
    if file and file.filename:
        suffix = Path(file.filename).suffix or ".m4a"
        fpath = TEMP_DIR / f"{job_id}{suffix}"
        with open(fpath, "wb") as f:
            f.write(file.file.read())

    t = threading.Thread(
        target=run_pipeline,
        args=(job_id, url or None, str(fpath) if fpath else None, preset, model, no_summary),
        daemon=True,
    )
    t.start()

    return {"job_id": job_id}


@app.get("/api/progress/{job_id}")
def api_progress(job_id: str):
    def stream():
        last = 0
        while True:
            job = _jobs.get(job_id)
            if not job:
                break
            logs = _job_logs.get(job_id, [])
            new_logs = logs[last:]
            last = len(logs)
            data = {
                "status": job["status"],
                "stage": job.get("stage", ""),
                "progress": job.get("progress", 0),
                "total": job.get("total", 0),
                "logs": new_logs,
                "error": job.get("error", ""),
                "results": job.get("results"),
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            if job["status"] in ("done", "failed"):
                break
            time.sleep(1)
    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/api/download/{category}/{filename}")
def api_download(category: str, filename: str):
    dirs = {"audio": AUDIO_DIR, "transcript": TRANSCRIPT_DIR, "summary": SUMMARY_DIR}
    d = dirs.get(category)
    if not d:
        return {"error": "未知类别"}
    path = d / filename
    if not path.exists():
        return {"error": "文件不存在"}
    return FileResponse(path, filename=filename)


@app.get("/api/files")
def api_files():
    return {
        "audio": [f.name for f in AUDIO_DIR.glob("*.m4a")],
        "transcript": [f.name for f in TRANSCRIPT_DIR.glob("*.txt")],
        "summary": [f.name for f in SUMMARY_DIR.glob("*.md")],
    }

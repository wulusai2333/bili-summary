"""Bilibili → 音频 → 转文字 → DeepSeek 总结

用法:
    python main.py BV1xxx                          # 单个视频
    python main.py BV1xxx --playlist --start 1 --end 10  # 合集
    python main.py https://www.bilibili.com/video/BV1xx   # 完整 URL

环境变量:
    DEEPSEEK_API_KEY    DeepSeek API Key（必需）
    HTTP_PROXY          代理地址（可选）
"""

import argparse
import os
import sys
from pathlib import Path


def _load_env():
    """加载项目根目录的 .env 文件。"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


_load_env()

from download import download, download_playlist
from transcribe import transcribe
from summarize import summarize_file


def normalize_url(raw: str) -> str:
    if raw.startswith("BV"):
        return f"https://www.bilibili.com/video/{raw}"
    if "bilibili.com" in raw:
        return raw
    return f"https://www.bilibili.com/video/{raw}"


def main():
    parser = argparse.ArgumentParser(
        description="Bilibili 视频 → 音频 → 转文字 → DeepSeek 总结",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py BV1xxx
  python main.py BV1xxx --playlist --start 1 --end 5
  python main.py BV1xxx --no-summary          # 只转文字
  python main.py BV1xxx --prompt "用日语总结"  # 自定义提示词
        """,
    )
    parser.add_argument("url", help="B 站视频 URL 或 BV 号")
    parser.add_argument("-o", "--output", default=None, help="输出目录")
    parser.add_argument("-m", "--model", default="large-v3", help="Whisper 模型大小")
    parser.add_argument("-k", "--api-key", default=None, help="DeepSeek API Key")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--llm-model", default="deepseek-chat", help="总结模型")
    parser.add_argument("--prompt", default=None, help="自定义总结提示词")
    parser.add_argument("-p", "--preset", default="structured", help="总结预设 (structured/notes/brief/timeline/action)")
    parser.add_argument("--proxy", default=None, help="代理地址")
    parser.add_argument("--no-summary", action="store_true", help="跳过总结")
    parser.add_argument("--no-download", action="store_true", help="跳过下载(直接转录已有音频)")
    parser.add_argument("--no-transcribe", action="store_true", help="跳过转录(直接总结已有文本)")
    # 合集选项
    parser.add_argument("--playlist", action="store_true", help="下载整个合集")
    parser.add_argument("--start", type=int, default=1, help="起始分 P")
    parser.add_argument("--end", type=int, default=None, help="结束分 P")

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("DEEPSEEK_API_KEY")
    if not args.no_summary and not api_key:
        print("错误: 需要 DEEPSEEK_API_KEY 环境变量或 -k 参数")
        sys.exit(1)

    url = normalize_url(args.url)
    out_dir = Path(args.output) if args.output else Path("output")
    audio_dir = out_dir / "audio"

    # --- 步骤 1: 下载音频 ---
    if args.no_download:
        audio_files = sorted(audio_dir.glob("*.m4a")) if audio_dir.exists() else []
        if not audio_files:
            print(f"错误: 未找到已有音频文件 ({audio_dir})，请先下载")
            sys.exit(1)
        print(f"[跳过下载] 找到 {len(audio_files)} 个已有音频")
    else:
        proxy = args.proxy or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        if args.playlist or args.end:
            audio_files = download_playlist(url, str(audio_dir), args.start, args.end, proxy)
        else:
            audio_files = download(url, str(audio_dir), proxy)

    if not audio_files:
        print("错误: 没有下载到任何音频文件")
        sys.exit(1)

    # --- 步骤 2: 语音转文字 ---
    if args.no_transcribe:
        transcript_dir = out_dir / "transcript"
        txt_files = sorted(transcript_dir.glob("*.txt")) if transcript_dir.exists() else []
        print(f"[跳过转录] 找到 {len(txt_files)} 个已有文本")
    else:
        txt_files = []
        for audio in audio_files:
            result = transcribe(str(audio), args.model, device="auto")
            txt_files.append(Path(result["output_path"]))

    if not txt_files:
        print("错误: 没有找到转录文本")
        sys.exit(1)

    # --- 步骤 3: DeepSeek 总结 ---
    if args.no_summary:
        for f in txt_files:
            print(f"[跳过总结] {f}")
    else:
        for f in txt_files:
            summarize_file(str(f), api_key, args.base_url, args.llm_model, args.prompt, args.preset, out_dir)

    print(f"\n完成! 文件在: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

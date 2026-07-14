# AGENTS.md

## Project overview

Flat Python script repo: Bilibili video → download audio (yt-dlp) → transcribe (faster-whisper) → summarize (DeepSeek API). No tests, no CI, no build system. Dual platform: Windows (native) & WSL/Linux.

## Quick start

```bash
# WSL / Linux
bash run.sh BV1xxx
bash run.sh --preset notes --no-summary

# Windows
run.bat BV1xxx
run.bat --preset notes --no-summary
# or: python main.py BV1xxx
```

## Commands

```bash
# Environment check
python env_check.py

# CLI pipeline
python main.py BV1xxx
python main.py BV1xxx --preset notes --no-summary

# Web UI (WSL)
pip install fastapi uvicorn python-multipart    # one-time into .venv
python web_server.py
python -m uvicorn web_server:app --host 0.0.0.0 --port 8765

# Individual stages
python download.py BV1xxx
python transcribe.py audio.m4a -m small
python summarize.py transcript.txt -p notes
```

## Architecture

```
main.py          orchestrator (argparse, pipeline)
web_server.py    FastAPI UI (thread-per-job, SSE progress)
download.py      yt-dlp subprocess wrapper
transcribe.py    faster-whisper (auto GPU/CPU)
summarize.py     DeepSeek via openai SDK, preset TOML
env_check.py     dependency checker
run.sh           WSL/Linux launcher (activates .venv)
run.bat          Windows launcher
```

Output structure: `output/audio/`, `output/transcript/`, `output/summary/`

## Key gotchas

- **`run.sh` / `run.bat`** — use the launcher scripts. WSL uses `.venv/bin/python`, Windows uses system `python`. Both scripts set `HF_ENDPOINT` mirror env vars.
- **`.venv/` at project root** — on WSL this is a Linux venv inside the shared `D:` drive. Windows ignores it (use system Python on Windows). Already in `.gitignore`.
- **ffmpeg must be in `PATH`** — WSL: `sudo apt install ffmpeg`. Windows: `winget install ffmpeg`.
- **`.env` loaded at import time** — each module calls `_load_env()` at module level before anything imports it. This means env vars are set by the time `main()` runs, but only if the module is imported (not if you run `summarize.py` directly without the env).
- **`tomllib` requires Python 3.11+** — README says 3.10+ but `summarize.py` uses `tomllib` which was added in 3.11.
- **Whisper model auto-downloads ~3GB on first run** — cached to the HuggingFace hub cache. Set `HF_ENDPOINT=https://hf-mirror.com` in `.env` to avoid timeouts in mainland China.
- **WSL GPU requires extra pip packages** — `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` (Linux/WSL only). `run.sh` sets `LD_LIBRARY_PATH` so ctranslate2 can find `libcublas.so.12`. Without these, GPU detection succeeds but actual encoding fails with `RuntimeError: Library libcublas.so.12 is not found`.
- **No test suite exists** — verify changes by running `python env_check.py` and a quick `python download.py BV1xxx` on a known-good BV号.

## Adding/editing presets

Edit `summary_presets.toml`. Presets use a Jinja2-like template syntax (`{{% if has_timestamps %}}` blocks) parsed by simple regex in `summarize.py:build_prompt()`. Not actual Jinja2 — do not add complex template logic.

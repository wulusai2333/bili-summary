# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flat Python script repo (no packages, no tests, no CI, no build system). Pipeline: Bilibili video → download audio (yt-dlp) → transcribe (faster-whisper) → summarize (DeepSeek API). Two entry points: CLI (`main.py`) and a FastAPI web UI (`web_server.py`). Dual-platform: Windows native + WSL/Linux. Code comments, output, and UI text are in Chinese. `AGENTS.md` and `SKILL.md` cover the same project from an agent/skill angle; keep them in sync when architecture changes.

## Commands

Prefer the launcher scripts in normal operation — they activate the venv, pre-check the Whisper model cache (`ensure_model.py`, auto-downloads if missing), and set the GPU library paths:

```bash
bash run.sh BV1xxx                        # WSL/Linux CLI (uses .venv/bin/python)
run.bat BV1xxx                            # Windows CLI (uses system python)
```

Environment check and individual pipeline stages (each module is runnable standalone):

```bash
python env_check.py                       # dependency checker; exit 0 = ready
python main.py BV1xxx                     # CLI pipeline (structured preset by default)
python main.py BV1xxx --preset notes --no-summary
python main.py BV1xxx --playlist --start 1 --end 5   # 合集 (passing --end alone also triggers playlist)
python download.py BV1xxx                 # stage 1 only
python transcribe.py audio.m4a -m small   # stage 2 only
python summarize.py transcript.txt -p notes  # stage 3 only (needs DEEPSEEK_API_KEY in env)
```

Web UI:

```bash
pip install fastapi uvicorn python-multipart   # one-time; NOT in requirements.txt
bash run_web.sh      # start (pre-checks model; PORT env overrides default 8765)
bash stop_web.sh     # stop (kills only the port-8765 listener)
python -m uvicorn web_server:app --host 0.0.0.0 --port 8765   # or run web_server.py directly
```

There is no test suite. Verify changes with `python env_check.py` plus a quick end-to-end run on a known-good BV号.

## Architecture

```
main.py          CLI orchestrator — argparse, loads .env, calls the 3 stages in order
web_server.py    FastAPI app — serves index.html, one daemon thread per job, SSE progress
download.py      yt-dlp subprocess wrapper → output/audio/*.m4a
transcribe.py    faster-whisper with auto GPU/CPU detection
summarize.py     DeepSeek via OpenAI SDK; presets from summary_presets.toml
env_check.py     dependency/CUDA checker
index.html       single-file SPA served by web_server (no framework)
run.sh / run.bat / run_web.sh launchers — set HF_HOME=.hf_cache and WSL GPU LD_LIBRARY_PATH; ensure_model.py pre-checks model cache; stop_web.sh stops the web server
```

Output layout (created on demand): `output/audio/` (`.m4a`), `output/transcript/` (`.txt` + `_transcript.json` with timed segments), `output/summary/` (`{stem}_summary.md`).

### Data flow & key mechanics

- **`.env` loading is a duplicated ~15-line `_load_env()`** in `main.py`, `web_server.py`, and `env_check.py`, each called at import time. `download.py` / `transcribe.py` / `summarize.py` do NOT load `.env` themselves — running them directly requires env vars pre-set (use `run.sh`) or explicit args.
- **Download dedup**: `download.py` snapshots `output/audio/` before yt-dlp (which runs with `--break-on-existing`) and returns only the NEW `.m4a` files sorted by mtime. Re-running a downloaded video yields no new files and raises.
- **GPU auto-detection**: `transcribe.py` probes `ctranslate2.get_cuda_device_count()`; CUDA uses `compute_type="int8_float16"`, CPU uses `int8`, any exception falls back to CPU. On Windows it pre-adds `nvidia/cublas/bin` and `nvidia/cudnn/bin` from site-packages to the DLL search path.
- **Preset templates**: `summarize.py:build_prompt()` does plain string/regex substitution on `summary_presets.toml` templates — `{{% if has_timestamps %}}` / `{{% else %}}` / `{{% endif %}}` blocks are stripped. Not Jinja2; don't add template features. Quirks: `has_timestamps` is never passed as `True` by the pipeline (the `if` branch is dead), and the `{content}` marker is never substituted — the raw transcript goes in the user message, the template (marker included) goes verbatim to the system prompt.
- **Web job model**: in-memory `_jobs` / `_job_logs` dicts; one daemon thread per job, `job_id` = 12-hex uuid. Progress = transcribe index / total audio count. Results track only the current job's files. State is in memory — restarting uvicorn loses all jobs.
- **Web API routes**: `POST /api/run` (multipart form: url, preset, model, no_summary, start_ep, end_ep, file), `GET /api/progress/{job_id}` (SSE stream), `GET /api/download/{category}/{filename}`, `GET /api/files`. Note the web UI form defaults `preset` to `notes` while the CLI defaults to `structured`.

## Key gotchas

- **Use `run.sh` / `run.bat`, not bare `python main.py`** — they set `HF_HOME=.hf_cache` (local model cache), `LD_LIBRARY_PATH` for WSL GPU, and pre-check the model cache via `ensure_model.py`. Do NOT add `HF_ENDPOINT=hf-mirror.com` / `HF_HUB_DISABLE_XET=1` back: both are incompatible with huggingface_hub ≥1.26 (Xet-storage models fail with `LocalEntryNotFoundError`; mirror absolute redirects aren't followed). If model downloads time out in mainland China, set `HTTP(S)_PROXY` instead.
- **Dual platform**: the `.venv/` at project root is a Linux venv inside shared storage (WSL). Windows ignores it and uses system Python. Don't assume a single interpreter.
- **ffmpeg must be in PATH** for audio extraction. WSL: `sudo apt install ffmpeg`; Windows: `winget install ffmpeg`.
- **Python 3.11+ is required** — `summarize.py` uses `tomllib` (3.11+).
- **WSL GPU**: `env_check.py` can report CUDA available while transcription fails with `RuntimeError: Library libcublas.so.12 is not found` unless `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` was run and `LD_LIBRARY_PATH` is set (run.sh does this). Windows counterpart: `cublas64_12.dll not found`.
- **Whisper model auto-downloads ~3GB** on first transcription (cached under `HF_HOME`).
- **requirements.txt is minimal** (`yt-dlp`, `faster-whisper`, `openai`). Web deps (fastapi, uvicorn, python-multipart) and WSL GPU wheels (nvidia-cublas-cu12, nvidia-cudnn-cu12) are documented in README but not pinned there.

## Adding/editing presets

Edit `summary_presets.toml`. Each preset is a `label` + `prompt_template`. Keep the simple `{{% if has_timestamps %}}` conditional syntax understood by `build_prompt()` — do not introduce real templating. Default preset is `structured` (TOML `default` key); the CLI falls back to a built-in generic prompt when a preset name doesn't resolve.

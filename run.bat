@echo off
set HF_ENDPOINT=https://hf-mirror.com
set HF_HUB_DISABLE_XET=1
set HF_HOME=%~dp0.hf_cache
python main.py %*

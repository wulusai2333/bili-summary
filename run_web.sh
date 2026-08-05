#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export HF_HOME="$DIR/.hf_cache"

NVIDIA_LIB=$(echo "$DIR"/.venv/lib/python*/site-packages/nvidia)
export LD_LIBRARY_PATH="$NVIDIA_LIB/cublas/lib:$NVIDIA_LIB/cudnn/lib:${LD_LIBRARY_PATH}"

# 检测并预下载默认 Whisper 模型（缺失时自动下载，避免任务中途卡住）
python ensure_model.py "${WHISPER_MODEL:-large-v3}"

PORT="${PORT:-8765}"
echo "[Web] 启动 http://localhost:${PORT} (Ctrl+C 退出)"
exec python -m uvicorn web_server:app --host 0.0.0.0 --port "$PORT"

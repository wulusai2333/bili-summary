#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

export HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com}
export HF_HUB_DISABLE_XET=1
export HF_HOME="$DIR/.hf_cache"

NVIDIA_LIB=$(echo "$DIR"/.venv/lib/python*/site-packages/nvidia)
export LD_LIBRARY_PATH="$NVIDIA_LIB/cublas/lib:$NVIDIA_LIB/cudnn/lib:${LD_LIBRARY_PATH}"

exec python main.py "$@"

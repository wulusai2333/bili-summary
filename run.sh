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

# 解析 --model / -m 参数（默认 large-v3），其余参数原样透传给 main.py
MODEL="large-v3"
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--model)
            MODEL="$2"
            ARGS+=("$1" "$2")
            shift 2
            ;;
        --model=*)
            MODEL="${1#*=}"
            ARGS+=("$1")
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done
[ -n "$MODEL" ] || MODEL="large-v3"

# 检测 Whisper 模型缓存，缺失则自动下载（下载配置已去除镜像/禁用Xet等旧变量）
python ensure_model.py "$MODEL"

exec python main.py "${ARGS[@]}"

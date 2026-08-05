#!/usr/bin/env python3
"""启动脚本辅助：检测 Whisper 模型本地缓存，缺失时自动下载。

用法:
    python ensure_model.py            # 默认 large-v3
    python ensure_model.py small      # 指定模型大小
    python ensure_model.py Systran/faster-whisper-small   # 或完整仓库 ID

依赖 HF_HOME 环境变量（run.sh / run.bat 已设置）；未设置时使用
huggingface_hub 默认缓存位置，与 transcribe.py 的加载路径一致。
"""

import sys
from pathlib import Path


def ensure(model_size: str) -> None:
    repo = model_size if "/" in model_size else f"Systran/faster-whisper-{model_size}"

    from huggingface_hub.constants import HF_HUB_CACHE

    model_dir = Path(HF_HUB_CACHE) / f"models--{repo.replace('/', '--')}"
    snapshots = model_dir / "snapshots"
    cached = (
        any((d / "model.bin").is_file() for d in snapshots.iterdir())
        if snapshots.is_dir()
        else False
    )

    if cached:
        print(f"[模型] {model_size} 已缓存，跳过下载")
        return

    print(f"[模型] {model_size} 未缓存，开始下载（约 3GB，仅首次）...")
    from faster_whisper import download_model

    download_model(model_size)
    print(f"[模型] {model_size} 下载完成")


def main() -> int:
    model_size = sys.argv[1] if len(sys.argv) > 1 else "large-v3"
    ensure(model_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())

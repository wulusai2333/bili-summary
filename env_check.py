"""环境依赖检查"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).parent


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
        if key and key not in os.environ:
            os.environ[key] = val


_load_env()


CHECKS = {
    "Python": (">=3.10", lambda: f"{sys.version_info.major}.{sys.version_info.minor}"),
    "ffmpeg": ("必需", lambda: shutil.which("ffmpeg") or "未安装"),
    "yt-dlp": ("必需", lambda: "已安装" if importlib.util.find_spec("yt_dlp") else "未安装"),
    "faster-whisper": ("必需", lambda: "已安装" if importlib.util.find_spec("faster_whisper") else "未安装"),
    "openai": ("必需", lambda: "已安装" if importlib.util.find_spec("openai") else "未安装"),
    "DEEPSEEK_API_KEY": ("必需", lambda: "已设置" if os.getenv("DEEPSEEK_API_KEY") else "未设置"),
    "HF_ENDPOINT": ("推荐", lambda: os.getenv("HF_ENDPOINT", "未设置(将直连HF)")),
    "HF_HUB_DISABLE_XET": ("推荐", lambda: "已设置" if os.getenv("HF_HUB_DISABLE_XET") else "未设置(可能认证失败)"),
}


def check_cuda() -> str:
    try:
        from ctranslate2 import get_cuda_device_count
        n = get_cuda_device_count()
        return f"可用 ({n} 设备)" if n > 0 else "不可用"
    except Exception:
        return "不可用"


def check_cublas_loadable() -> str:
    """检查 libcublas.so 是否可加载（仅 Linux/WSL 需要）。"""
    if sys.platform == "win32":
        return "Windows 无需检查"
    try:
        from ctypes import CDLL
        CDLL("libcublas.so.12")
        return "可加载"
    except OSError:
        pass

    # 检查 .venv 下的 nvidia 库目录
    for lib_dir in (PROJECT_DIR / ".venv" / "lib").glob("python*/site-packages/nvidia/cublas/lib"):
        try:
            from ctypes import CDLL
            CDLL(str(lib_dir / "libcublas.so.12"))
            return f"已就绪({lib_dir.parent.parent.name})"
        except OSError:
            pass

    return "未找到 (pip install nvidia-cublas-cu12)"


def main():
    print("=" * 50)
    print("  bili-summary 环境检查")
    print("=" * 50)
    ok = True

    for name, (required, getter) in CHECKS.items():
        try:
            status = getter()
        except Exception as e:
            status = f"错误: {e}"
        tag = "[OK]" if "未" not in str(status) and "错误" not in str(status) else "[!!]"
        print(f"  {tag:6s} {name:20s} {required:6s} → {status}")
        if tag == "[!!]" and required == "必需":
            ok = False

    print(f"  {'[OK]' if ok else '[!!]':6s} {'CUDA (GPU)':20s} {'可选':6s} → {check_cuda()}")

    cuda_status = check_cuda()
    if "可用" in cuda_status:
        cublas = check_cublas_loadable()
        tag = "[OK]" if "可加载" in cublas or "已就绪" in cublas or "Windows" in cublas else "[!!]"
        print(f"  {tag:6s} {'libcublas.so.12':20s} {'可选':6s} → {cublas}")

    try:
        nvidia_smi = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                                    capture_output=True, text=True, timeout=5)
        gpu = nvidia_smi.stdout.strip() or "未检测到"
        print(f"  [OK]   {'GPU':20s} {'':6s} → {gpu}")
    except Exception:
        pass

    print()
    if not ok:
        print("缺少必需依赖，请安装:")
        print("  pip install yt-dlp faster-whisper openai")
        print("  sudo apt install ffmpeg")
    else:
        print("环境就绪，可以运行: python main.py BV号")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

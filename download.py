"""Bilibili 音频下载"""

import subprocess
import sys
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_TEMPLATE = "%(title)s.%(ext)s"


def download(url: str, output: str | None = None, proxy: str | None = None) -> list[Path]:
    """下载 B 站视频音频，支持合集/分 P。返回下载文件列表。"""
    out_dir = Path(output) if output else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--audio-format", "m4a",
        "--audio-quality", "0",
        "-o", str(out_dir / OUTPUT_TEMPLATE),
        "--no-playlist",  # 默认只下载单个视频；合集用 --playlist
    ]

    if proxy:
        cmd += ["--proxy", proxy]

    cmd.append(url)

    print(f"[下载] {url}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"下载失败:\n{result.stderr}")

    files = sorted(out_dir.glob("*.m4a"), key=lambda f: f.stat().st_mtime, reverse=True)
    return files[:1] if files else []


def download_playlist(
    url: str,
    output: str | None = None,
    start: int = 1,
    end: int | None = None,
    proxy: str | None = None,
) -> list[Path]:
    """下载合集/播放列表，指定分 P 范围。"""
    out_dir = Path(output) if output else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    playlist_items = f"{start}-{end}" if end else str(start)

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-x",
        "--audio-format", "m4a",
        "--audio-quality", "0",
        "-o", str(out_dir / OUTPUT_TEMPLATE),
        "--playlist-items", playlist_items,
    ]

    if proxy:
        cmd += ["--proxy", proxy]

    cmd.append(url)

    print(f"[下载合集] {url} (P{start}-{end or '末'})")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"下载失败:\n{result.stderr}")

    return sorted(out_dir.glob("*.m4a"), key=lambda f: f.stat().st_mtime)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="下载 B 站视频音频")
    parser.add_argument("url", help="视频/合集 URL")
    parser.add_argument("-o", "--output", default=None, help="输出目录")
    parser.add_argument("-p", "--proxy", default=None, help="代理地址")
    parser.add_argument("--playlist", action="store_true", help="下载整个合集")
    parser.add_argument("--start", type=int, default=1, help="起始分 P")
    parser.add_argument("--end", type=int, default=None, help="结束分 P")
    args = parser.parse_args()

    if args.playlist or args.end:
        files = download_playlist(args.url, args.output, args.start, args.end, args.proxy)
    else:
        files = download(args.url, args.output, args.proxy)

    for f in files:
        print(f"  -> {f}")

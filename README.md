# bili-summary

B 站视频一键下载、转文字、AI 总结。全本地化，零云服务依赖（除 DeepSeek API）。

## 功能

```
B站视频 → 下载音频 → 语音转文字 → DeepSeek 总结
  yt-dlp    faster-whisper    DeepSeek API
```

- 🎬 支持单个视频 / 合集 / 指定分 P / 本地音频视频
- 🖥️ Web UI 界面，浏览器一键操作
- 🚀 自动检测 GPU 加速转录（RTX 系列）
- 🏠 本地 Whisper 转录，无需上传云端
- 📝 5 种总结预设（笔记 / 结构化 / 脑图 / 时间线 / 行动指南）
- 📂 输出分类：audio / transcript / summary

## 快速开始

### WSL / Linux

```bash
# 1. 安装系统依赖
sudo apt install ffmpeg

# 2. 创建虚拟环境并安装 Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. (WSL GPU 加速) 安装 CUDA 计算库
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

# 4. 编辑 .env 设置 DeepSeek API Key
# DEEPSEEK_API_KEY=sk-xxx

# 5. 环境检查
.venv/bin/python env_check.py

# 6. 运行（推荐使用启动脚本）
bash run.sh BV号            # 命令行
bash run.sh --preset notes --no-summary

# 或直接启动 Web UI
pip install fastapi uvicorn python-multipart
.venv/bin/python web_server.py
```

### Windows

```powershell
# 1. 安装系统依赖
winget install ffmpeg

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 编辑 .env 设置 DeepSeek API Key

# 4. 环境检查
python env_check.py

# 5. 运行（推荐使用启动脚本）
run.bat BV号
# 或: python main.py BV号
```

首次运行会自动下载 Whisper 模型（约 3GB），后续缓存复用。

## Web UI

浏览器界面，支持 B站链接 / 本地上传 / 已有音频三种输入方式。

### 启动

```bash
python -m uvicorn web_server:app --host 0.0.0.0 --port 8765
```

浏览器打开 `http://localhost:8765`。

> 首次运行需安装额外依赖：`pip install fastapi uvicorn python-multipart`

### 环境要求

- Python 3.10+
- ffmpeg（音频提取必需）
- DeepSeek API Key（[获取地址](https://platform.deepseek.com)）

### ffmpeg 安装

```bash
# Debian/Ubuntu (含 WSL)
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (非 WSL)
winget install ffmpeg
```

## CLI 用法

```bash
# 单个视频
python main.py BV1xxx

# 完整 URL
python main.py https://www.bilibili.com/video/BV1xxx

# 合集第 1-5P
python main.py BV1xxx --playlist --start 1 --end 5

# 只转录，不总结
python main.py BV1xxx --no-summary

# 选择总结预设
python main.py BV1xxx --preset notes    # 学习笔记
python main.py BV1xxx --preset brief    # 简短摘要
python main.py BV1xxx --preset timeline # 时间线梳理
python main.py BV1xxx --preset action   # 行动指南

# 用更快的模型
python main.py BV1xxx --model small
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | BV 号或完整 URL | 必填 |
| `--model`, `-m` | Whisper 模型 | `large-v3` |
| `--llm-model` | DeepSeek 模型 | `deepseek-chat` |
| `--api-key`, `-k` | API Key（优先于环境变量） | `$env:DEEPSEEK_API_KEY` |
| `--prompt` | 自定义总结提示词 | 内置提示词 |
| `--no-summary` | 跳过总结 | — |
| `--no-download` | 跳过下载（转录已有音频） | — |
| `--no-transcribe` | 跳过转录（总结已有文本） | — |
| `--playlist` | 下载整个合集 | — |
| `--start` | 起始分 P | 1 |
| `--end` | 结束分 P | 末 P |
| `--proxy` | 代理地址 | `$env:HTTP_PROXY` |
| `--output`, `-o` | 输出目录 | `./output` |

## Whisper 模型选择

| 模型 | 大小 | 速度 | 中文精度 | 推荐场景 |
|------|------|------|----------|----------|
| `tiny` | ~150MB | 最快 | 一般 | 快速预览 |
| `base` | ~300MB | 快 | 尚可 | 短视频 |
| `small` | ~1GB | 中等 | 好 | 日常使用 |
| `medium` | ~3GB | 慢 | 很好 | 高质量需求 |
| `large-v3` | ~3GB | 最慢 | 最好 | 默认推荐 |

## 输出文件

```
output/
  ├── audio/         # 下载的音频 .m4a
  ├── transcript/    # 转录文本 .txt + .json
  └── summary/       # DeepSeek 总结 .md
```

## 总结预设

预设配置文件 `summary_presets.toml`。

| 预设 | 说明 | 适用场景 |
|------|------|----------|
| `structured` | 结构化总结（默认）| 通用视频 |
| `notes` | 学习笔记 | 教程/课程 |
| `brief` | 简短摘要 | 快速浏览 |
| `timeline` | 时间线梳理 | 讲座/访谈 |
| `action` | 行动指南 | 实操教程 |

## 单独使用各模块

```bash
# 只下载音频
python download.py BV1xxx

# 只转录
python transcribe.py audio.m4a

# 只总结
python summarize.py transcript.txt
```

## 常见问题

### 启动报 `ffprobe and ffmpeg not found`

ffmpeg 未安装或未加入 PATH。

```bash
# WSL / Linux
sudo apt install ffmpeg

# Windows
winget install ffmpeg
```

### 转录时 HuggingFace 模型下载超时

`.env` 中已配置国内镜像，确认包含以下两行：

```
HF_ENDPOINT=https://hf-mirror.com
HF_HUB_DISABLE_XET=1
```

> `HF_HUB_DISABLE_XET=1` 必须设置，否则 HuggingFace 的 XetHub CAS 存储认证会失败。

### 转录时 `LocalEntryNotFoundError: ConnectError`

模型下载失败。两个可能原因：

1. **直连 huggingface.co 被墙** → `.env` 中必须配置 `HF_ENDPOINT=https://hf-mirror.com`
2. **XetHub CAS 认证失败 (401 Unauthorized)** → `.env` 中必须配置 `HF_HUB_DISABLE_XET=1`

使用 `run.sh` / `run.bat` 启动会自动设置这两个环境变量。

### WSL GPU 报错 `libcublas.so.12 is not found`

CUDA GPU 被检测到但计算库缺失。WSL 中需要单独安装：

```bash
# 安装 CUDA 计算库
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

安装后使用 `run.sh` 启动（已配置 `LD_LIBRARY_PATH`），或手动设置：

```bash
export LD_LIBRARY_PATH=.venv/lib/python3.12/site-packages/nvidia/cublas/lib:.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH
```

### WSL GPU 报错 `RuntimeError: Library libcublas.so.12 is not found`

`env_check.py` 显示 CUDA 可用，但转录时报错。原因同上 — pip 装的 `nvidia-cublas-cu12` 库文件不在 `LD_LIBRARY_PATH` 中。使用 `bash run.sh` 启动即可自动处理。

### 用 python 直接运行 vs 启动脚本的区别

| 方式 | `HF_ENDPOINT` | `HF_HUB_DISABLE_XET` | WSL `LD_LIBRARY_PATH` |
|------|:---:|:---:|:---:|
| `run.bat` (Windows) | 自动设置 | 自动设置 | 不需要 |
| `run.sh` (WSL) | 自动设置 | 自动设置 | 自动设置 |
| `python main.py` | 从 `.env` 读取 | 从 `.env` 读取 | 需手动设置 |

## License

MIT

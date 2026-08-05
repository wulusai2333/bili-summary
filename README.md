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

# 6. 运行（推荐使用启动脚本，会自动检测/下载模型）
bash run.sh BV号            # 命令行
bash run.sh --preset notes --no-summary

# 或启动 Web UI（需先安装 Web 依赖，见下方 Web UI 一节）
pip install fastapi uvicorn python-multipart
bash run_web.sh             # 浏览器打开 http://localhost:8765
bash stop_web.sh            # 关闭 Web 服务
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

首次运行会自动下载 Whisper 模型（约 3GB），后续缓存复用。启动脚本
（`run.sh` / `run.bat` / `run_web.sh`）每次启动都会先检测模型缓存，缺失时才下载。

## Web UI

浏览器界面，支持 B站链接 / 本地上传 / 已有音频三种输入方式。

### 启动

WSL / Linux 推荐使用启停脚本（自动检测模型、设置 GPU 库路径）：

```bash
bash run_web.sh       # 启动，浏览器打开 http://localhost:8765
bash stop_web.sh      # 关闭（只结束 8765 端口的服务）
```

或直接运行（Windows 用此方式）：

```bash
python -m uvicorn web_server:app --host 0.0.0.0 --port 8765
```

> 首次运行需安装额外依赖：`pip install fastapi uvicorn python-multipart`
> 端口可用环境变量 `PORT` 覆盖，如 `PORT=9000 bash run_web.sh`

### 环境要求

- Python 3.11+
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

旧版文档建议在 `.env` 中配置镜像：

```
HF_ENDPOINT=https://hf-mirror.com
HF_HUB_DISABLE_XET=1
```

这两个变量与当前 huggingface_hub 版本（1.26+）**不兼容**，会导致下载失败：
Xet 存储的模型必须走 XetHub 通道，`HF_HUB_DISABLE_XET=1` 会强制走已失效的旧下载
路径；hf-mirror.com 的绝对地址重定向也无法被当前版本正确跟随。请**删除这两行**，
脚本已不再设置它们。

国内网络直连超时时，设置代理而不是镜像：

```bash
export HTTP_PROXY=http://127.0.0.1:7890    # 换成你的代理地址
export HTTPS_PROXY=http://127.0.0.1:7890
```

### 转录时 `LocalEntryNotFoundError: ConnectError`

模型下载失败。常见原因：

1. **旧配置残留** → 确认 `.env` 中没有 `HF_ENDPOINT` / `HF_HUB_DISABLE_XET`
   （这两个变量与当前 huggingface_hub 版本不兼容，见上一条）
2. **网络无法直连 huggingface.co** → 设置 `HTTP_PROXY` / `HTTPS_PROXY` 代理
3. **缓存损坏** → 删除 `.hf_cache/hub/models--Systran--faster-whisper-*` 后重试

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

| 方式 | 模型预检 | WSL `LD_LIBRARY_PATH` |
|------|:---:|:---:|
| `run.bat` (Windows) | 自动检测/下载 | 不需要 |
| `run.sh` (WSL) | 自动检测/下载 | 自动设置 |
| `python main.py` | 无（转录时才下载） | 需手动设置 |

## License

MIT

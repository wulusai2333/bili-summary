---
name: bili-summary
description: B站/本地视频一键下载、语音转文字、AI总结。支持单集/合集/分P/本地文件，5种总结预设。当用户提供B站链接、BV号、本地音视频文件，或要求总结视频内容时自动触发。
allowed-tools: Read, Write, Bash, Glob, Grep
---

# Bili Summary Skill

B站视频/本地音视频 → 下载音频 → 语音转文字 → DeepSeek 总结。

## 触发条件

满足任一即触发：
- 用户发送 B站链接 (bilibili.com) 或 BV 号
- 用户发送本地 `.mp4` / `.m4a` / `.mp3` / `.wav` 文件路径
- 用户要求 "总结这个视频"、"提取视频文字"、"视频转笔记"

## 环境检查（首次或报错时执行）

```bash
python {baseDir}/env_check.py
```

如果缺少依赖，按提示安装：
- `pip install yt-dlp faster-whisper openai tomllib`
- `winget install ffmpeg` (Windows) 或 ` brew install ffmpeg` (macOS)

## 工作流

### 步骤 1：确定输入模式

| 用户输入 | 模式 | 参数 |
|----------|------|------|
| BV 号 / bilibili.com 链接 | `bili_single` | `url` |
| 合集链接 + "合集"/"全部"/"第X集到第Y集" | `bili_playlist` | `url --playlist --start X --end Y` |
| BV 号 + "第X集"/"第Xp" | `bili_single_p` | `url --playlist --start X --end X` |
| 本地 .m4a/.mp3/.wav | `local_audio` | `url --no-download` (先跳过下载) |
| 本地 .mp4 | `local_video` | 先 `ffmpeg -i input.mp4 -vn output.m4a` 再处理 |

### 步骤 2：确定输出模式

询问用户（如果没明确说）：
- **完整流程**（默认）：下载 → 转录 → 总结
- **只要转录**：`--no-summary`
- **只要总结**（已有 txt）：`--no-download --no-transcribe`

### 步骤 3：选择总结预设

| 预设 | 命令 | 适用 |
|------|------|------|
| 结构化总结 | `--preset structured` | 通用 |
| 学习笔记 | `--preset notes` | 课程/教程 |
| 简短摘要 | `--preset brief` | 快速浏览 |
| 时间线 | `--preset timeline` | 讲座/访谈 |
| 行动指南 | `--preset action` | 实操教程 |

### 步骤 4：选择模型大小

| 模型 | 速度 | 精度 | 命令 |
|------|------|------|------|
| large-v3 | 慢 | 最高 | `--model large-v3`（默认） |
| medium | 中 | 高 | `--model medium` |
| small | 快 | 中 | `--model small` |

### 步骤 5：执行

```bash
$env:HF_ENDPOINT="https://hf-mirror.com"; $env:HF_HUB_DISABLE_XET="1"
python {baseDir}/main.py "URL" [参数...]
```

### 步骤 6：返回结果

Read 输出的 `_summary.md` 文件，展示总结。

同时告知用户输出目录位置：`{baseDir}/output/`

## 批量处理

如果用户要处理整个合集（如 28 集），建议：

```bash
# 先批量下载所有音频（快速）
python -m yt_dlp -x --audio-format m4a -o "{baseDir}/output/%(title)s.%(ext)s" "URL"

# 然后逐集转录+总结
for f in {baseDir}/output/*.m4a; do
    python {baseDir}/transcribe.py "$f"
    python {baseDir}/summarize.py "${f%.m4a}.txt" --preset notes
done
```

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| `cublas64_12.dll not found` | CUDA 运行时缺失 | 自动回退 CPU；想用 GPU 则 `pip install nvidia-cublas-cu12` |
| `HF ConnectTimeout` | HuggingFace 被墙 | 已自动用 `hf-mirror.com` 镜像 |
| `ffmpeg not found` | 未安装 | `winget install ffmpeg` |
| `DEEPSEEK_API_KEY` 未设置 | 缺少 Key | `.env` 文件已配置 |

## 预设文件

`{baseDir}/summary_presets.toml` 包含所有总结预设，可自行修改提示词。

## 示例

```
用户: https://www.bilibili.com/video/BV1xxx/
→ 完整流程，structured 预设

用户: 帮我总结这个视频，只要文字不要总结
→ bili_single → --no-summary

用户: 把 D:\videos\lecture.mp4 转成学习笔记
→ local_video → 先提取音频 → --preset notes

用户: 这个合集全部 28 集总结一下
→ 批量下载 → 逐集转录+总结
```

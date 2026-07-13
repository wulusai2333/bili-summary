# bili-summary

B 站视频一键下载、转文字、AI 总结。全本地化，零云服务依赖（除 DeepSeek API）。

## 功能

```
B站视频 → 下载音频 → 语音转文字 → DeepSeek 总结
  yt-dlp    faster-whisper    DeepSeek API
```

- 支持单个视频 / 合集 / 指定分 P
- 本地 Whisper 转录，无需上传云端
- DeepSeek API 总结，国内直连

## 快速开始

```powershell
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置 DeepSeek API Key
set DEEPSEEK_API_KEY=sk-你的key

# 3. 运行
python main.py BV1xxx
```

首次运行会自动下载 Whisper 模型（约 3GB），后续缓存复用。

## 用法

```powershell
# 单个视频
python main.py BV1xxx

# 完整 URL
python main.py https://www.bilibili.com/video/BV1xxx

# 合集第 1-5P
python main.py BV1xxx --playlist --start 1 --end 5

# 只转录，不总结
python main.py BV1xxx --no-summary

# 跳过下载（转录已有 m4a 文件）
python main.py BV1xxx --no-download

# 用更快的模型
python main.py BV1xxx --model tiny

# 自定义总结提示词
python main.py BV1xxx --prompt "用英文总结并提取关键时间戳"

# 选择总结预设
python main.py BV1xxx --preset notes    # 学习笔记
python main.py BV1xxx --preset brief    # 简短摘要
python main.py BV1xxx --preset timeline # 时间线梳理
python main.py BV1xxx --preset action   # 行动指南
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

## 环境要求

- Python 3.10+
- Windows / macOS / Linux
- DeepSeek API Key（[获取地址](https://platform.deepseek.com)）

## 单独使用各模块

```powershell
# 只下载音频
python download.py BV1xxx

# 只转录
python transcribe.py audio.m4a

# 只总结
python summarize.py transcript.txt
```

## License

MIT

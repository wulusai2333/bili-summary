"""DeepSeek 总结"""

import os
import tomllib
from pathlib import Path

from openai import OpenAI


DEFAULT_MODEL = "deepseek-chat"
OUTPUT_DIR = Path(__file__).parent / "output"
SUMMARY_DIR = OUTPUT_DIR / "summary"
PRESETS_FILE = Path(__file__).parent / "summary_presets.toml"
DEFAULT_PRESET = "structured"


def load_presets(path: Path | None = None) -> dict:
    """加载总结预设。"""
    p = path or PRESETS_FILE
    if not p.exists():
        return {}
    data = tomllib.loads(p.read_text(encoding="utf-8"))
    return data.get("presets", {})


def build_prompt(preset: str | None = None, custom: str | None = None, has_timestamps: bool = False) -> str | None:
    """构建总结提示词。优先自定义 > 预设 > 默认。"""
    if custom:
        return custom

    if preset:
        presets = load_presets()
        entry = presets.get(preset)
        if entry:
            template = entry.get("prompt_template", "")
            if has_timestamps:
                template = template.replace("{{% if has_timestamps %}}", "").replace("{{% else %}}", "").replace("{{% endif %}}", "")
            else:
                import re
                template = re.sub(r"{{% if has_timestamps %}}.*?{{% else %}}", "", template, flags=re.DOTALL)
                template = template.replace("{{% endif %}}", "")
            return template
        print(f"[警告] 预设 '{preset}' 不存在，使用默认提示词")

    return None


def summarize(
    text: str,
    api_key: str | None = None,
    base_url: str = "https://api.deepseek.com",
    model: str = DEFAULT_MODEL,
    prompt: str | None = None,
    preset: str | None = None,
) -> str:
    """调用 DeepSeek API 总结文本。"""
    key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("未设置 DEEPSEEK_API_KEY（环境变量或传参）")

    client = OpenAI(api_key=key, base_url=base_url)

    system_prompt = build_prompt(preset=preset, custom=prompt) or (
        "你是一个专业的文本总结助手。请用中文对以下内容进行结构化总结，"
        "包括：1) 核心主题 2) 关键要点（以列表呈现）3) 总结概述。"
        "语言简洁清晰，不要遗漏重要信息。"
    )

    label = preset or "默认"
    print(f"[总结] {len(text)} 字 | 预设: {label} | 模型: {model}")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content or ""


def summarize_file(
    file_path: str | Path,
    api_key: str | None = None,
    base_url: str = "https://api.deepseek.com",
    model: str = DEFAULT_MODEL,
    prompt: str | None = None,
    preset: str | None = None,
    output_dir: str | Path | None = None,
) -> str:
    """从文件读取转录文本并总结，结果保存为 Markdown。"""
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")

    summary = summarize(text, api_key, base_url, model, prompt, preset)

    out_dir = Path(output_dir) if output_dir else SUMMARY_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"{path.stem}_summary.md"
    md_path.write_text(summary, encoding="utf-8")

    print(f"  -> {md_path}")
    return summary


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DeepSeek 总结")
    parser.add_argument("file", help="转录文本文件")
    parser.add_argument("-k", "--api-key", default=None, help="DeepSeek API Key")
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt", default=None, help="自定义提示词")
    parser.add_argument("-p", "--preset", default=DEFAULT_PRESET, help="总结预设 (structured/notes/brief/timeline/action)")
    parser.add_argument("-o", "--output", default=None, help="输出目录")
    parser.add_argument("--list-presets", action="store_true", help="列出所有预设")
    args = parser.parse_args()

    if args.list_presets:
        presets = load_presets()
        for name, entry in presets.items():
            print(f"  {name:16s} {entry.get('label', '')}")
    else:
        result = summarize_file(args.file, args.api_key, args.base_url, args.model, args.prompt, args.preset, args.output)
        print(f"\n{result}")

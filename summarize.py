"""DeepSeek 总结"""

import os
from pathlib import Path

from openai import OpenAI


DEFAULT_MODEL = "deepseek-chat"
OUTPUT_DIR = Path(__file__).parent / "output"


def summarize(
    text: str,
    api_key: str | None = None,
    base_url: str = "https://api.deepseek.com",
    model: str = DEFAULT_MODEL,
    prompt: str | None = None,
) -> str:
    """调用 DeepSeek API 总结文本。"""
    key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise ValueError("未设置 DEEPSEEK_API_KEY（环境变量或传参）")

    client = OpenAI(api_key=key, base_url=base_url)

    system_prompt = prompt or (
        "你是一个专业的文本总结助手。请用中文对以下内容进行结构化总结，"
        "包括：1) 核心主题 2) 关键要点（以列表呈现）3) 总结概述。"
        "语言简洁清晰，不要遗漏重要信息。"
    )

    print(f"[总结] 文本长度 {len(text)} 字，模型: {model}")
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
    output_dir: str | Path | None = None,
) -> str:
    """从文件读取转录文本并总结，结果保存为 Markdown。"""
    path = Path(file_path)
    text = path.read_text(encoding="utf-8")

    summary = summarize(text, api_key, base_url, model, prompt)

    out_dir = Path(output_dir) if output_dir else path.parent
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
    parser.add_argument("-o", "--output", default=None, help="输出目录")
    args = parser.parse_args()

    result = summarize_file(args.file, args.api_key, args.base_url, args.model, args.prompt, args.output)
    print(f"\n{result}")

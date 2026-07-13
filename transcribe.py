"""语音转文字（faster-whisper）"""

import json
from pathlib import Path

from faster_whisper import WhisperModel


MODEL_SIZE = "large-v3"
OUTPUT_DIR = Path(__file__).parent / "output"


def transcribe(
    audio_path: str | Path,
    model_size: str = MODEL_SIZE,
    language: str = "zh",
    device: str = "auto",
    output_dir: str | Path | None = None,
) -> dict:
    """转录音频文件，返回 {text, segments, output_path}。"""
    model = WhisperModel(model_size, device=device, compute_type="int8")
    audio = str(audio_path)

    print(f"[转录] {Path(audio_path).name} (模型: {model_size})")
    segments, info = model.transcribe(audio, language=language, beam_size=5)

    text_parts = []
    seg_list = []
    for seg in segments:
        text_parts.append(seg.text.strip())
        seg_list.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })

    text = " ".join(text_parts)

    out_dir = Path(output_dir) if output_dir else Path(audio_path).parent
    stem = Path(audio_path).stem

    txt_path = out_dir / f"{stem}.txt"
    txt_path.write_text(text, encoding="utf-8")

    json_path = out_dir / f"{stem}_transcript.json"
    json_path.write_text(json.dumps({
        "language": info.language,
        "duration": info.duration,
        "segments": seg_list,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  -> {txt_path}")

    return {
        "text": text,
        "segments": seg_list,
        "duration": info.duration,
        "language": info.language,
        "output_path": str(txt_path),
        "json_path": str(json_path),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="语音转文字")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("-m", "--model", default=MODEL_SIZE, help="模型大小")
    parser.add_argument("-l", "--language", default="zh", help="语言代码")
    parser.add_argument("-d", "--device", default="auto", help="设备 (auto/cpu/cuda)")
    parser.add_argument("-o", "--output", default=None, help="输出目录")
    args = parser.parse_args()

    result = transcribe(args.audio, args.model, args.language, args.device, args.output)
    print(f"\n时长: {result['duration']:.0f}秒 | 语言: {result['language']}")
    print(f"前200字: {result['text'][:200]}...")

# transcribe.py
# Author: Matteo Mastore
# Description:
#   Transcribe audio/video files (mp3, wav, mp4, mov, mkv, etc.) using OpenAI Whisper.
#   Outputs: .txt (full text), .srt (subtitles), .vtt (webvtt).
#
# Usage examples:
#   python transcribe.py "C:\path\file.mp4" --model small --language it
#   python transcribe.py "C:\file1.mp3" "D:\file2.mp4" --timestamps srt,vtt --model medium --language it

import argparse
import sys
from pathlib import Path
from datetime import timedelta

import torch
import whisper

def format_timestamp(seconds: float, srt: bool = True) -> str:
    td = timedelta(seconds=max(0, seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int((td.total_seconds() - total_seconds) * 1000)
    if srt:
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    else:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def write_txt(out_path: Path, text: str):
    out_path.write_text(text.strip() + "\n", encoding="utf-8")

def write_srt(out_path: Path, segments):
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = format_timestamp(seg["start"], srt=True)
        end = format_timestamp(seg["end"], srt=True)
        text = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

def write_vtt(out_path: Path, segments):
    lines = ["WEBVTT\n"]
    for seg in segments:
        start = format_timestamp(seg["start"], srt=False)
        end = format_timestamp(seg["end"], srt=False)
        text = seg["text"].strip()
        lines.append(f"{start} --> {end}\n{text}\n")
    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Transcribe audio/video to text/subtitles using OpenAI Whisper.")
    parser.add_argument("inputs", nargs="+", help="Audio/Video file paths.")
    parser.add_argument("--model", default="small",
                        choices=["tiny", "base", "small", "medium", "large-v3"],
                        help="Whisper model size (default: small).")
    parser.add_argument("--language", default="it", help="Language code (default: it).")
    parser.add_argument("--timestamps", default="txt,srt,vtt",
                        help="Comma-separated outputs: txt,srt,vtt (default: all).")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device}")
    model = whisper.load_model(args.model, device=device)

    requested = {t.strip().lower() for t in args.timestamps.split(",")}
    valid = {"txt", "srt", "vtt"}
    targets = list(requested & valid)

    for inp in args.inputs:
        in_path = Path(inp)
        if not in_path.exists():
            print(f"[ERROR] File not found: {in_path}")
            continue

        print(f"[INFO] Transcribing: {in_path}")
        result = model.transcribe(str(in_path), language=args.language, task="transcribe", verbose=False)

        full_text = result.get("text", "").strip()
        segments = result.get("segments", [])

        if "txt" in targets:
            write_txt(in_path.with_suffix(".txt"), full_text)
            print(f"[OK] Wrote TXT: {in_path.with_suffix('.txt')}")

        if "srt" in targets:
            write_srt(in_path.with_suffix(".srt"), segments)
            print(f"[OK] Wrote SRT: {in_path.with_suffix('.srt')}")

        if "vtt" in targets:
            write_vtt(in_path.with_suffix(".vtt"), segments)
            print(f"[OK] Wrote VTT: {in_path.with_suffix('.vtt')}")

    print("[DONE] All files processed.")

if __name__ == "__main__":
    main()

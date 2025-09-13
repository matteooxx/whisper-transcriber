# transcribe.py
# Windows-friendly Whisper runner with optional AI post-translation.
#
# Features:
# - Prompts once for an OpenAI API key and stores it in "openai_api_key.txt" (gitignored) next to this file.
# - User selects model, outputs (txt/srt/vtt), input language, output language via the .bat wrapper.
# - Behavior by language:
#     * out-lang == in-lang  -> Whisper TRANSCRIBE in input language (no translation)
#     * out-lang == en       -> Whisper TRANSLATE to English; writes [eng].*
#     * out-lang != en and out-lang != in-lang ->
#           1) Whisper TRANSLATE -> English; writes [eng].*
#           2) AI translation (OpenAI) English -> target; writes [<lang>].txt
# - Per input file, creates "<project>/<name>/" and writes results inside as "<name> [xxx].ext".
# - SRT/VTT reflect the first-step language (English if you requested a non-English target).
#
# NOTE:
#   Do NOT commit your API key. It is stored locally in openai_api_key.txt, which should be in .gitignore.

import argparse
import os
import re
from pathlib import Path
from datetime import timedelta
from typing import List

import torch
import whisper

SUPPORTED_LANGS = {"en", "zh", "hi", "es", "ar", "it"}
KEY_FILENAME = "openai_api_key.txt"  # stored in the project root (same dir as this script)

def sanitize_folder_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name.strip()) or "output"

def ts_srt(seconds: float) -> str:
    td = timedelta(seconds=max(0, seconds))
    total = int(td.total_seconds())
    h, m, s = total // 3600, (total % 3600) // 60, total % 60
    ms = int((td.total_seconds() - total) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def ts_vtt(seconds: float) -> str:
    td = timedelta(seconds=max(0, seconds))
    total = int(td.total_seconds())
    h, m, s = total // 3600, (total % 3600) // 60, total % 60
    ms = int((td.total_seconds() - total) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def write_txt(path: Path, text: str):
    path.write_text((text or "").strip() + "\n", encoding="utf-8")

def write_srt(path: Path, segments):
    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(f"{i}\n{ts_srt(seg['start'])} --> {ts_srt(seg['end'])}\n{seg['text'].strip()}\n")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

def write_vtt(path: Path, segments):
    lines = ["WEBVTT\n"]
    for seg in segments:
        lines.append(f"{ts_vtt(seg['start'])} --> {ts_vtt(seg['end'])}\n{seg['text'].strip()}\n")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

def chunk_text(text: str, max_chars: int = 8000) -> List[str]:
    """Split long texts into API-friendly chunks."""
    text = text.replace("\r\n", "\n")
    chunks, current, count = [], [], 0
    for line in text.split("\n"):
        if count + len(line) + 1 > max_chars and current:
            chunks.append("\n".join(current))
            current = [line]
            count = len(line) + 1
        else:
            current.append(line)
            count += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks

def ensure_openai_api_key(project_dir: Path) -> str:
    """Ensure an OpenAI API key exists in openai_api_key.txt; if missing/invalid, prompt, save, return."""
    key_path = project_dir / KEY_FILENAME
    key = ""
    if key_path.exists():
        key = key_path.read_text(encoding="utf-8").strip()

    def looks_valid(k: str) -> bool:
        return bool(k) and k.startswith("sk-")

    if not looks_valid(key):
        print("[SETUP] No valid API key found.")
        while True:
            entered = input("Enter your OpenAI API key (starts with 'sk-'): ").strip()
            if looks_valid(entered):
                key = entered
                key_path.write_text(key, encoding="utf-8")
                print(f"[SETUP] Key saved to: {key_path}  (remember: it's in .gitignore)")
                break
            else:
                print("[WARN] Invalid key. Try again (must start with 'sk-').")
    return key

def ai_translate_english_to_target(english_text: str, target_lang_code: str, api_key: str) -> str:
    """AI translation from English to the target language using OpenAI."""
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not available. Ensure 'openai' is in requirements.txt.") from e

    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are a professional translator. Translate the following English text into the target language "
        "while preserving meaning, tone, names, numbers, and formatting. Use natural, fluent prose."
    )

    chunks = chunk_text(english_text, max_chars=8000)
    outputs = []

    for ch in chunks:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Target language code: {target_lang_code}\n\nText:\n{ch}"}
            ],
        )
        outputs.append(resp.choices[0].message.content.strip())

    return "\n".join(outputs).strip()

def main():
    ap = argparse.ArgumentParser(description="Transcribe/translate audio/video using Whisper + AI post-translation.")
    ap.add_argument("inputs", nargs="+", help="Audio/Video file paths.")
    ap.add_argument("--model", default="small",
                    choices=["tiny", "base", "small", "medium", "large-v3"],
                    help="Whisper model size (default: small).")
    ap.add_argument("--outputs", default="txt",
                    help="Comma-separated outputs for step 1: txt,srt,vtt (default: txt).")
    ap.add_argument("--in-lang", default="it",
                    help="Input language code (en, zh, hi, es, ar, it).")
    ap.add_argument("--out-lang", default="it",
                    help="Output language code (en, zh, hi, es, ar, it).")
    args = ap.parse_args()

    project_dir = Path(__file__).resolve().parent

    # Ensure API key file exists (even if this run may not need it)
    api_key = ensure_openai_api_key(project_dir)

    in_lang = args.in_lang if args.in_lang in SUPPORTED_LANGS else "it"
    out_lang = args.out_lang if args.out_lang in SUPPORTED_LANGS else in_lang

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[INFO] Using device: {device}")
    print(f"[INFO] Loading model: {args.model}")
    model = whisper.load_model(args.model, device=device)

    requested = {t.strip().lower() for t in args.outputs.split(",") if t.strip()}
    valid = {"txt", "srt", "vtt"}
    targets = list(requested & valid) or ["txt"]

    for inp in args.inputs:
        in_path = Path(inp).resolve()
        if not in_path.exists() or not in_path.is_file():
            print(f"[ERROR] File not found: {in_path}")
            continue

        name = sanitize_folder_name(in_path.stem)
        out_dir = project_dir / name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: decide mode
        if out_lang == in_lang:
            mode = "transcribe"
            print(f"[INFO] Mode: TRANSCRIBE in '{in_lang}'")
        elif out_lang == "en":
            mode = "translate"  # to English
            print("[INFO] Mode: TRANSLATE Whisper -> English (step 1)")
        else:
            mode = "translate"  # then AI EN -> target
            print("[INFO] Mode: TRANSLATE Whisper -> English (step 1), then AI EN -> target (step 2)")

        print(f"[INFO] Processing: {in_path}")
        tr_kwargs = dict(task=mode, verbose=False, language=in_lang)
        result = model.transcribe(str(in_path), **tr_kwargs)

        text = (result.get("text") or "").strip()
        segments = result.get("segments", [])

        # Step 1 outputs
        if mode == "transcribe":
            if "txt" in targets:
                write_txt(out_dir / f"{name} [{in_lang}].txt", text)
                print(f"[OK] Wrote TXT: {out_dir / f'{name} [{in_lang}].txt'}")
            if "srt" in targets:
                write_srt(out_dir / f"{name}.srt", segments)
                print(f"[OK] Wrote SRT: {out_dir / f'{name}.srt'}")
            if "vtt" in targets:
                write_vtt(out_dir / f"{name}.vtt", segments)
                print(f"[OK] Wrote VTT: {out_dir / f'{name}.vtt'}")

        else:
            if "txt" in targets:
                write_txt(out_dir / f"{name} [eng].txt", text)
                print(f"[OK] Wrote TXT (EN): {out_dir / f'{name} [eng].txt'}")
            if "srt" in targets:
                write_srt(out_dir / f"{name} [eng].srt", segments)
                print(f"[OK] Wrote SRT (EN): {out_dir / f'{name} [eng].srt'}")
            if "vtt" in targets:
                write_vtt(out_dir / f"{name} [eng].vtt", segments)
                print(f"[OK] Wrote VTT (EN): {out_dir / f'{name} [eng].vtt'}")

            # Step 2: AI EN -> target (only if target != en and != input)
            if out_lang != "en" and out_lang != in_lang:
                try:
                    print(f"[INFO] AI translating English -> '{out_lang}' (step 2)")
                    translated = ai_translate_english_to_target(text, out_lang, api_key)
                    write_txt(out_dir / f"{name} [{out_lang}].txt", translated)
                    print(f"[OK] Wrote TXT ({out_lang}): {out_dir / f'{name} [{out_lang}].txt'}")
                    print("[INFO] Note: SRT/VTT remain in English from step 1. "
                          "Ask if you want target-language SRT/VTT with per-segment alignment.")
                except Exception as e:
                    print(f"[ERROR] AI translation failed: {e}")

    print("[DONE] All files processed.")

if __name__ == "__main__":
    main()

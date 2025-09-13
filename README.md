# Whisper Transcriber (Windows-friendly)

Transcribe or translate **audio/video** files (MP3, WAV, MP4, MOV, MKV, etc.) using **OpenAI Whisper**.
- Choose **accuracy** (model size).
- Choose one or more **outputs**: TXT / SRT / VTT.
- Pick **input language** (spoken in the media) and **output language** (final text language).
- If output language = English → Whisper **translate** to English.
- If output language = same as input → Whisper **transcribe** (no translation).
- If output language ≠ English and ≠ input → 2-step pipeline:
  1) Whisper **translate** to English → saves `[eng].*`
  2) **AI translation** (OpenAI) from English TXT → target language → saves `[<lang>].txt`

> Subtitles (SRT/VTT) are generated from **step 1** and will be **English** if you chose a non-English target.  
> Ask if you want target-language SRT/VTT with per-segment alignment.

## Requirements (Windows)

1. **Python 3.10+** – https://www.python.org/downloads/  
   Make sure to check **“Add Python to PATH”** during install.

2. **FFmpeg**  
   Easiest with Chocolatey:  
   ```powershell
   choco install ffmpeg -y
   ```
   (Or download a prebuilt FFmpeg and add `...\ffmpeg\bin` to PATH.)

3. (Optional) **NVIDIA GPU**  
   If you want GPU acceleration:
   ```powershell
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```
   Otherwise CPU is fine:
   ```powershell
   pip install torch
   ```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## How to get your OpenAI API key

1. Go to https://platform.openai.com/ and log in.  
2. Open **View API keys** (or go to https://platform.openai.com/account/api-keys).  
3. Click **Create new secret key** and copy it (starts with `sk-...`).

> **Never commit your API key.** This project stores it locally in `openai_api_key.txt` (gitignored).

## Usage

- Drag & drop one or more media files onto `transcribe.bat`.
- Pick:
  - **Accuracy (model)**: tiny / base / small / medium / large-v3
  - **Outputs**: TXT / SRT / VTT (multi-select)
  - **Input language**: en / zh / hi / es / ar / it
  - **Output language**: en / zh / hi / es / ar / it
- The first time, you’ll be prompted to paste your **OpenAI API key**.  
  It will be saved to `openai_api_key.txt` next to `transcribe.py`.

Outputs are saved under:
```
<project>\<input_name>\ 
  - <input_name> [eng].txt / .srt / .vtt     (if step 1 was English)
  - <input_name> [<lang>].txt                (final AI translation if requested)
  - <input_name> [it].txt                    (if you transcribed in Italian)
```

## Examples (command line)

```powershell
# Run via .bat with prompts (recommended)
.\transcribe.bat "C:\media\lecture.mp4"

# Or directly with Python (no prompts):
python transcribe.py --model small --outputs txt,srt --in-lang it --out-lang en "C:\media\interview.mp3"
```

## Troubleshooting

- **ffmpeg not found** → ensure FFmpeg is installed and in PATH.
- **Slow on CPU** → choose a smaller model (tiny/base/small).
- **GPU not used** → install Torch with CUDA and up-to-date NVIDIA drivers.
- **Key issues** → delete `openai_api_key.txt` to re-enter a fresh key.

## Security

- `openai_api_key.txt` is in `.gitignore`.  
- Do **not** share or commit your API key.

#!/usr/bin/env bash
# doctor.sh - check (and where free + safe, fix) everything cinematic-edit needs. No sudo, no accounts.
#   bash <skill>/scripts/doctor.sh          prints "All set" when ready
SK="$(cd "$(dirname "$0")/.." && pwd)"; source "$SK/scripts/env.sh"
BAD=0; OS="$(uname -s)"
ok(){ printf '  ok      %-10s %s\n' "$1" "$2"; }; no(){ printf '  MISSING %-10s %s\n' "$1" "$2"; BAD=1; }
echo "cinematic-edit doctor ($OS $(uname -m))"
if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then ok ffmpeg "$(ffmpeg -version | head -1 | awk '{print $3}')"
  ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libx264 && ok x264 present || no x264 "ffmpeg lacks libx264 (brew install ffmpeg / apt install ffmpeg)"
else case "$OS" in Darwin) no ffmpeg "brew install ffmpeg";; *) no ffmpeg "sudo apt install ffmpeg";; esac; fi
if command -v python3 >/dev/null && python3 -c 'import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)'; then
  ok python "$(python3 -V | awk '{print $2}')"
  if ! "$CE_PY" -c 'import numpy,cv2,PIL' 2>/dev/null; then
    echo "  ..      venv       creating $CE_HOME/venv and installing numpy, opencv, pillow"
    mkdir -p "$CE_HOME" && python3 -m venv "$CE_HOME/venv" >/dev/null 2>&1 \
      && "$CE_HOME/venv/bin/pip" install -q numpy opencv-python-headless pillow >/dev/null 2>&1
    [ -x "$CE_HOME/venv/bin/python" ] && CE_PY="$CE_HOME/venv/bin/python"
  fi
  "$CE_PY" -c 'import numpy,cv2,PIL' 2>/dev/null && ok packages "numpy opencv pillow ($CE_PY)" || no packages "pip install failed: check connection"
else no python "need Python 3.9+ (python.org or brew install python)"; fi
# optional extras ----------------------------------------------------------------
MATTE=0; for a in "$@"; do [ "$a" = "--install-matte" ] && MATTE=1; [ "$a" = "--install-whisper" ] && WHISPER=1; done
if [ "$MATTE" = 1 ] && ! "$CE_PY" -c 'import torch,torchvision' 2>/dev/null; then
  echo "  ..      torch      installing PyTorch for the cutout (about 1 GB, one time)"; "$CE_PY" -m pip install -q torch torchvision >/dev/null 2>&1; fi
if [ "${WHISPER:-0}" = 1 ] && ! "$CE_PY" -c 'import faster_whisper' 2>/dev/null; then
  echo "  ..      whisper    installing faster-whisper (model downloads on first use)"; "$CE_PY" -m pip install -q faster-whisper >/dev/null 2>&1; fi
"$CE_PY" -c 'import torch' 2>/dev/null && echo "  ok      cutout     PyTorch present (matte.py usable)" || echo "  note    cutout     optional: doctor.sh --install-matte"
if "$CE_PY" -c 'import faster_whisper' 2>/dev/null; then echo "  ok      speech     faster-whisper"
elif command -v npx >/dev/null; then echo "  ok      speech     npx hyperframes transcribe (fallback)"
else echo "  note    speech     optional, for captions: doctor.sh --install-whisper (or install Node 22+)"; fi
command -v node >/dev/null && echo "  ok      capture    node $(node -v) (sourcing/capture.mjs for web pages; needs Chrome)" || echo "  note    capture    optional: Node 22+ for page captures"
command -v yt-dlp >/dev/null && echo "  ok      yt-dlp     present" || echo "  note    yt-dlp     optional, for YouTube clips"
AFJ="$("$CE_PY" "$SK/scripts/audioforge.py" detect 2>/dev/null)"; case "$AFJ" in *'"ready": true'*) echo "  ok      audio      audio-forge ready (music, voice, effects: ask the person before using)";; *'"found": true'*) echo "  note    audio      audio-forge installed but not ready: run its doctor";; *) echo "  note    audio      optional: install audio-forge for generated music/voice/effects";; esac
echo; [ $BAD -eq 0 ] && { echo "All set"; exit 0; }; echo "Not ready: fix the MISSING items and re-run."; exit 1

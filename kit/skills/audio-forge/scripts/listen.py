#!/usr/bin/env python3
"""listen.py -- speech to text: make subtitles (.srt) and word timings from any audio/video (OPTIONAL, faster-whisper).

  python3 listen.py talk.mp4 --srt talk.srt [--words words.json] [--model small] [--language en]

--words writes editor-v1's work/tx/words.json format: [{"w": "Right", "s": 0.0, "e": 0.24}, ...]
Install: bash doctor.sh --install transcribe   (about 500 MB: ctranslate2 + the 'small' model; asked first)
Models: tiny (75 MB) base (140 MB) small (480 MB) medium (1.5 GB). Use tiny/base for a quick draft.
"""
import argparse, json, sys

ap = argparse.ArgumentParser()
ap.add_argument("media"); ap.add_argument("--srt"); ap.add_argument("--words"); ap.add_argument("--model", default="small")
ap.add_argument("--language"); a = ap.parse_args()
try:
    from faster_whisper import WhisperModel
except Exception:
    sys.exit("faster-whisper is not installed (optional, ~500 MB). Run: bash doctor.sh --install transcribe")
m = WhisperModel(a.model, device="cpu", compute_type="int8")
segs, info = m.transcribe(a.media, language=a.language, word_timestamps=True, vad_filter=True)
def ts(t):
    h, r = divmod(t, 3600); mi, s = divmod(r, 60)
    return f"{int(h):02d}:{int(mi):02d}:{s:06.3f}".replace(".", ",")
srt, words = [], []
for i, s in enumerate(segs, 1):
    srt.append(f"{i}\n{ts(s.start)} --> {ts(s.end)}\n{s.text.strip()}\n")
    for w in (s.words or []):
        words.append({"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)})
if a.srt:
    open(a.srt, "w", encoding="utf-8").write("\n".join(srt))
if a.words:
    json.dump(words, open(a.words, "w"))
print(json.dumps(dict(language=info.language, segments=len(srt), words=len(words), srt=a.srt, words_json=a.words)))

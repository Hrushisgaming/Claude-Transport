#!/usr/bin/env python3
"""subs2speech.py -- speak a subtitle file (.srt .vtt .ass) as a timed voice track.

!! The agent must confirm intent with the user BEFORE running this (see SKILL.md): replace the original speech (dub),
!! add a voice-over under the original audio, or just produce a voice track? which voice/language?

  python3 subs2speech.py subs.srt --out voice.wav [--duration 94.2]
  python3 subs2speech.py subs.srt --engine kokoro --voice af_heart --max-tempo 1.3 --out voice.wav
  python3 subs2speech.py subs.srt --video in.mp4 --mode replace --out dubbed.mp4      # dub
  python3 subs2speech.py subs.srt --video in.mp4 --mode mix --orig-db -16 --out vo.mp4   # voice-over, original kept under it
  python3 subs2speech.py subs.srt --voice-map '{"ALICE":"af_heart","BOB":"am_adam"}'    # "ALICE: text" lines pick a voice

Each cue is synthesised, then sped up (never slowed) with a pitch-preserving time stretch if it is longer than its slot;
cues that still do not fit are listed in <out>.fit.json so the text can be shortened. Cues are placed at their start times.
"""
import argparse, json, os, re, subprocess, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tts
from forge.song import write_wav, read_wav
from forge import dsp
import audio_edit

SR = tts.OUT_SR


def ts(s):
    s = s.strip().replace(",", ".")
    p = s.split(":")
    p = [float(x) for x in p]
    while len(p) < 3:
        p.insert(0, 0.0)
    return p[0] * 3600 + p[1] * 60 + p[2]


def clean(t):
    t = re.sub(r"\{[^}]*\}", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\\N", " ").replace("\\n", " ").replace("♪", "")
    return " ".join(t.split())


def parse(path):
    raw = open(path, encoding="utf-8-sig", errors="replace").read().replace("\r", "")
    cues = []
    if path.lower().endswith(".ass") or path.lower().endswith(".ssa"):
        for ln in raw.split("\n"):
            if ln.startswith("Dialogue:"):
                f = ln.split(",", 9)
                cues.append((ts(f[1]), ts(f[2]), clean(f[9])))
    else:
        for blk in re.split(r"\n\s*\n", raw):
            lines = [l for l in blk.split("\n") if l.strip()]
            for i, l in enumerate(lines):
                if "-->" in l:
                    a, b = l.split("-->")[:2]
                    cues.append((ts(a.split()[0]), ts(b.strip().split()[0]), clean(" ".join(lines[i + 1:]))))
                    break
    return [c for c in cues if c[2]]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("subs")
    ap.add_argument("--out", default="voice.wav"); ap.add_argument("--duration", type=float)
    ap.add_argument("--engine", default="auto"); ap.add_argument("--voice"); ap.add_argument("--lang"); ap.add_argument("--voice-fx")
    ap.add_argument("--speed", type=float, default=1.0); ap.add_argument("--max-tempo", type=float, default=1.35)
    ap.add_argument("--borrow-gap", action="store_true", help="a cue may run into the silence before the next cue")
    ap.add_argument("--align", default="start", choices=["start", "center"])
    ap.add_argument("--keep-sfx", action="store_true", help="also speak [bracketed] sound descriptions")
    ap.add_argument("--voice-map", help='JSON {"SPEAKER":"voice"} for "SPEAKER: text" lines')
    ap.add_argument("--video"); ap.add_argument("--mode", default="replace", choices=["replace", "mix"]); ap.add_argument("--orig-db", type=float, default=-16)
    a = ap.parse_args()

    cues = parse(a.subs)
    if not a.keep_sfx:
        cues = [c for c in cues if not re.fullmatch(r"[\[\(].*[\]\)]", c[2])]
    vmap = json.loads(a.voice_map) if a.voice_map else {}
    total = a.duration or (max(c[1] for c in cues) + 1.0)
    buf = np.zeros(int(total * SR) + SR * 5)
    report = []
    for i, (s, e, text) in enumerate(cues):
        voice = a.voice
        m = re.match(r"^([A-Za-z0-9 _.-]{1,24}):\s+(.*)$", text)
        if m and (m.group(1) in vmap or m.group(1).upper() in vmap):
            voice = vmap.get(m.group(1), vmap.get(m.group(1).upper()))
            text = m.group(2)
        x, eng = tts.synth(text, a.engine, voice, a.speed, a.lang, a.voice_fx)
        nat = len(x) / SR
        slot = e - s
        if a.borrow_gap and i + 1 < len(cues):
            slot = max(slot, cues[i + 1][0] - s - 0.08)
        tempo = 1.0
        if nat > slot and slot > 0.2:
            tempo = min(nat / slot, a.max_tempo)
            tmp_in, tmp_out = tempfile.mktemp(suffix=".wav"), tempfile.mktemp(suffix=".wav")
            write_wav(tmp_in, x)
            audio_edit.tempo_shift_file(tmp_in, tmp_out, tempo)
            _, x = read_wav(tmp_out)
            x = x if x.ndim == 1 else x.mean(axis=1)
            os.remove(tmp_in); os.remove(tmp_out)
        dur = len(x) / SR
        start = s if a.align == "start" else s + max(0, (e - s - dur) / 2)
        i0 = int(start * SR)
        end_play = start + dur
        nxt = cues[i + 1][0] if i + 1 < len(cues) else 1e9
        status = "ok" if dur <= slot + 0.05 else ("runs-into-next-cue" if end_play > nxt else "overflows-slot")
        if status == "runs-into-next-cue":
            n_cut = int((nxt + 0.05 - start) * SR)
            x = dsp.fade(x[:n_cut], 0.002, 0.04, SR)
        if i0 + len(x) > len(buf):
            buf = np.pad(buf, (0, i0 + len(x) - len(buf)))
        buf[i0:i0 + len(x)] += x
        report.append(dict(i=i, start=round(s, 3), end=round(e, 3), slot=round(slot, 3), natural=round(nat, 3), tempo=round(tempo, 3),
                           played=round(dur, 3), status=status, text=text))
    out_len = int((a.duration or max(c[1] for c in cues) + 0.5) * SR)
    buf = buf[:max(out_len, int(max(r["start"] + r["played"] for r in report) * SR))]
    buf = dsp.normalize(buf, -3.0)
    wav = a.out if a.out.lower().endswith(".wav") else tempfile.mktemp(suffix=".wav")
    write_wav(wav, buf)
    bad = [r for r in report if r["status"] != "ok"]
    json.dump(dict(engine=eng, cues=report, problem_cues=len(bad)), open(a.out + ".fit.json", "w"), indent=1)
    if a.video:
        if a.mode == "replace":
            audio_edit.ff("-i", a.video, "-i", wav, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", a.out)
        else:
            fc = f"[0:a]volume={a.orig_db}dB[o];[o][1:a]amix=inputs=2:normalize=0:duration=first[m]"
            audio_edit.ff("-i", a.video, "-i", wav, "-filter_complex", fc, "-map", "0:v:0", "-map", "[m]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", a.out)
    print(json.dumps(dict(out=a.out, cues=len(cues), engine=eng, problem_cues=len(bad), fit_report=a.out + ".fit.json")))
    for r in bad[:8]:
        print(f"  cue {r['i']} {r['start']}s: {r['status']} (needs {r['natural']}s, slot {r['slot']}s, tempo x{r['tempo']}) -> shorten: {r['text'][:70]}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""instrument_showcase.py -- render one short phrase per instrument (V2 voices next to the 'real' voices) so you can audition them,
and write a standalone index.html with an audio player per voice.
  python3 instrument_showcase.py --out showcase/            (wav + mp3 clips, index.json, index.html)
Honest note: nobody has listened. The groups are there so you can A/B: left = V2 kit voices, right = real.py/voices.py voices."""
import argparse, base64, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge.song import Song, write_wav  # noqa: E402
from forge import instruments as I  # noqa: E402

PHRASE = [(0, 4, 57), (4, 4, 60), (8, 4, 64), (12, 4, 69), (16, 8, 67), (24, 4, 64), (28, 4, 60), (32, 12, 57)]
CHORD = [57, 60, 64]
GROUPS = [  # title, [(label, key, kwargs, octave shift)], side
    ("Piano", [("V2 piano", "piano", {}, 0), ("V2 piano_m1", "piano_m1", {}, 0)], [("piano_grand", "piano_grand", {}, 0), ("piano_bright", "piano_bright", {}, 0)]),
    ("Electric piano", [("V2 ep", "ep", {}, 0)], [("ep_rhodes", "ep_rhodes", {"tremolo": 0.6}, 0)]),
    ("Bells", [("V2 bell", "bell", {}, 12), ("V2 bell_tubular", "bell_tubular", {}, 12), ("V2 clock_bell", "clock_bell", {}, 12), ("V2 music_box", "music_box", {}, 12)],
     [("bell_church", "bell_church", {"ring": 0.8}, 12), ("glock", "glock", {}, 12), ("celesta", "celesta", {}, 12)]),
    ("Organ", [("V2 organ", "organ", {}, 0), ("V2 organ_rock", "organ_rock", {}, 0), ("V2 organ_pipe", "organ_pipe", {}, 0)],
     [("organ_drawbar", "organ_drawbar", {}, 0), ("organ_church", "organ_church", {}, 0)]),
    ("Guitar", [("V2 guitar_pluck", "guitar_pluck", {}, 0), ("V2 guitar_elec", "guitar_elec", {}, 0), ("V2 guitar_mute", "guitar_mute", {}, 0)],
     [("guitar_ks (clean)", "guitar_ks", {}, 0), ("guitar_crunch", "guitar_crunch", {}, 0), ("guitar_heavy", "guitar_heavy", {}, 0), ("guitar_lead", "guitar_lead", {}, 0)]),
    ("Strings and brass", [("V2 strings", "strings", {}, 0), ("V2 brass", "brass", {}, 0), ("V2 showtime_sax", "showtime_sax", {}, 0)],
     [("string_ensemble", "string_ensemble", {}, 0), ("brass_section", "brass_section", {}, 0)]),
    ("Plucks", [("V2 marimba", "marimba", {}, 0), ("V2 pluck", "pluck", {}, 0), ("V2 chip_lead", "chip_lead", {}, 12)],
     [("harp", "harp", {}, 0), ("harpsichord", "harpsichord", {}, 0), ("chip_pluck", "chip_pluck", {}, 12)]),
    ("Bass", [("V2 saw_bass", "saw_bass", {}, -24), ("V2 y2k_bass", "y2k_bass", {}, -24)], [("bass_guitar", "bass_guitar", {}, -24)]),
    ("Clock (A Grave Soul section)", [("V2 clock_tick", "clock_tick", {}, 0), ("V2 clock_bell", "clock_bell", {}, 0), ("V2 heartbeat", "heartbeat", {}, -21)], []),
]


def clip(key, kw, shift, path):
    S = Song(100, 3, seed=1, tail=2.5)
    S.track("v", reverb=0.25, gain_db=-3.0)
    if key == "clock_tick":
        for i in range(0, 48, 4): S.note("v", key, i, 0.5, 76 if (i // 4) % 2 == 0 else 72, 0.9)
    elif key == "heartbeat":
        for i in range(0, 48, 6): S.note("v", key, i, 1, 36, 0.9)
    else:
        for st, d, m in PHRASE: S.note("v", key, st, d, m + shift, 0.85, **kw)
        if key in ("piano", "piano_m1", "piano_grand", "piano_bright", "organ", "organ_rock", "organ_pipe", "organ_drawbar", "organ_church", "string_ensemble",
                   "strings", "brass", "brass_section", "guitar_elec", "guitar_heavy", "guitar_crunch", "ep", "ep_rhodes", "harp"):
            for nn in CHORD: S.note("v", key, 44, 4, nn + (shift if shift < 0 else 0) - 12, 0.6, **kw)
    out = S.mixdown(master=True, reverb_rt60=1.6, dynamics=0)
    import numpy as np
    m = out.mean(1) if out.ndim == 2 else out
    act = m[np.abs(m) > 0.01 * (np.abs(m).max() + 1e-9)]
    rms = float(np.sqrt(np.mean(act ** 2))) if len(act) else 1e-6
    out = out * (10 ** (-20 / 20.0) / max(rms, 1e-6))            # match loudness across voices (-20 dBFS RMS while sounding) so A/B is fair
    pk = float(np.abs(out).max())
    if pk > 0.89: out = out * (0.89 / pk)
    write_wav(path, out, S.sr)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="showcase"); ap.add_argument("--only", default=None, help="comma list of keys")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    index = []
    for title, left, right in GROUPS:
        g = {"title": title, "left": [], "right": []}
        for side, items in (("left", left), ("right", right)):
            for label, key, kw, sh in items:
                if only and key not in only: continue
                wav = os.path.join(a.out, key + ".wav"); mp3 = os.path.join(a.out, key + ".mp3")
                try:
                    clip(key, kw, sh, wav)
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ac", "1", "-b:a", "64k", mp3], check=True)
                    g[side].append({"label": label, "key": key, "mp3": os.path.basename(mp3)})
                    print("ok", key, flush=True)
                except Exception as e:
                    print("FAIL", key, repr(e)[:100], flush=True)
        index.append(g)
    json.dump(index, open(os.path.join(a.out, "index.json"), "w"), indent=1)
    cards = ""
    for g in index:
        def col(items, name):
            h = "".join(f'<div class="v"><b>{v["label"]}</b><audio controls preload="none" src="data:audio/mpeg;base64,{base64.b64encode(open(os.path.join(a.out, v["mp3"]), "rb").read()).decode()}"></audio></div>' for v in items)
            return f'<div class="col"><h3>{name}</h3>{h or "<i>none</i>"}</div>'
        cards += f'<section><h2>{g["title"]}</h2><div class="cols">{col(g["left"], "V2 kit")}{col(g["right"], "real voices")}</div></section>'
    open(os.path.join(a.out, "index.html"), "w").write(f'<!DOCTYPE html><meta charset="utf-8"><title>Instrument showcase</title><style>body{{font:16px system-ui;max-width:900px;margin:20px auto;padding:0 14px}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.v{{margin:8px 0}}audio{{width:100%}}@media(max-width:640px){{.cols{{grid-template-columns:1fr}}}}</style><h1>Instrument showcase</h1><p>Nobody has listened to these. Left: V2 kit voices. Right: real.py / voices.py voices.</p>{cards}')
    print("wrote", a.out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""compose.py -- generate an original piece of music from code (no samples, no downloads).

  python3 compose.py --genre synthwave --bars 32 --out song.wav
  python3 compose.py --genre forsaken --bpm 168 --key F# --scale phrygian --stems stems/ --out chase.wav
  python3 compose.py --profile ref_profile.json --out remake.wav        # match an analyzed reference's style
  python3 compose.py --genre house --override '{"hat": ...}'            # JSON deep-merged into the genre spec
  python3 compose.py --list

Writes <out> (16-bit stereo 44.1 kHz WAV) and <out>.beatmap.json (exact beats / downbeats / sections / drops,
ready for the editor bridge). --stems DIR also writes one WAV per instrument track.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import genres, song as songmod


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--genre", help="see --list (aliases like forsaken, 8bit, lo-fi work)")
    ap.add_argument("--bars", type=int)
    ap.add_argument("--duration", type=float, help="target seconds (overrides --bars, needs bpm known or random)")
    ap.add_argument("--bpm", type=float)
    ap.add_argument("--key", help="C C# D ... B")
    ap.add_argument("--scale", help="major minor dorian phrygian lydian mixolydian harmonic_minor pent_minor pent_major blues locrian")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--intensity", type=float, help="0-1; lower = sparser (default 0.75)")
    ap.add_argument("--swing", type=float)
    ap.add_argument("--profile", help="profile.json from analyze.py: derive genre/bpm/key/scale/intensity from it")
    ap.add_argument("--override", help="JSON string or file merged into the genre spec")
    ap.add_argument("--plan", help="JSON list of [section,fraction] e.g. '[[\"intro\",0.2],[\"drop\",0.8]]'")
    ap.add_argument("--stems", help="directory for per-track stems")
    ap.add_argument("--dynamics", type=float, default=None, help="0 = flat loudness, 1 = natural arc (quiet intro, rising build, full drop), 1.5 = dramatic")
    ap.add_argument("--midi", action="store_true", help="also write <out>.mid (open in any DAW)")
    ap.add_argument("--no-master", action="store_true")
    ap.add_argument("--out", default="forge_out.wav")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        for g, s in sorted(genres.GENRES.items()):
            print(f"{g:14s} bpm {s['bpm'][0]}-{s['bpm'][1]}  scales {','.join(s['scales'])}")
        print("aliases:", ", ".join(f"{k}->{v}" for k, v in sorted(genres.ALIASES.items())))
        return

    ov = {}
    if a.profile:
        from remake import params_from_profile
        p, ov = params_from_profile(json.load(open(a.profile)), a.genre)
        for k, v in p.items():
            if getattr(a, k, None) is None:
                setattr(a, k, v)
        print("profile ->", p, file=sys.stderr)
    a.genre = a.genre or "synthwave"
    if a.bars is None and not a.duration:
        a.bars = 32
    if a.override:
        ov = genres.deep_merge(ov, json.load(open(a.override)) if os.path.exists(a.override) else json.loads(a.override))
    bars = a.bars or 32
    if a.duration:
        bpm_guess = a.bpm or sum(genres.GENRES[genres.resolve(a.genre)]["bpm"]) / 2
        bars = max(4, int(round(a.duration / (240.0 / bpm_guess))))
        if not a.bpm:
            a.bpm = bpm_guess
    t0 = time.time()
    plan = [tuple(x) for x in json.loads(a.plan)] if a.plan else None
    s = genres.build(a.genre, bars, a.bpm, a.key, a.scale, a.seed, 0.75 if a.intensity is None else a.intensity, ov, plan, a.swing)
    dyn = a.dynamics if a.dynamics is not None else genres.deep_merge(genres.GENRES[genres.resolve(a.genre)], ov or {}).get("dynamics", 1.0)   # a genre can set its own default
    audio = s.mixdown(stems_dir=a.stems, master=not a.no_master, reverb_rt60=s.rt60, dynamics=dyn)
    songmod.write_wav(a.out, audio, s.sr)
    spec_all = genres.deep_merge(genres.GENRES[genres.resolve(a.genre)], ov or {})
    if spec_all.get("lufs") and not a.no_master:          # optional loudness target in the genre spec: "lufs": -14.5 (style-copy sets it from the reference)
        import analyze as _A
        from forge import dsp as _dsp
        for _ in range(2):
            cur = _A.loudness(a.out)["lufs"]
            if cur is None or abs(cur - spec_all["lufs"]) < 0.4: break
            audio = audio * (10 ** ((spec_all["lufs"] - cur) / 20.0))
            if spec_all["lufs"] > cur: audio = _dsp.limiter(audio, -1.0, sr=s.sr)
            songmod.write_wav(a.out, audio, s.sr)
    bm = s.beatmap()
    bm["meta"] = s.meta
    json.dump(bm, open(a.out + ".beatmap.json", "w"), indent=1)
    if a.midi:
        songmod.write_midi(a.out + ".mid", s)
    print(json.dumps(dict(out=a.out, seconds=round(len(audio) / s.sr, 1), render_s=round(time.time() - t0, 1), **s.meta)))


if __name__ == "__main__":
    main()

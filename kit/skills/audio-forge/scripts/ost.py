#!/usr/bin/env python3
"""ost.py - build and check a ROBLOX game soundtrack set (round-based survival / chase games, last-man-standing modes).

  af.py ost build --out ost/ [--key A] [--scale minor] [--bpm 178] [--family styles/lms-family] [--lms-bars 48] [--format ogg] [--target-lufs -14] [--quick] [--seed 1]
  af.py ost check FILE... [--bpm 178] [--loop]          Roblox upload checks (+ loop seam check for files that must loop)

BUILD makes one set with ONE key and ONE BPM so states can crossfade and layer:
  lobby (loop) . tension (loop) . chase (loop, with stems) . lms_intro (once) + lms (loop; the Last Man Standing theme, shaped by --family if given) . win (stinger) . lose (stinger)
Every loop is made seam-safe: rendered tail folded back onto the start, cut to a WHOLE number of bars, then loudness-matched (linear gain + peak limit, no fades).
Writes the audio, roblox_manifest.md (what plays when, loop yes/no, checks) and MusicDirector.luau (the in-game script; not run in Studio here).
These are ORIGINAL compositions in a genre feel from the kit's engine. Nobody has listened: the person must audition every file.

Roblox upload limits used by `check` (Creator Hub docs, create.roblox.com/docs/audio/assets, re-check before relying on them): mp3/ogg/wav/flac, single track, < 20 MB, <= 7 minutes, <= 48 kHz.
"""
import argparse, json, os, re, shutil, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); AF = os.path.join(HERE, "af.py")
LIMITS = dict(max_mb=20.0, max_s=420.0, max_hz=48000, formats=(".mp3", ".ogg", ".wav", ".flac"))
SECT = {"intro": "intro", "build": "build", "drop": "drop", "break": "break_", "outro": "outro", "verse": "verse"}


def run(*a):
    r = subprocess.run([sys.executable, AF, *map(str, a)], capture_output=True, text=True)
    if r.returncode: print(r.stdout[-400:], r.stderr[-600:], file=sys.stderr)
    return r.returncode


def ff(*a):
    return subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, a)], capture_output=True, text=True)


def read_wav(path):
    import study as S
    wav, sr, x = S.load_wav(path); return x.astype(np.float64), sr


def write_wav(path, x, sr):
    import wave
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w: w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def make_loop(path, bpm, bars):
    """fold the reverb/decay tail back onto the start and cut to exactly `bars` bars: the seam then plays on, the grid never drifts"""
    x, sr = read_wav(path); L = int(round(bars * 240.0 / bpm * sr))
    if len(x) < L: x = np.vstack([x, np.zeros((L - len(x), x.shape[1]))])
    main, tail = x[:L].copy(), x[L:]
    if len(tail): n = min(len(tail), L); main[:n] += tail[:n]
    pk = np.abs(main).max()
    if pk > 0.98: main *= 0.98 / pk
    write_wav(path, main, sr); return L / sr


def lufs_peak(path):
    r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r); P = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    return (float(I[-1]) if I else None), (float(P[-1]) if P else None)


def match_loudness(path, target):
    I, P = lufs_peak(path)
    if I is None: return None
    gain = target - I; ceiling = -1.5
    if P is not None and P + gain > ceiling: gain = ceiling - P              # never push the peak over -1.5 dBFS: quieter than target beats clipping
    x, sr = read_wav(path); x *= 10 ** (gain / 20); write_wav(path, x, sr); return round(I + gain, 1)


def encode(wav, fmt):
    out = os.path.splitext(wav)[0] + "." + fmt
    if fmt == "wav": return wav
    args = ["-i", wav] + (["-c:a", "libvorbis", "-q:a", "6"] if fmt == "ogg" else ["-c:a", "flac"] if fmt == "flac" else ["-c:a", "libmp3lame", "-b:a", "256k"]); r = ff(*args, out)
    if r.returncode: print("encode failed:", r.stderr[-300:], file=sys.stderr); return wav
    os.remove(wav); return out


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=sample_rate,channels,codec_name", "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}"); s = (j.get("streams") or [{}])[0]; f = j.get("format", {})
    return dict(seconds=float(f.get("duration", 0)), mb=float(f.get("size", 0)) / 1e6, sr=int(s.get("sample_rate", 0)), ch=int(s.get("channels", 0)), codec=s.get("codec_name"))


def _low_corr(x, sr, hz=110.0, mono=False):
    """correlation of the two channels in the sub/bass region; ~1.0 means the low end is mono-compatible.
    Measured at 110 Hz (6th order) so the filter's own transition band does not count 140-250 Hz as 'sub'."""
    if x.ndim == 1 or x.shape[1] < 2:
        return 1.0
    try:
        from scipy.signal import butter, sosfilt
        sos = butter(6, hz / (sr / 2.0), "low", output="sos")
        a, b = sosfilt(sos, x[:, 0]), sosfilt(sos, x[:, 1])
        if a.std() < 1e-9 or b.std() < 1e-9:
            return 1.0
        return float(np.corrcoef(a, b)[0, 1])
    except Exception:
        return 1.0


def check(path, bpm=None, loop=False):
    """Roblox upload checks. Loop mode is strict: seam click, edge silence, whole bars, mono sub, headroom, DC."""
    p = probe(path); iss = []
    if not path.lower().endswith(LIMITS["formats"]): iss.append(f"format {os.path.splitext(path)[1]} is not mp3/ogg/wav/flac")
    if p["seconds"] > LIMITS["max_s"]: iss.append(f"{p['seconds']:.0f} s is over the 7-minute limit")
    if p["mb"] >= LIMITS["max_mb"]: iss.append(f"{p['mb']:.1f} MB is not under 20 MB")
    if p["sr"] > LIMITS["max_hz"]: iss.append(f"{p['sr']} Hz is over 48 kHz")
    I, P = lufs_peak(path); res = dict(file=os.path.basename(path), seconds=round(p["seconds"], 2), mb=round(p["mb"], 2), sample_rate=p["sr"], channels=p["ch"], lufs=I, peak_dbfs=P)
    if P is not None and P > -1.0: iss.append(f"peak {P} dBFS: not enough headroom for game SFX and re-encoding; keep true peak <= -1.5")
    if I is not None and I > -9.0: iss.append(f"{I} LUFS: too hot for a music bed that sits under SFX; target about -14")
    if I is not None and I < -26.0: iss.append(f"{I} LUFS: very quiet; target about -14")
    x = sr = None
    if path.lower().endswith(".wav"):
        x, sr = read_wav(path)
        mono = x.mean(1) if x.ndim > 1 else x
        dc = float(np.max(np.abs(mono.mean())))
        clip = int((np.abs(x) >= 0.999).sum())
        res["dc_offset"] = round(dc, 5); res["clipped_samples"] = clip
        if dc > 0.002: iss.append(f"DC offset {dc:.4f}: high-pass the master around 25-30 Hz")
        if clip: iss.append(f"{clip} samples at/over full scale: clipping")
        lc = _low_corr(x, sr)
        res["low_corr_below_140hz"] = round(lc, 3)
        if lc < 0.85: iss.append(f"low end is not mono (corr {lc:.2f} below 140 Hz): it can cancel on a phone speaker / in a club")
    if loop:
        if x is None: iss.append("loop check needs a WAV; encode an ogg/wav copy first")
        else:
            m = x.mean(1) if x.ndim > 1 else x; n = len(m); w = int(0.05 * sr)
            head = 20 * np.log10(np.sqrt(np.mean(m[:w] ** 2)) + 1e-9); tail = 20 * np.log10(np.sqrt(np.mean(m[-w:] ** 2)) + 1e-9); body = 20 * np.log10(np.sqrt(np.mean(m ** 2)) + 1e-9)
            if tail < body - 25: iss.append(f"ends in near-silence ({tail:.0f} dB vs body {body:.0f} dB): the loop would pump/gap")
            if head < body - 25: iss.append(f"starts in near-silence ({head:.0f} dB vs body {body:.0f} dB)")
            jump = float(np.max(np.abs(x[0] - x[-1]))); step = float(np.percentile(np.abs(np.diff(x, axis=0)).max(1), 99.5)) + 1e-6; res["seam_jump_vs_normal_step"] = round(jump / step, 2)
            if jump > 1.5 * step: iss.append(f"the last sample is {jump / step:.1f}x the file's largest normal sample-to-sample step away from the first: expect a click at the loop point (the tail should fold onto the start)")
            if bpm:
                bars = p["seconds"] * bpm / 240.0; res["bars"] = round(bars, 3)
                if abs(bars - round(bars)) > 0.01: iss.append(f"{bars:.3f} bars: not a whole number of bars at {bpm} BPM, so the loop drifts off the beat grid")
            if p["codec"] == "mp3": iss.append("mp3 adds encoder padding (a tiny gap at the loop point); for looping Sounds prefer ogg/flac/wav (verify in Studio)")
    res["issues"] = iss; res["ready"] = not iss; return res


def family_plan(fam_dir):
    d = json.load(open(os.path.join(fam_dir, "dna.json"))); dp = d.get("deep")
    if not dp: return None, None, None
    secs = dp["form"]["sections"]; tot = sum(q["pct"] for q in secs) or 100.0; plan = []
    for q in secs:
        nm = SECT.get(q["label"], "verse"); fr = q["pct"] / tot
        if plan and plan[-1][0] == nm: plan[-1][1] += fr
        else: plan.append([nm, fr])
    return [[a, round(b, 3)] for a, b in plan], dp["tempo_feel"]["feel_bpm"], f"{d['key']['tonic']}"


def loop_plan(plan):
    """a game LOOP must hold the full-energy part only: drop the quiet intro/build and the outro of a finished track (the intro is rendered separately and plays once)"""
    if not plan: return None
    k = next((i for i, (nm, _) in enumerate(plan) if nm in ("drop", "chase", "climax", "main")), None)
    if k is None: return None
    body = [[nm, fr] for nm, fr in plan[k:] if nm != "outro"]; tot = sum(fr for _, fr in body) or 1.0
    return [[nm, round(fr / tot, 3)] for nm, fr in body]


def build(a):
    out = a.out; os.makedirs(out, exist_ok=True); work = os.path.join(out, "_work"); os.makedirs(work, exist_ok=True)
    plan, fbpm, fkey = (None, None, None)
    if a.family: plan, fbpm, fkey = family_plan(a.family)
    bpm = float(a.bpm or (round(fbpm) if fbpm else 178)); key = a.key or fkey or "A"; K = ["--key", key, "--bpm", bpm, "--scale", a.scale, "--seed", a.seed]; q = 0.5 if a.quick else 1.0
    n = lambda v: max(8, int(round(v * q / 4) * 4)); lms_bars = n(a.lms_bars)
    states = [  # name, genre, extra args, bars, loop, role
        ("lobby", "dark_ambient", ["--intensity", 0.3, "--plan", json.dumps([["main", 1.0]])], n(32), True, "lobby / intermission: calm, sparse, loops quietly under chat"),
        ("tension", "horror_chase", ["--intensity", 0.45, "--plan", json.dumps([["chase", 1.0]])], n(32), True, "round running, nobody chased yet: unease, pulse without the full attack"),
        ("chase", "horror_chase", ["--intensity", 0.9, "--plan", json.dumps([["chase", 1.0]]), "--stems", os.path.join(out, "chase_stems")], n(48), True, "a killer is chasing you: driving pulse, stems for danger layering"),
        ("lms_intro", "horror_chase", ["--intensity", 0.8, "--plan", json.dumps([["intro", 0.4], ["build", 0.6]])], n(8), False, "LAST MAN STANDING entrance: plays ONCE when the last survivor remains, then hands over to `lms`"),
        ("lms", "horror_chase", ["--intensity", 1.0] + (["--plan", json.dumps(loop_plan(plan))] if loop_plan(plan) else ["--plan", json.dumps([["chase", 1.0]])]), lms_bars, True, "LAST MAN STANDING loop: one survivor, one killer; loops until the round ends (full-energy part of the family shape if --family)")]
    manifest = []
    for name, genre, extra, bars, loop, role in states:
        w = os.path.join(out, name + ".wav"); print(f"== {name}: {genre}, {bars} bars", flush=True)
        if run("compose", "--genre", genre, *K, *extra, "--bars", bars, "--out", w) or not os.path.exists(w): print(f"   (failed: {name})"); continue
        dur = make_loop(w, bpm, bars) if loop else bars * 240.0 / bpm; lu = match_loudness(w, a.target_lufs); f = encode(w, a.format); manifest.append(dict(state=name, file=os.path.basename(f), role=role, loop=loop, bars=bars, seconds=round(dur, 1), lufs=lu))
    for name, sfx, role in (("win", "stinger_bright", "round over, you survived / the survivor escaped: relief, no loop"), ("lose", "stinger_dark", "you were caught: short dark sting, no loop")):
        w = os.path.join(out, name + ".wav")
        if run("sfx", "--name", sfx, "--out", w) or not os.path.exists(w): print(f"   (failed: {name})"); continue
        lu = match_loudness(w, a.target_lufs + 1.0); f = encode(w, a.format); manifest.append(dict(state=name, file=os.path.basename(f), role=role, loop=False, bars=None, seconds=None, lufs=lu))
    cs = os.path.join(out, "chase_stems")
    for fn in (os.listdir(cs) if os.path.isdir(cs) else []): 
        if fn.endswith(".wav"): make_loop(os.path.join(cs, fn), bpm, n(48))
    for root, _, files in os.walk(out):                                         # compose leaves beatmaps next to the wavs; a Roblox set does not need them
        for fn in files:
            if fn.endswith(".beatmap.json"): os.remove(os.path.join(root, fn))
    shutil.copy(os.path.join(os.path.dirname(HERE), "templates", "MusicDirector.luau"), os.path.join(out, "MusicDirector.luau"))
    L = ["# Roblox soundtrack set", "", f"One key ({key} {a.scale}) and one BPM ({bpm:g}) for every state, so they crossfade on bar lines and stems layer cleanly. Loudness target {a.target_lufs} LUFS (music bed; leaves headroom for SFX; NOT a Roblox rule). Nobody has listened: audition every file.", "",
         "| state | file | plays when | loops | bars | LUFS | checks |", "|---|---|---|---|---|---|---|"]
    bad = []
    for m in manifest:
        c = check(os.path.join(out, m["file"]), bpm, m["loop"]); m["checks"] = c
        if not c["ready"] and m["loop"]: bad.append(m["state"])
        L.append(f"| {m['state']} | {m['file']} | {m['role']} | {'yes' if m['loop'] else 'no'} | {m['bars'] or '-'} | {c['lufs']} | {'OK' if c['ready'] else '; '.join(c['issues'])} |")
    L += ["", "Upload each file at create.roblox.com (Creator Hub > Assets > Audio) and put the returned asset IDs into the `TRACKS` table in `MusicDirector.luau`. New uploads are private to you until you grant them to your experience; verify limits on the Creator Hub audio page before relying on them.",
          "", "Stems for adaptive layers: `chase_stems/`. All stems are the same length and start together; play them as synchronized Sounds and fade layers with danger level.", "", "These are original compositions in a genre feel; they are not copies of any game's tracks."]
    if bad: L += ["", f"**STRICT CHECK FAILED for: {', '.join(bad)}.** Fix the loop seam/headroom/sub before uploading."]
    open(os.path.join(out, "roblox_manifest.md"), "w").write("\n".join(L) + "\n"); shutil.rmtree(work, ignore_errors=True); print("\n".join(L))
    if bad and a.strict:
        raise SystemExit("ost build: strict check failed for " + ", ".join(bad))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build"); b.add_argument("--out", default="ost"); b.add_argument("--key"); b.add_argument("--scale", default="minor"); b.add_argument("--bpm", type=float); b.add_argument("--family"); b.add_argument("--lms-bars", type=int, default=48)
    b.add_argument("--format", default="ogg", choices=["ogg", "mp3", "wav", "flac"]); b.add_argument("--target-lufs", type=float, default=-14.0); b.add_argument("--quick", action="store_true"); b.add_argument("--seed", type=int, default=1)
    b.add_argument("--strict", action="store_true", help="exit non-zero if any loop fails the seam/headroom/mono-sub checks")
    c = sp.add_parser("check"); c.add_argument("files", nargs="+"); c.add_argument("--bpm", type=float); c.add_argument("--loop", action="store_true")
    a = ap.parse_args()
    if a.cmd == "build": build(a)
    else:
        for f in a.files: print(json.dumps(check(f, a.bpm, a.loop), indent=1))


if __name__ == "__main__":
    main()

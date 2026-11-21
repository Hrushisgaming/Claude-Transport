#!/usr/bin/env python3
"""stem_mix.py - mix a folder of WAV stems into one finished mix (EQ carve, mono bass, sidechain, width, loudness, limit).

  af.py stem_mix stems/ --out mix.wav
  af.py stem_mix stems/ --out mix.wav --target-lufs -14 --bpm 178
  af.py stem_mix stems/ --out mix.wav --reference styles/lms-family/dna.json
  af.py stem_mix stems/ --out mix.wav --processed-out stems_processed/ --json

WHAT IT DOES (in this order, per stem)
  1. role detection from the file name AND from the audio itself (bass / drums / guitar / pad / lead / other)
  2. EQ carve: high-pass every melodic stem, a small 250-450 Hz cut on guitars and pads (the classic "mud" carve),
     a high-pass on the bass only where it is needed, a presence lift on the lead
  3. mono bass: everything below 140 Hz is folded to mono (so it survives phone speakers and club systems)
  4. sidechain: the kick's own onsets duck the bass and the pads (depth per role); if there is no kick stem the
     low-band onsets of the drum stem are used instead
  5. stereo width: guitars and pads get a little extra width, the low end stays mono
  6. master: DC removal, gentle glue compression, soft saturation, look-ahead limiter, then loudness matching
     to --target-lufs (measured with ffmpeg ebur128, default -14 LUFS for a game bed)

It measures and processes; whether the result sounds good is the person's call. Audition it.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audioutil as U
from forge import dsp

BASS_WORDS = ("bass", "sub", "808", "low", "kick_bass")
DRUM_WORDS = ("kick", "snare", "clap", "hat", "drum", "perc", "tom", "ride", "crash", "cymbal", "breakbeat")
GUITAR_WORDS = ("guitar", "gtr", "strat", "les")
PAD_WORDS = ("pad", "strings", "choir", "organ", "amb", "atmos", "texture")
LEAD_WORDS = ("lead", "vox", "vocal", "melody", "arp", "synth", "bell", "piano")


def role_of(name, x, sr):
    """name first, then the sound itself (centroid + low/high balance)"""
    n = os.path.splitext(os.path.basename(name))[0].lower()
    if any(w in n for w in BASS_WORDS): return "bass"
    if any(w in n for w in DRUM_WORDS): return "drums"
    if any(w in n for w in GUITAR_WORDS): return "guitar"
    if any(w in n for w in PAD_WORDS): return "pad"
    if any(w in n for w in LEAD_WORDS): return "lead"
    # fall back to the spectrum
    m = U.to_stereo(x).mean(1)
    if len(m) < 1024:
        return "other"
    n_fft = min(len(m), 1 << 18)
    spec = np.abs(np.fft.rfft(m[:n_fft]))
    f = np.fft.rfftfreq(n_fft, 1.0 / sr)
    tot = spec.sum() + 1e-9
    low = spec[f < 120].sum() / tot
    mid = spec[(f >= 200) & (f < 2500)].sum() / tot
    high = spec[f > 5000].sum() / tot
    cent = float((f * spec).sum() / tot)
    if low > 0.45: return "bass"
    if high > 0.22 and cent > 2500: return "drums"
    if mid > 0.5: return "lead"
    return "other"


def carve(x, sr, role):
    """EQ carve per role. returns (y, notes)"""
    notes = []
    x = x - x.mean(axis=0, keepdims=True)          # DC first: a DC step would ring through the filters
    if role == "bass":
        x = dsp.hp(x, 25, sr, 2); notes.append("hp 25 Hz")
        x = dsp.lp(x, 3200, sr, 2); notes.append("lp 3.2 kHz")
    elif role == "drums":
        x = dsp.hp(x, 28, sr, 2); notes.append("hp 28 Hz")
    elif role == "guitar":
        x = dsp.hp(x, 120, sr, 2); notes.append("hp 120 Hz")
        x = dsp.bp(x, 250, 450, sr, 2); notes.append("carve 250-450 Hz")
        x = x * 0.93
    elif role == "pad":
        x = dsp.hp(x, 150, sr, 2); notes.append("hp 150 Hz")
        x = dsp.bp(x, 280, 520, sr, 2); notes.append("carve 280-520 Hz")
        x = x * 0.94
    elif role == "lead":
        x = dsp.hp(x, 100, sr, 2); notes.append("hp 100 Hz")
    else:
        x = dsp.hp(x, 60, sr, 2); notes.append("hp 60 Hz")
    return x, notes


def kick_hits(x, sr):
    """onset positions of the kick: low-band energy peaks"""
    m = U.to_stereo(x).mean(1)
    from scipy.signal import butter, sosfilt
    sos = butter(2, 120.0 / (sr / 2.0), "low", output="sos")
    low = sosfilt(sos, m)
    env = np.abs(low)
    if len(env) < 64:
        return []
    k = max(1, int(0.012 * sr))
    env = np.convolve(env, np.ones(k) / k, mode="same")
    thr = float(np.percentile(env, 92))
    dist = max(1, int(0.12 * sr))
    peaks, last = [], -10 ** 9
    for i in range(1, len(env) - 1):
        if env[i] > thr and env[i] >= env[i - 1] and env[i] > env[i + 1] and i - last > dist:
            peaks.append(i); last = i
    return peaks


def sidechain_depth(role, mode):
    if mode == "off":
        return 0.0
    base = dict(bass=0.35, pad=0.20, guitar=0.14, lead=0.08, drums=0.0, other=0.0).get(role, 0.0)
    return base if mode == "auto" else base * 0.6


def build_mix(stems, target_lufs=-14.0, width=0.012, sidechain="auto", limiter_db=-1.0):
    """stems: list of (name, x, sr). returns (mix, report)"""
    sr = stems[0][2]
    n = max(len(s[1]) for s in stems)
    roles = {}
    prepared = []
    for name, x, s_sr in stems:
        x = U.fit_length(U.to_stereo(np.asarray(x, dtype=np.float64)), n)
        r = role_of(name, x, sr)
        y, notes = carve(x, sr, r)
        roles[name] = r
        prepared.append((name, y, r, notes))
    # kick source: a kick-named stem, else the drums stem's own low-band onsets
    hits = []
    src = None
    for name, y, r, _ in prepared:
        if "kick" in name.lower():
            src = y; break
    if src is None:
        for name, y, r, _ in prepared:
            if r == "drums":
                src = y; break
    if src is not None:
        hits = kick_hits(src, sr)
    out = np.zeros((n, 2))
    rows = []
    processed = []
    for name, y, r, notes in prepared:
        gain = 1.0
        if r == "drums": gain = 1.0
        elif r == "bass": gain = 0.9
        elif r == "pad": gain = 0.85
        elif r == "guitar": gain = 0.9
        elif r == "lead": gain = 0.95
        d = sidechain_depth(r, sidechain)
        if d and hits:
            y = y * dsp.sidechain_curve(n, hits, d, 0.18, sr=sr)[:, None]
        if r in ("guitar", "pad") and width:
            y = dsp.widen(y, width, sr)
        if r == "bass":
            y = dsp.mono_below(y, 160.0, sr)
        y = y * gain
        y = dsp.limiter(y, -1.0, sr=sr)      # per-stem safety: a cut or a filter transient must not clip
        out += y
        processed.append((os.path.splitext(name)[0] + ".wav", y))
        rows.append(dict(stem=name, role=r, gain=round(20 * np.log10(gain + 1e-9), 2), eq=notes,
                         sidechain_db=round(d * 100), peak_dbfs=round(U.peak_db(y), 2), rms_db=round(U.rms_db(y.mean(1)), 2)))
    # master
    out = dsp.hp(out, 25, sr, 2)
    out = dsp.compress(out, -16, 1.5, 0.03, 0.25, 0.8, sr)
    sat = dsp.asym_drive(out * 0.85, 1.2, 0.04)
    out = 0.8 * out + 0.2 * sat * (np.abs(out).max() + 1e-9)
    out = dsp.limiter(out, limiter_db, sr=sr)
    out = dsp.normalize(out, limiter_db)
    report = dict(stems=rows, kick_hits=len(hits), sidechain=sidechain, width=width,
                  pre_master_peak_dbfs=round(U.peak_db(out), 2), target_lufs=target_lufs)
    return out, report, processed


def match_lufs(x, sr, target, ceiling=-1.0):
    """write a temp file, measure with ebur128, apply the gain, re-limit"""
    p = U.temp_wav(x, sr)
    try:
        I, P = U.lufs_peak(p)
    finally:
        try:
            os.remove(p)
        except OSError:
            pass
    if I is None:
        return x, None
    gain_db = target - I
    y = x * (10 ** (gain_db / 20.0))
    y = dsp.limiter(y, ceiling, sr=sr)
    if gain_db < 0:
        y = dsp.normalize(y, min(ceiling, U.peak_db(x) + gain_db))
    return y, round(I + gain_db, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stems", help="folder with the stem WAVs")
    ap.add_argument("--out", default="mix.wav")
    ap.add_argument("--target-lufs", type=float, default=-14.0)
    ap.add_argument("--width", type=float, default=0.012)
    ap.add_argument("--sidechain", choices=["auto", "on", "off"], default="auto")
    ap.add_argument("--reference", help="dna.json: use its loudness/width as the target instead of --target-lufs")
    ap.add_argument("--processed-out", help="also write the processed stems here")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(a.stems):
        raise SystemExit(f"stem_mix: not a folder: {a.stems}")
    files = sorted([f for f in os.listdir(a.stems) if f.lower().endswith((".wav", ".flac", ".mp3", ".ogg", ".m4a"))])
    if not files:
        raise SystemExit(f"stem_mix: no audio files in {a.stems}")
    stems = []
    for f in files:
        x, sr = U.read_audio(os.path.join(a.stems, f))
        stems.append((f, x, sr))
    sr = stems[0][2]
    if any(s[2] != sr for s in stems):
        raise SystemExit("stem_mix: all stems must share the sample rate (resample them first)")
    target = a.target_lufs
    width = a.width
    if a.reference:
        dna = json.load(open(a.reference))
        target = float(dna.get("mix", {}).get("lufs") or target)
        width = 0.012 if dna.get("mix", {}).get("side_to_mid_db", 0) < 2 else 0.02
    mix, rep, processed = build_mix(stems, target, width, a.sidechain)
    mix, got = match_lufs(mix, sr, target)
    rep["lufs_after"] = got
    rep["output"] = os.path.abspath(a.out)
    rep["sample_rate"] = sr
    rep["seconds"] = round(len(mix) / sr, 2)
    U.write_wav(a.out, mix, sr)
    if a.processed_out:
        os.makedirs(a.processed_out, exist_ok=True)
        for name, y in processed:
            U.write_wav(os.path.join(a.processed_out, name), dsp.normalize(y, -1.5), sr)
        rep["processed_out"] = os.path.abspath(a.processed_out)
    if a.json:
        print(json.dumps(rep, indent=1))
    else:
        print(f"# stem mix: {len(stems)} stem(s) -> {a.out}")
        print(f"target {target} LUFS, measured {got} LUFS, {rep['seconds']} s, {rep['kick_hits']} kick onsets used for the sidechain\n")
        print(f"{'stem':28s} {'role':8s} {'gain dB':>8s} {'peak dBFS':>10s}  eq / sidechain")
        for r in rep["stems"]:
            print(f"{r['stem']:28s} {r['role']:8s} {r['gain']:8.1f} {r['peak_dbfs']:10.1f}  {', '.join(r['eq'])} | sc {r['sidechain_db']}%")
        print("\nNobody has listened to this mix. Audition it before shipping.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

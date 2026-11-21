#!/usr/bin/env python3
"""analyze.py -- listen to a reference track and write a style profile (JSON).

    python3 analyze.py ref.mp3 --out profile.json [--max-seconds 300] [--engine auto|builtin|librosa] [--stems stems_dir]

Needs only numpy + scipy + ffmpeg. If librosa is installed it is used to cross-check tempo/beats.
If --stems points at a demucs output dir (drums.wav bass.wav other.wav vocals.wav) the drum pattern, bass notes and
melody range are measured from the isolated stems, which is much more accurate than the full mix.

The profile holds: tempo (+candidates, steadiness), beats / downbeats / meter, key + mode (+runner-ups), per-bar chords,
16-step kick/snare/hat patterns, swing, loudness (LUFS), dynamics, stereo width, band energy balance, brightness,
percussive/harmonic split, structure (sections with energy), drop candidates, a per-beat energy curve and a genre guess.
Everything is measured, nothing is copied: remake.py turns it into an ORIGINAL piece in the same style.
"""
import argparse, json, os, re, subprocess, sys
import numpy as np
from scipy import signal
from scipy.ndimage import median_filter, uniform_filter1d, maximum_filter1d

SR = 22050
NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
KS_MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KS_MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


# ── io ──────────────────────────────────────────────────────────────────────
def decode(path, sr=SR, start=0.0, max_s=None, channels=2):
    cmd = ["ffmpeg", "-v", "error", "-nostdin"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", path]
    if max_s:
        cmd += ["-t", str(max_s)]
    cmd += ["-f", "f32le", "-acodec", "pcm_f32le", "-ac", str(channels), "-ar", str(sr), "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if channels == 2:
        x = x[: len(x) // 2 * 2].reshape(-1, 2)
    return x.astype(np.float64)


def loudness(path, max_s=None):
    cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-i", path]
    if max_s:
        cmd += ["-t", str(max_s)]
    cmd += ["-af", "ebur128=peak=true", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    seg = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    def g(pat):
        m = re.search(pat, seg)
        return float(m.group(1)) if m else None
    return dict(lufs=g(r"I:\s+(-?[\d.]+) LUFS"), lra=g(r"LRA:\s+(-?[\d.]+) LU"), true_peak_db=g(r"Peak:\s+(-?[\d.]+) dBFS"))


# ── features ────────────────────────────────────────────────────────────────
def stft_mag(x, n_fft, hop):
    f, t, Z = signal.stft(x, SR, nperseg=n_fft, noverlap=n_fft - hop, boundary=None, padded=False)
    return f, t, np.abs(Z)


def onset_envelopes(mono, hop=256, n_fft=1024):
    f, t, S = stft_mag(mono, n_fft, hop)
    L = np.log1p(S * 50.0)
    d = np.maximum(np.diff(L, axis=1, prepend=L[:, :1]), 0)
    bands = dict(low=(30, 160), mid=(160, 2500), high=(5500, 11000), snare=(1500, 6000))
    env = {}
    for k, (lo, hi) in bands.items():
        m = (f >= lo) & (f < hi)
        env[k] = d[m].sum(axis=0)
    env["all"] = d.sum(axis=0)
    for k in env:
        e = env[k]
        e = e - uniform_filter1d(e, size=int(0.5 * SR / hop) | 1)
        env[k] = np.maximum(e, 0)
        p = np.percentile(env[k], 99) + 1e-9
        env[k] = env[k] / p
    return env, t, f, S


def estimate_tempo(env, fps, lo=60, hi=200):
    n = len(env)
    e = env - env.mean()
    ac = np.fft.irfft(np.abs(np.fft.rfft(e, 2 * n)) ** 2)[:n]
    ac = ac / (ac[0] + 1e-9)
    bpms = np.arange(lo, hi + 0.05, 0.1)
    lags = fps * 60.0 / bpms
    def at(l):
        i = np.clip(l, 0, n - 2)
        i0 = i.astype(int)
        fr = i - i0
        return ac[i0] * (1 - fr) + ac[np.minimum(i0 + 1, n - 1)] * fr
    score = at(lags) + 0.5 * at(2 * lags) + 0.25 * at(4 * lags) + 0.3 * at(lags / 2)
    prior = np.exp(-0.5 * (np.log2(bpms / 120.0) / 0.9) ** 2)
    sc = score * prior
    order = np.argsort(sc)[::-1]
    cands = []
    for i in order:
        b = bpms[i]
        if all(abs(b - c["bpm"]) / c["bpm"] > 0.04 for c in cands):
            cands.append(dict(bpm=round(float(b), 2), score=round(float(sc[i]), 4)))
        if len(cands) >= 5:
            break
    return cands


def grid_fit(env, fps, bpm):
    """refine bpm and find phase so a regular grid best lines up with onsets"""
    n = len(env)
    best = (-1, bpm, 0.0)
    for b in np.arange(bpm * 0.985, bpm * 1.0151, bpm * 0.0005):
        period = fps * 60.0 / b
        ph = np.arange(0, period, 0.5)
        for p in ph:
            idx = np.arange(p, n - 1, period)
            i0 = idx.astype(int)
            fr = idx - i0
            s = float(np.mean(env[i0] * (1 - fr) + env[np.minimum(i0 + 1, n - 1)] * fr))
            if s > best[0]:
                best = (s, b, p)
    s, b, p = best
    return b, p / fps, s / (env.mean() + 1e-9)


def dp_beats(env, fps, bpm, tight=100.0):
    n = len(env)
    period = fps * 60.0 / bpm
    score = np.zeros(n)
    back = np.zeros(n, dtype=int)
    win = int(period * 0.5)
    for i in range(n):
        lo = max(0, i - int(period * 1.5))
        hi = max(0, i - int(period * 0.6))
        if hi <= lo:
            score[i] = env[i]
            back[i] = -1
            continue
        prev = np.arange(lo, hi)
        pen = -tight * (np.log((i - prev) / period) ** 2)
        c = score[prev] + pen
        j = int(np.argmax(c))
        score[i] = env[i] + c[j]
        back[i] = prev[j]
    i = int(np.argmax(score[-int(period):])) + n - int(period)
    out = []
    while i >= 0:
        out.append(i)
        i = back[i]
    return np.array(out[::-1]) / fps


def estimate_meter(env, fps, beats):
    """returns (beats_per_bar, downbeat_phase, confidence) from accent contrast on low-band emphasis"""
    def val(bt):
        i = np.clip((np.asarray(bt) * fps).astype(int), 0, len(env) - 1)
        return maximum_filter1d(env, 3)[i]
    v = val(beats)
    base = v.mean() + 1e-9
    best = None
    for bpb, prior in ((4, 1.12), (3, 1.0)):
        if len(v) < bpb * 2:
            continue
        sums = [v[p::bpb].mean() for p in range(bpb)]
        ph = int(np.argmax(sums))
        contrast = sums[ph] / (np.mean(sums) + 1e-9) * prior
        if best is None or contrast > best[0]:
            best = (contrast, bpb, ph)
    if best is None:
        return 4, 0, 0.0
    return best[1], best[2], round(float(best[0] - 1.0), 3)


def chroma(mono, hop=2048, n_fft=8192, fmin=70, fmax=2200, harmonic=True):
    f, t, S = stft_mag(mono, n_fft, hop)
    m = (f >= fmin) & (f <= fmax)
    f, S = f[m], S[m]
    if harmonic:
        S = median_filter(S, size=(1, 15))
    midi = 69 + 12 * np.log2(f / 440.0)
    pc = np.round(midi).astype(int) % 12
    dev = np.abs(midi - np.round(midi))
    w = np.exp(-0.5 * (dev / 0.25) ** 2) * (1.0 / (1 + (f / 800.0)))
    C = np.zeros((12, S.shape[1]))
    for k in range(12):
        C[k] = (np.sqrt(S[pc == k]) * w[pc == k][:, None]).sum(axis=0)
    C /= (C.max(axis=0, keepdims=True) + 1e-9)
    return C, t


def estimate_key(C):
    v = C.mean(axis=1)
    out = []
    for k in range(12):
        for mode, prof in (("major", KS_MAJ), ("minor", KS_MIN)):
            r = np.corrcoef(v, np.roll(prof, k))[0, 1]
            out.append((r, NOTE[k], mode))
    out.sort(reverse=True)
    return [dict(key=n, mode=m, score=round(float(r), 3)) for r, n, m in out[:4]], v


CHORD_T = {}
for _r in range(12):
    for _q, _iv in (("", (0, 4, 7)), ("m", (0, 3, 7)), ("dim", (0, 3, 6)), ("5", (0, 7))):
        t = np.zeros(12)
        for i in _iv:
            t[(_r + i) % 12] = 1.0
        CHORD_T[(NOTE[_r] + _q)] = t / np.linalg.norm(t)


def chord_label(c):
    c = c / (np.linalg.norm(c) + 1e-9)
    best = max(CHORD_T.items(), key=lambda kv: float(kv[1] @ c))
    return best[0], float(best[1] @ c)


# ── structure ───────────────────────────────────────────────────────────────
def novelty_boundaries(F, min_gap=4, k=4, thresh=0.6):
    Fz = (F - F.mean(0)) / (F.std(0) + 1e-9)
    D = np.linalg.norm(Fz[:, None, :] - Fz[None, :, :], axis=2)
    Ssim = np.exp(-D / (D.mean() + 1e-9))
    n = len(Fz)
    kern = np.ones((2 * k, 2 * k))
    kern[:k, k:] = -1
    kern[k:, :k] = -1
    nov = np.zeros(n)
    P = np.pad(Ssim, k, mode="edge")
    for i in range(n):
        nov[i] = (P[i:i + 2 * k, i:i + 2 * k] * kern).sum()
    nov = np.maximum(nov, 0)
    nov /= nov.max() + 1e-9
    peaks, _ = signal.find_peaks(nov, height=thresh * 0.5, distance=min_gap)
    return [int(p) for p in peaks if 2 <= p <= n - 2], nov


# ── main analysis ───────────────────────────────────────────────────────────
def pattern_from_flux(flux, fps, t0, beat_s, beats_per_bar, nbars, bar0_idx_beats, step_frac=0.25):
    steps = beats_per_bar * 4
    acc = np.zeros(steps)
    cnt = np.zeros(steps)
    for b in range(nbars):
        for s in range(steps):
            tt = t0 + (bar0_idx_beats + b * beats_per_bar) * beat_s + s * beat_s * step_frac
            i = int(round(tt * fps))
            if i < 1 or i >= len(flux) - 1:
                continue
            acc[s] += flux[max(i - 1, 0): i + 2].max()
            cnt[s] += 1
    m = acc / np.maximum(cnt, 1)
    return m


def to_pattern(m, steps=16):
    if m.max() <= 1e-6:
        return "." * steps
    z = m / (m.max() + 1e-9)
    # take only first `steps` positions (first bar of the meter), or fold longer meters
    out = ""
    for v in z[:steps]:
        out += "X" if v >= 0.8 else "x" if v >= 0.5 else "o" if v >= 0.27 else "."
    return out.ljust(steps, ".")


def analyze(path, max_s=300.0, start=0.0, engine="auto", stems=None, quiet=False, bpm_range=None):
    log = (lambda *a: None) if quiet else (lambda *a: print(*a, file=sys.stderr))
    st = decode(path, SR, start, max_s, 2)
    if len(st) < SR * 3:
        raise SystemExit("audio shorter than 3 seconds, nothing to analyze")
    mono = st.mean(axis=1)
    dur = len(mono) / SR
    prof = dict(schema="audio-forge/profile@1", file=os.path.basename(path), analyzed_seconds=round(dur, 2), start=start)
    log(f"decoded {dur:.1f}s")

    # loudness / dynamics / stereo
    prof["loudness"] = loudness(path, max_s)
    rms = np.sqrt(np.mean(mono ** 2)) + 1e-12
    pk = np.abs(mono).max()
    blk = SR // 2
    short = np.array([np.sqrt(np.mean(mono[i:i + blk] ** 2)) for i in range(0, len(mono) - blk, blk)]) + 1e-12
    sdb = 20 * np.log10(short)
    prof["dynamics"] = dict(rms_db=round(float(20 * np.log10(rms)), 2), peak_db=round(float(20 * np.log10(pk + 1e-12)), 2),
                            crest_db=round(float(20 * np.log10(pk / rms)), 2),
                            range_db=round(float(np.percentile(sdb, 95) - np.percentile(sdb, 10)), 2))
    mid, side = st.mean(axis=1), (st[:, 0] - st[:, 1]) / 2
    corr = float(np.corrcoef(st[:, 0], st[:, 1])[0, 1]) if st[:, 0].std() > 0 and st[:, 1].std() > 0 else 1.0
    prof["stereo"] = dict(side_to_mid_db=round(float(10 * np.log10((side ** 2).mean() / ((mid ** 2).mean() + 1e-12) + 1e-9)), 2),
                          lr_correlation=round(corr, 3))

    # onset envelopes, tempo, beats
    env, ft, f, S = onset_envelopes(mono)
    fps = SR / 256.0
    cands = estimate_tempo(env["all"], fps)
    bpm0 = cands[0]["bpm"]
    op_all = len(signal.find_peaks(env["all"], height=0.25, distance=int(0.04 * fps))[0]) / dur
    adjusted = None
    alt_pool = [c["bpm"] for c in cands]
    if bpm_range:  # the user knows the tempo octave: pick the candidate (or its double/half) inside the range
        lo_, hi_ = bpm_range
        for c in [bpm0, bpm0 * 2, bpm0 / 2, bpm0 * 4, bpm0 / 4]:
            if lo_ <= c <= hi_:
                adjusted = "bpm_range" if abs(c - bpm0) > 0.5 else None
                bpm0 = c
                break
    elif bpm0 <= 92 and 2.6 < op_all * 60.0 / bpm0 <= 4.5 and any(abs(c - 2 * bpm0) / (2 * bpm0) < 0.03 for c in alt_pool):
        bpm0, adjusted = bpm0 * 2, "doubled: onsets per beat too dense for the slower grid"
    if engine in ("auto", "librosa"):
        try:
            import librosa  # optional cross-check
            tl, _ = librosa.beat.beat_track(y=mono.astype(np.float32), sr=SR)
            prof["librosa_tempo"] = round(float(np.atleast_1d(tl)[0]), 2)
        except Exception:
            pass
    bpm, t0, fit = grid_fit(env["all"], fps, bpm0)
    steady = fit > 2.2
    beat_s = 60.0 / bpm
    if steady:
        beats = np.arange(t0, dur, beat_s)
    else:
        beats = dp_beats(env["all"], fps, bpm0)
        if len(beats) > 4:
            bpm = round(60.0 / float(np.median(np.diff(beats))), 2)
            beat_s = 60.0 / bpm
    alt = [round(bpm * 2, 1), round(bpm / 2, 1)]
    prof["tempo"] = dict(bpm=round(float(bpm), 2), candidates=cands, grid_fit=round(float(fit), 2), steady=bool(steady),
                         first_beat=round(float(beats[0]), 3) if len(beats) else None, octave_adjusted=adjusted,
                         alt_octaves=alt, ambiguous=any(abs(c["bpm"] - a_) / a_ < 0.03 for c in cands for a_ in alt),
                         note="half/double-time feel is common (dnb, trap, dubstep, metal). If ambiguous, ask which tempo feels right, "
                              "then re-run with --bpm-range lo hi")
    log(f"tempo {bpm:.2f} bpm (steady={steady}, fit={fit:.2f})")
    lowhigh = env["low"] * 1.0 + env["all"] * 0.6
    bpb, ph, conf = estimate_meter(lowhigh, fps, beats)
    downs = beats[ph::bpb]
    prof["meter"] = dict(beats_per_bar=bpb, downbeat_phase=ph, confidence=conf)
    prof["beats"] = [round(float(b), 3) for b in beats]
    prof["downbeats"] = [round(float(b), 3) for b in downs]

    # key / chords
    kseg = mono[: int(min(dur, 180) * SR)]
    C, ct = chroma(kseg)
    keys, v = estimate_key(C)
    kb = keys[0]
    ki = NOTE.index(kb["key"])
    rel = NOTE[(ki + 9) % 12] + " minor" if kb["mode"] == "major" else NOTE[(ki + 3) % 12] + " major"
    prof["key"] = dict(best=keys[0], relative=rel, alternatives=keys[1:],
                       note="major/minor & modes share notes; the relative key is equally likely. Modal tunes (dorian/phrygian) report as their parent key.",
                       chroma=[round(float(x), 3) for x in v / (v.max() + 1e-9)])
    log(f"key {keys[0]['key']} {keys[0]['mode']}")
    Cfull, ctf = chroma(mono, hop=2048)
    bar_chords = []
    for i in range(len(downs) - 1):
        m = (ctf >= downs[i]) & (ctf < downs[i + 1])
        if m.sum() == 0:
            continue
        lab, sc = chord_label(Cfull[:, m].mean(axis=1))
        bar_chords.append(dict(bar=i, t=round(float(downs[i]), 3), chord=lab, score=round(sc, 3)))
    prof["chords_per_bar"] = bar_chords

    # drum / groove pattern (from stems if available)
    drum_env = env
    if stems and os.path.exists(os.path.join(stems, "drums.wav")):
        d = decode(os.path.join(stems, "drums.wav"), SR, start, max_s, 1)
        drum_env, _, _, _ = onset_envelopes(d)
        prof["drum_source"] = "demucs stem"
    else:
        prof["drum_source"] = "full mix (approximate)"
    nb = max(len(downs) - 2, 0)
    bar0 = ph
    pat = {}
    for nm in ("low", "snare", "high"):
        m = pattern_from_flux(drum_env[nm], fps, beats[0] if len(beats) else 0.0, beat_s, bpb, nb, bar0)
        pat[{"low": "kick", "snare": "snare", "high": "hat"}[nm]] = to_pattern(m, bpb * 4)
    prof["pattern"] = pat
    prof["kick_four_on_floor"] = all(pat["kick"][i] in "xX" for i in (0, 4, 8, 12)) if bpb == 4 else False
    # swing: where the off-beat 8th really sits between beats
    fr = []
    for b in beats[:-1]:
        a, c = int((b + 0.3 * beat_s) * fps), int((b + 0.75 * beat_s) * fps)
        if c > a and c < len(env["high"]):
            seg = env["all"][a:c]
            if seg.max() > 0.3:
                fr.append((a + int(np.argmax(seg))) / fps - b)
    sw = 0.0
    if len(fr) > 8:
        sw = float(np.clip(2 * (np.median(fr) / beat_s - 0.5), 0, 0.6))
    prof["swing"] = round(sw, 3)
    prof["onsets_per_sec"] = round(float(len(signal.find_peaks(env["all"], height=0.25, distance=int(0.04 * fps))[0]) / dur), 2)

    # spectrum
    Fm = S.mean(axis=1) ** 2
    tot = Fm.sum() + 1e-12
    edges = [("sub", 20, 60), ("bass", 60, 250), ("low_mid", 250, 500), ("mid", 500, 2000), ("high_mid", 2000, 6000), ("air", 6000, 11000)]
    prof["bands_db"] = {n: round(float(10 * np.log10(Fm[(f >= lo) & (f < hi)].sum() / tot + 1e-12)), 1) for n, lo, hi in edges}
    cen = (f[:, None] * S).sum(axis=0) / (S.sum(axis=0) + 1e-9)
    prof["spectral"] = dict(centroid_hz=round(float(np.average(cen, weights=S.sum(axis=0) + 1e-9)), 1),
                            rolloff85_hz=round(float(f[np.searchsorted(np.cumsum(Fm) / tot, 0.85)]), 1),
                            flatness=round(float(np.exp(np.mean(np.log(S.mean(axis=1) + 1e-9))) / (S.mean() + 1e-9)), 4))
    # harmonic / percussive
    Sm = S[: int(5000 / (SR / 1024))]
    H = median_filter(Sm, size=(1, 17))
    P = median_filter(Sm, size=(17, 1))
    prof["harmonic_ratio"] = round(float((H ** 2).sum() / ((H ** 2).sum() + (P ** 2).sum() + 1e-12)), 3)

    # structure: per-bar features
    nbar = len(downs) - 1
    energy_beats = []
    if nbar >= 8:
        feats, tt = [], []
        for i in range(nbar):
            a, b = int(downs[i] * SR), int(downs[i + 1] * SR)
            seg = mono[a:b]
            if len(seg) < 100:
                continue
            fa, fb = int(downs[i] * fps), max(int(downs[i + 1] * fps), int(downs[i] * fps) + 1)
            spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
            fr_ = np.fft.rfftfreq(len(seg), 1 / SR)
            feats.append([20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9),
                          float((fr_ * spec).sum() / (spec.sum() + 1e-9)) / 1000,
                          float(10 * np.log10(spec[fr_ < 200].sum() / (spec.sum() + 1e-9) + 1e-9)),
                          float(env["all"][fa:fb].mean())])
            tt.append(i)
        F = np.array(feats)
        bounds, nov = novelty_boundaries(F)
        idx = [0] + bounds + [len(F)]
        raw = []
        for a, b in zip(idx[:-1], idx[1:]):
            if b > a:
                raw.append((a, b, float(F[a:b, 0].mean()), float(F[a:b, 3].mean())))
        e = np.array([r[2] for r in raw])
        en = (e - e.min()) / (e.max() - e.min() + 1e-9)
        secs = []
        for k, ((a, b, _, od), ev) in enumerate(zip(raw, en)):
            if ev >= 0.72:
                lab = "drop"
            elif k == 0 and ev < 0.6:
                lab = "intro"
            elif k == len(raw) - 1 and ev < 0.6:
                lab = "outro"
            elif ev < 0.4:
                lab = "break"
            elif k + 1 < len(raw) and en[k + 1] > ev + 0.2:
                lab = "build"
            else:
                lab = "verse"
            secs.append(dict(label=lab, start_bar=int(a), bars=int(b - a), start=round(float(downs[a]), 3),
                             end=round(float(downs[min(b, len(downs) - 1)]), 3), energy=round(float(ev), 2)))
        prof["sections"] = secs
        prof["drops"] = [s["start"] for k, s in enumerate(secs) if s["label"] == "drop" and (k == 0 or secs[k - 1]["label"] != "drop")]
        # per-beat energy curve for the editor
        for bt in beats:
            a, b = int(bt * SR), int((bt + beat_s) * SR)
            seg = mono[a:b]
            energy_beats.append(float(np.sqrt(np.mean(seg ** 2))) if len(seg) > 50 else 0.0)
        ebm = np.array(energy_beats)
        prof["energy_per_beat"] = [round(float(x), 3) for x in ebm / (ebm.max() + 1e-9)]
    else:
        prof["sections"], prof["drops"] = [], []

    prof["genre_guess"] = guess_genre(prof)
    prof["summary"] = summarize(prof)
    return prof


def guess_genre(p):
    from importlib import import_module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    G = import_module("forge.genres").GENRES
    bpm = p["tempo"]["bpm"]
    mode = p["key"]["best"]["mode"]
    kick = p["pattern"]["kick"]
    cen = p["spectral"]["centroid_hz"]
    fl = p["spectral"]["flatness"]
    op = p["onsets_per_sec"]
    scores = {}
    for g, s in G.items():
        sc, why = 0.0, []
        lo, hi = s["bpm"]
        cand = [bpm, bpm * 2, bpm / 2]
        d = min(0 if lo - 5 <= c <= hi + 5 else min(abs(c - lo), abs(c - hi)) / 20.0 for c in cand)
        direct = lo - 5 <= bpm <= hi + 5
        sc += 2.5 * (1 if direct else 0.55 if d == 0 else max(0, 1 - d))
        if direct:
            why.append("tempo in range")
        smode = "major" if s["scales"][0] in ("major", "pent_major", "lydian", "mixolydian") else "minor"
        if smode == mode:
            sc += 0.8
        if g in ("house", "techno", "edm") and p.get("kick_four_on_floor"):
            sc += 1.6; why.append("four-on-the-floor")
        if g in ("lofi", "boombap", "jazz") and p["swing"] > 0.12:
            sc += 1.2; why.append("swung")
        if g in ("dark_ambient", "cinematic") and op < 2.0:
            sc += 1.4; why.append("sparse onsets")
        if g in ("chiptune",) and cen > 2500 and fl > 0.02:
            sc += 0.6
        if g in ("metal", "rock", "horror_chase", "techno", "dubstep") and p["bands_db"]["high_mid"] > -18:
            sc += 0.5
        if g in ("lofi", "dark_ambient") and cen < 1800:
            sc += 0.8; why.append("dark/soft spectrum")
        if g in ("metal", "dnb", "horror_chase") and op > 6:
            sc += 0.8; why.append("busy")
        def sim(a, b):
            a = [c in "xX" for c in a.ljust(16, ".")[:16]]
            b = [c in "xX" for c in b.ljust(16, ".")[:16]]
            tp = sum(1 for u, v in zip(a, b) if u and v)
            return tp / max(sum(a), sum(b), 1)
        d = s.get("drums", {})
        if d.get("kick") is not None and p["meter"]["beats_per_bar"] == 4:
            sk = sim(p["pattern"]["kick"], d["kick"])
            ss = sim(p["pattern"]["snare"], d.get("snare") or d.get("clap") or "")
            sc += 2.2 * sk + 1.2 * ss
            if sk > 0.7:
                why.append("kick pattern matches")
        scores[g] = (sc, why)
    top = sorted(scores.items(), key=lambda kv: -kv[1][0])[:3]
    return [dict(genre=g, score=round(s, 2), reasons=w) for g, (s, w) in top] + [dict(note="heuristic; confirm by ear / ask the user")]


def summarize(p):
    k = p["key"]["best"]
    t = p["tempo"]
    g = p["genre_guess"][0]["genre"]
    return (f"{t['bpm']:.0f} BPM ({'steady' if t['steady'] else 'drifting'}), {p['meter']['beats_per_bar']}/4, {k['key']} {k['mode']}, "
            f"~{g}-like, {p['loudness'].get('lufs')} LUFS, swing {p['swing']}, kick {p['pattern']['kick']}, "
            f"{len(p['sections'])} sections, drops at {p['drops'][:4]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-seconds", type=float, default=300)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--engine", default="auto", choices=["auto", "builtin", "librosa"])
    ap.add_argument("--stems", help="demucs output dir (drums.wav bass.wav other.wav vocals.wav)")
    ap.add_argument("--bpm-range", nargs=2, type=float, metavar=("LO", "HI"), help="force the tempo octave, e.g. 150 190")
    ap.add_argument("--brief", action="store_true", help="print only the summary line")
    a = ap.parse_args()
    rng = tuple(a.bpm_range) if a.bpm_range else None
    hint = None
    bmf = a.audio + ".beatmap.json"
    if rng is None and os.path.exists(bmf):  # audio-forge wrote this file: its tempo is known, use it to pick the right octave
        try:
            hint = float(json.load(open(bmf))["bpm"])
            rng = (hint * 0.93, hint * 1.07)
        except Exception:
            hint = None
    p = analyze(a.audio, a.max_seconds, a.start, a.engine, a.stems, bpm_range=rng)
    if hint:
        p["tempo"]["source"] = f"octave chosen from {os.path.basename(bmf)} (declared {hint} BPM); beat grid still measured from the audio"
        p["tempo"]["declared_bpm"] = hint
    out = a.out or os.path.splitext(a.audio)[0] + ".profile.json"
    json.dump(p, open(out, "w"), indent=1)
    print(p["summary"] if a.brief else json.dumps({k: v for k, v in p.items() if k not in ("beats", "downbeats", "energy_per_beat", "chords_per_bar")}, indent=1))
    print(f"\nprofile written -> {out}", file=sys.stderr)


if __name__ == "__main__":
    main()

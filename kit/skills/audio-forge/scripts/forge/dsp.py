"""dsp.py -- oscillators, envelopes, filters and effects. Pure numpy + scipy.
Mono is shape (n,), stereo is (n, 2). Everything is float64 in roughly [-1, 1].

V2 additions (2026-11-19): 2x-oversampled resonant SVF (scalar or per-sample cutoff),
Karplus-Strong strings, ping-pong delay, fast multi-tap hall reverb, asymmetric tube
drive, guitar cabinet, stereo high-pass, glide/vibrato-aware oscillators and
additive synthesis with Nyquist-safe harmonic clipping.
"""
import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d

SR = 44100
TAU = 2 * np.pi
NYQ = SR * 0.44              # never synthesise a partial at/above this (keeps aliases out)


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def db(x):
    return 10.0 ** (x / 20.0)


def nyquist_ok(freq, sr=SR):
    return np.asarray(freq) < sr * 0.44


# ── oscillators ─────────────────────────────────────────────────────────────
def _phase(freq, n, sr=SR, phase0=0.0):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return (phase0 + np.cumsum(f / sr)) % 1.0, f / sr


def _polyblep(t, dt):
    y = np.zeros_like(t)
    m = t < dt
    x = t[m] / dt[m]
    y[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    x = (t[m] - 1.0) / dt[m]
    y[m] = x * x + x + x + 1.0
    return y


def _shape_freq(freq, n, sr, vib_delay_s=0.0, vib_rate=5.5, vib_depth=0.0,
                glide_from=None, glide_s=0.0):
    """Broadcast a frequency, then apply an optional portamento glide and a
    delayed vibrato (starts after vib_delay_s and fades in over ~90 ms)."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,)).astype(float).copy()
    if glide_from is not None and glide_s > 0:
        t = np.arange(n) / sr
        u = np.clip(t / glide_s, 0.0, 1.0)
        u = u * u * (3.0 - 2.0 * u)                    # smoothstep, no zipper
        f = float(glide_from) + (f - float(glide_from)) * u
    if vib_depth:
        t = np.arange(n) / sr
        ramp = np.clip((t - vib_delay_s) / 0.09, 0.0, 1.0) if vib_delay_s > 0 else 1.0
        f = f * 2.0 ** (vib_depth * ramp * np.sin(TAU * vib_rate * t) / 12.0)
    return f


def osc(kind, freq, n, sr=SR, phase0=0.0, pw=0.5, vib_delay_s=0.0, vib_rate=5.5,
        vib_depth=0.0, glide_from=None, glide_s=0.0):
    """kind: sine saw square pulse tri noise. freq: scalar or per-sample array (Hz).
    V2: delayed vibrato, smooth portamento and a hard Nyquist clamp."""
    if kind == "noise":
        return np.random.uniform(-1, 1, n)
    f = _shape_freq(freq, n, sr, vib_delay_s, vib_rate, vib_depth, glide_from, glide_s)
    f = np.clip(f, 0.01, sr * 0.49)
    t, dt = _phase(f, n, sr, phase0)
    dt = np.clip(dt, 1e-6, 0.49)
    if kind == "sine":
        return np.sin(TAU * t)
    if kind == "saw":
        return 2.0 * t - 1.0 - _polyblep(t, dt)
    if kind in ("square", "pulse"):
        w = 0.5 if kind == "square" else pw
        return np.where(t < w, 1.0, -1.0) + _polyblep(t, dt) - _polyblep((t - w) % 1.0, dt)
    if kind == "tri":
        return 2.0 * np.abs(2.0 * t - 1.0) - 1.0
    raise ValueError(kind)


def supersaw(freq, n, voices=7, detune=0.15, sr=SR, kind="saw", vib_delay_s=0.0,
             vib_rate=5.5, vib_depth=0.0, glide_from=None, glide_s=0.0):
    """detune = spread in semitones across the voices. Voices above Nyquist are skipped."""
    f0 = _shape_freq(freq, n, sr, vib_delay_s, vib_rate, vib_depth, glide_from, glide_s)
    out = np.zeros(n)
    offs = np.linspace(-detune, detune, voices) if voices > 1 else [0.0]
    used = 0
    for i, o in enumerate(offs):
        fv = f0 * 2 ** (o / 12.0)
        if float(np.max(fv)) >= sr * 0.44:
            continue
        out += osc(kind, fv, n, sr, phase0=(i * 0.173) % 1)
        used += 1
    return out / max(used, 1)


def additive(freq, n, partials, sr=SR, phase0=0.0, detune_cents=0.0):
    """Sum sine partials, skipping any partial at/above sr*0.44.
    partials: iterable of (harmonic, amplitude, decay_tau_s or None)."""
    t = np.arange(n) / sr
    y = np.zeros(n)
    f = float(freq)
    offsets = (0.0,) if detune_cents == 0 else (-detune_cents, 0.0, detune_cents)
    for item in partials:
        k, amp = item[0], item[1]
        tau = item[2] if len(item) > 2 else None
        for d in offsets:
            fk = f * k * 2 ** (d / 1200.0)
            if fk >= sr * 0.44:
                continue
            ph = np.sin(TAU * fk * t + phase0 * k)
            if tau:
                ph *= np.exp(-t / max(tau, 1e-4))
            y += amp * ph
    return y / max(1.0, sum(abs(p[1]) for p in partials) * 0.55)


def fm(freq, n, ratio=2.0, index=3.0, index_env=None, sr=SR):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    idx = index * (index_env if index_env is not None else 1.0)
    mod = np.sin(TAU * np.cumsum(f * ratio / sr))
    return np.sin(TAU * np.cumsum(f / sr) + idx * mod)


# ── envelopes ───────────────────────────────────────────────────────────────
def adsr(n, a=0.005, d=0.1, s=0.7, r=0.1, sr=SR, curve=2.0):
    """n = total samples including the release tail (last r seconds)."""
    a_n, d_n, r_n = int(a * sr), int(d * sr), int(r * sr)
    r_n = min(r_n, n // 2)
    hold = max(n - r_n, 0)
    env = np.zeros(n)
    a_n = min(a_n, hold)
    d_n = min(d_n, max(hold - a_n, 0))
    if a_n:
        env[:a_n] = np.linspace(0, 1, a_n, endpoint=False) ** 1.5
    if d_n:
        env[a_n:a_n + d_n] = s + (1 - s) * (1 - np.linspace(0, 1, d_n, endpoint=False)) ** curve
    env[a_n + d_n:hold] = s
    if r_n:
        env[hold:hold + r_n] = s * (1 - np.linspace(0, 1, r_n)) ** 1.5
    return env


def decay(n, tau, sr=SR):
    return np.exp(-np.arange(n) / (tau * sr))


def fade(x, fin=0.003, fout=0.01, sr=SR):
    n = len(x)
    a, b = min(int(fin * sr), n), min(int(fout * sr), n)
    x = x.copy()
    sh = (slice(None),) + (None,) * (x.ndim - 1)
    if a:
        x[:a] *= np.linspace(0, 1, a)[sh]
    if b:
        x[n - b:] *= np.linspace(1, 0, b)[sh]
    return x


# ── filters ─────────────────────────────────────────────────────────────────
def _sos(kind, cutoff, sr, order=2):
    cutoff = float(np.clip(cutoff, 20, sr * 0.45))
    return signal.butter(order, cutoff, btype=kind, fs=sr, output="sos")


def lp(x, cutoff, sr=SR, order=2):
    return signal.sosfilt(_sos("low", cutoff, sr, order), x, axis=0)


def hp(x, cutoff, sr=SR, order=2):
    return signal.sosfilt(_sos("high", cutoff, sr, order), x, axis=0)


def bp(x, lo, hi, sr=SR, order=2):
    lo = float(np.clip(lo, 20, sr * 0.44))
    hi = float(np.clip(hi, lo * 1.05, sr * 0.45))
    return signal.sosfilt(signal.butter(order, [lo, hi], btype="band", fs=sr, output="sos"), x, axis=0)


def sweep_lp(x, cutoff_env, sr=SR, block=256, order=2):
    """low-pass whose cutoff follows cutoff_env (per-sample, Hz). Block-wise, filter state carried."""
    n = len(x)
    out = np.zeros(n)
    zi = None
    for i in range(0, n, block):
        sos = _sos("low", float(np.mean(cutoff_env[i:i + block])), sr, order)
        if zi is None:
            zi = signal.sosfilt_zi(sos) * x[i]
        seg, zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
        out[i:i + block] = seg
    return out


def _biquad(kind, fc, q, sr):
    """RBJ biquad coefficients (normalised). kind: low high band."""
    fc = float(np.clip(fc, 10.0, sr * 0.45))
    w0 = TAU * fc / sr
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * max(q, 0.05))
    if kind == "low":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "high":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "band":
        b = [alpha, 0.0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    else:
        raise ValueError(kind)
    b = np.asarray(b, float) / a[0]
    a = np.asarray(a, float) / a[0]
    return b, a


def _svf(x, cutoff, q, mode, sr=SR, os=2, block=64):
    """2x-oversampled resonant state-variable filter. cutoff may be scalar or per-sample.
    Implemented as a state-carrying biquad per block at 2x rate, so a per-sample cutoff
    array is honoured to within one 32-sample block while staying fast in numpy."""
    x = np.asarray(x, dtype=float)
    scalar = np.isscalar(cutoff) or (isinstance(cutoff, np.ndarray) and cutoff.ndim == 0)
    n = len(x)
    if n == 0:
        return x.copy()
    if scalar:
        c = float(cutoff)
        if c >= sr * 0.44 and mode == "low":
            return x.copy()
        xu = signal.resample_poly(x, os, 1) if os > 1 else x
        b, a = _biquad(mode, c, q, sr * os)
        y = signal.lfilter(b, a, xu)
        if hasattr(y, "ndim") and y.ndim == 2:
            y = y[::os] if os > 1 else y
        else:
            y = y[::os] if os > 1 else y
        return y[:n]
    cu = np.asarray(cutoff, float).reshape(-1)
    if len(cu) == 1:
        return _svf(x, float(cu[0]), q, mode, sr, os, block)
    tgt = np.linspace(0, 1, n)
    src = np.linspace(0, 1, len(cu))
    cb = np.interp(tgt, src, cu)
    xu = signal.resample_poly(x, os, 1) if os > 1 else x
    cb2 = np.interp(np.arange(len(xu)) / max(len(xu) - 1, 1), tgt, cb)
    y = np.empty_like(xu)
    zi = np.zeros(2, dtype=float)
    for i in range(0, len(xu), block):
        seg = xu[i:i + block]
        c = float(np.mean(cb2[i:i + block]))
        b, a = _biquad(mode, c, q, sr * os)
        if i == 0:
            try:
                zi = signal.lfilter_zi(b, a) * seg[0]
            except Exception:
                zi = np.zeros(2)
        out, zi = signal.lfilter(b, a, seg, zi=zi)
        y[i:i + block] = out
    return y[::os][:n]


def svf_lp(x, cutoff, q=0.707, sr=SR, os=2, block=64):
    """2x-oversampled resonant low-pass. cutoff: scalar or per-sample array."""
    return _svf(x, cutoff, q, "low", sr, os, block)


def svf_bp(x, cutoff, q=1.2, sr=SR, os=2, block=64):
    """2x-oversampled resonant band-pass (constant peak gain)."""
    return _svf(x, cutoff, q, "band", sr, os, block)


def svf_hp(x, cutoff, q=0.707, sr=SR, os=2, block=64):
    """2x-oversampled resonant high-pass."""
    return _svf(x, cutoff, q, "high", sr, os, block)


def peak_eq(x, f0, gain_db, q=1.0, sr=SR):
    A = 10 ** (gain_db / 40.0)
    w0 = TAU * f0 / sr
    al = np.sin(w0) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w0), 1 - al * A])
    a = np.array([1 + al / A, -2 * np.cos(w0), 1 - al / A])
    return signal.lfilter(b / a[0], a / a[0], x, axis=0)


def formant(x, formants, sr=SR):
    """parallel band-pass bank, formants = [(freq, bandwidth, gain), ...]"""
    out = np.zeros(len(x))
    for f, bw, g in formants:
        out += g * bp(x, max(f - bw / 2, 30), f + bw / 2, sr)
    return out


def hpf_stereo(stereo, cutoff=150.0, sr=SR):
    """High-pass both channels (2nd order). Mono input is duplicated."""
    x = np.asarray(stereo, dtype=float)
    if x.ndim == 1:
        x = np.column_stack([x, x])
    out = np.empty_like(x)
    for ch in range(2):
        out[:, ch] = hp(x[:, ch], cutoff, sr, 2)
    return out


def cab_filter(stereo, sr=SR, hp_hz=130.0, lp_hz=4000.0):
    """Guitar cabinet: ~130 Hz high-pass + ~4 kHz low-pass, one pass per channel."""
    x = np.asarray(stereo, dtype=float)
    if x.ndim == 1:
        x = np.column_stack([x, x])
    out = np.empty_like(x)
    sos_h = _sos("high", hp_hz, sr, 2)
    sos_l = _sos("low", lp_hz, sr, 2)
    for ch in range(2):
        y = signal.sosfilt(sos_h, x[:, ch])
        out[:, ch] = signal.sosfilt(sos_l, y)
    return out


def asym_drive(x, drive=6.0, bias=0.15):
    """Asymmetric tube/amp overdrive: more even harmonics, then DC removed."""
    y = np.tanh(np.asarray(x, float) * drive + bias) - np.tanh(bias)
    y = y / max(np.tanh(drive + bias) - np.tanh(bias), 1e-6)
    return y - np.mean(y)


def mono_below(stereo, cutoff=140.0, sr=SR):
    """Collapse everything below `cutoff` to mono (keeps the low end solid).

    Done in the frequency domain with a smooth 8th-order shelf weight, so the low
    band really is identical in both channels (an IIR high/low split leaks side
    energy around the corner and leaves the bass partly stereo).
    """
    x = np.asarray(stereo, dtype=float)
    if x.ndim == 1:
        return x
    n = len(x)
    if n < 32:
        return x
    L = np.fft.rfft(x[:, 0]); R = np.fft.rfft(x[:, 1])
    f = np.fft.rfftfreq(n, 1.0 / sr)
    c = max(float(cutoff), 1e-3)
    lo, hi = c * 0.90, c * 1.10                                # keep everything under 0.9*cutoff exactly mono
    w = np.ones_like(f); mid = (f > lo) & (f < hi)
    w[mid] = 0.5 * (1.0 + np.cos(np.pi * (f[mid] - lo) / (hi - lo)))
    w[f >= hi] = 0.0
    m = 0.5 * (L + R)
    L2 = m * w + L * (1.0 - w)
    R2 = m * w + R * (1.0 - w)
    return np.column_stack([np.fft.irfft(L2, n), np.fft.irfft(R2, n)])


# ── physical / plucked strings ──────────────────────────────────────────────
def ks_string(freq, n, damp=0.996, bright=0.65, sr=SR):
    """Karplus-Strong plucked string (no samples).

    A filtered noise burst fills one delay period; the loop then averages the
    current and previous period taps with `damp` loss and `bright` tilt.
    Vectorised per period, so it is fast even for long notes.
    """
    n = int(max(n, 2))
    f = max(float(freq), 20.0)
    D = max(2, int(round(sr / f)))
    rng = np.random.RandomState(int(f * 7) % 9973 + 11)
    exc = rng.uniform(-1, 1, D)
    # darken the excitation: two passes of a 3-tap average, then normalise
    exc = np.convolve(exc, np.array([0.25, 0.5, 0.25]), mode="same")
    exc = np.convolve(exc, np.array([0.25, 0.5, 0.25]), mode="same")
    exc /= (np.max(np.abs(exc)) + 1e-9)
    y = np.zeros(n)
    m0 = min(D, n)
    y[:m0] = exc[:m0]
    bright = float(np.clip(bright, 0.0, 1.0))
    damp = float(np.clip(damp, 0.80, 0.99999))
    i = D
    while i < n:
        m = min(D, n - i)
        cur = y[i - D:i - D + m]
        prev = np.empty(m)
        prev[0] = y[i - D - 1] if i - D - 1 >= 0 else 0.0
        if m > 1:
            prev[1:] = y[i - D:i - D + m - 1]
        y[i:i + m] = damp * (bright * cur + (1.0 - bright) * prev)
        i += D
    # tiny pick transient and DC block
    pick = rng.randn(min(int(0.004 * sr), n)) * np.exp(-np.arange(min(int(0.004 * sr), n)) / (0.0012 * sr))
    y[:len(pick)] += 0.10 * pick
    y -= np.mean(y)
    return y


# ── delays and reverbs ──────────────────────────────────────────────────────
def ping_pong_delay(x, time_s=0.375, feedback=0.35, mix=0.3, sr=SR, tone=6000, taps=6):
    """Stereo ping-pong echo: taps alternate left/right, each darker and quieter."""
    xs = x if x.ndim == 2 else np.column_stack([x, x])
    n = len(xs)
    d = max(1, int(time_s * sr))
    wetL = np.zeros(n)
    wetR = np.zeros(n)
    for k in range(1, taps + 1):
        off = d * k
        if off >= n:
            break
        g = feedback ** (k - 1)
        src = xs[:n - off]
        if k % 2:
            wetR[off:] += src[:, 1] * g
        else:
            wetL[off:] += src[:, 0] * g
    wetL = lp(wetL, tone, sr, 1)
    wetR = lp(wetR, tone, sr, 1)
    wet = np.column_stack([wetL, wetR])
    return xs * (1.0 - 0.45 * mix) + wet * mix


def hall_reverb(x, mix=0.25, rt60=2.2, sr=SR, predelay=0.02, damp=6000, width=1.0, taps=10):
    """Fast vectorised multi-tap hall: prime-number taps, exponential decay,
    alternating pan, one low-pass on the wet sum. No FFT convolution needed."""
    xs = x if x.ndim == 2 else np.column_stack([x, x])
    n = len(xs)
    if mix <= 0 or n == 0:
        return xs.copy()
    wet = np.zeros((n, 2))
    primes = [29, 37, 43, 53, 67, 83, 101, 127, 151, 181, 223, 271, 331]
    base = max(rt60, 0.25) / 2.0
    pd = int(predelay * sr)
    for i in range(min(taps, len(primes))):
        d = int(base * primes[i] / 29.0 * sr / 1000.0)
        start = pd + d
        if d <= 0 or start >= n:
            continue
        g = 10 ** (-3.0 * (d / sr) / max(rt60, 0.2))
        src = xs[:n - start]
        tgt = i % 2
        wet[start:, tgt] += src[:, tgt] * g
        wet[start:, 1 - tgt] += src[:, 1 - tgt] * g * 0.35
    wet[:, 0] = lp(wet[:, 0], damp, sr, 1)
    wet[:, 1] = lp(wet[:, 1], damp, sr, 1)
    if width < 1.0:
        m = wet.mean(axis=1, keepdims=True)
        wet = m + (wet - m) * width
    pk = np.max(np.abs(wet)) + 1e-9
    wet = wet / pk * (np.max(np.abs(xs)) + 1e-9)
    return xs * (1.0 - 0.5 * mix) + wet * mix


# ── effects ─────────────────────────────────────────────────────────────────
def distort(x, drive=3.0, mode="tanh"):
    if mode == "tanh":
        return np.tanh(x * drive) / np.tanh(drive)
    if mode == "fold":
        return np.sin(x * drive)
    if mode == "hard":
        return np.clip(x * drive, -1, 1)
    if mode == "asym":
        return asym_drive(x, drive)
    raise ValueError(mode)


def bitcrush(x, bits=8, hold=1):
    q = 2.0 ** (bits - 1)
    y = np.round(x * q) / q
    if hold > 1:
        y = np.repeat(y[::hold], hold, axis=0)[:len(x)]
    return y


def delay(x, time_s, feedback=0.35, mix=0.3, sr=SR, tone=6000, taps=6):
    d = int(time_s * sr)
    wet = np.zeros_like(x, dtype=float)
    for k in range(1, taps + 1):
        off = d * k
        if off >= len(x):
            break
        wet[off:] += x[:len(x) - off] * feedback ** (k - 1)
    wet = lp(wet, tone, sr, 1)
    return x * (1 - mix * 0.5) + wet * mix


_IR_CACHE = {}


def make_ir(rt60=1.6, sr=SR, predelay=0.012, damp=7000, seed=7, width=1.0):
    key = (round(rt60, 2), sr, round(predelay, 3), damp, seed, width)
    if key in _IR_CACHE:
        return _IR_CACHE[key]
    rng = np.random.RandomState(seed)
    n = int(rt60 * sr * 1.1)
    t = np.arange(n) / sr
    env = 10 ** (-3.0 * t / rt60)
    ir = np.zeros((n, 2))
    for c in range(2):
        noise = lp(rng.randn(n) * env, damp, sr, 1)
        tail = lp(noise, damp * 0.4, sr, 1)
        w = np.linspace(0, 1, n) ** 0.7
        ir[:, c] = noise * (1 - w) + tail * w
    if width < 1.0:
        m = ir.mean(axis=1, keepdims=True)
        ir = m + (ir - m) * width
    ir = np.vstack([np.zeros((int(predelay * sr), 2)), ir])
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    _IR_CACHE[key] = ir
    return ir


def reverb(x, mix=0.25, rt60=1.6, sr=SR, predelay=0.012, damp=7000, width=1.0):
    xs = x if x.ndim == 2 else np.stack([x, x], 1)
    if mix <= 0:
        return xs
    ir = make_ir(rt60, sr, predelay, damp, width=width)
    wet = np.stack([signal.fftconvolve(xs[:, c], ir[:, c])[:len(xs)] for c in range(2)], 1)
    return xs * (1 - mix * 0.6) + wet * mix * 3.0


def chorus(x, rate=0.6, depth=0.003, mix=0.5, sr=SR, base=0.012):
    n = len(x)
    d = (base + depth * np.sin(TAU * rate * np.arange(n) / sr)) * sr
    idx = np.clip(np.arange(n) - d, 0, n - 1)
    i0 = idx.astype(int)
    fr = idx - i0
    i1 = np.minimum(i0 + 1, n - 1)
    if x.ndim == 1:
        wet = x[i0] * (1 - fr) + x[i1] * fr
    else:
        wet = x[i0] * (1 - fr)[:, None] + x[i1] * fr[:, None]
    return x * (1 - mix * 0.5) + wet * mix


def stereo(x, pan=0.0):
    """equal-power pan, pan in [-1, 1]"""
    if x.ndim == 2:
        return x
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def widen(x, amount=0.012, sr=SR):
    xs = x if x.ndim == 2 else np.stack([x, x], 1)
    d = int(amount * sr)
    if d <= 0:
        return xs
    r = np.vstack([np.zeros((d, 2)), xs[:len(xs) - d]])
    return np.stack([xs[:, 0], r[:, 1] * 0.9 + xs[:, 1] * 0.1], 1)


def compress(x, thresh_db=-18, ratio=3.0, attack=0.005, release=0.08, makeup_db=0.0, sr=SR, block=64):
    xs = x if x.ndim == 2 else x[:, None]
    n = len(xs)
    env = np.abs(xs).max(axis=1)
    nb = (n + block - 1) // block
    e = np.pad(env, (0, nb * block - n)).reshape(nb, block).max(axis=1)
    over = np.maximum(20 * np.log10(e + 1e-9) - thresh_db, 0)
    gr = -over * (1 - 1 / ratio)
    a = np.exp(-block / (attack * sr + 1e-9))
    r = np.exp(-block / (release * sr + 1e-9))
    g = np.zeros(nb)
    cur = 0.0
    for i in range(nb):
        cur = (a * cur + (1 - a) * gr[i]) if gr[i] < cur else (r * cur + (1 - r) * gr[i])
        g[i] = cur
    gain = np.interp(np.arange(n), np.arange(nb) * block + block // 2, 10 ** ((g + makeup_db) / 20))
    y = xs * gain[:, None]
    return y if x.ndim == 2 else y[:, 0]


def sidechain_curve(n, hit_samples, depth=0.7, release=0.18, attack=0.004, sr=SR):
    """gain curve (n,) ducked at each hit (sample index) -- the pumping effect"""
    g = np.ones(n)
    a_n, r_n = max(int(attack * sr), 1), max(int(release * sr), 1)
    shape = np.concatenate([np.linspace(1, 1 - depth, a_n),
                            (1 - depth) + depth * (1 - np.exp(-np.linspace(0, 5, r_n)))])
    for h in hit_samples:
        h = int(h)
        if 0 <= h < n:
            seg = shape[:n - h]
            g[h:h + len(seg)] = np.minimum(g[h:h + len(seg)], seg)
    return g


def limiter(x, ceiling_db=-1.0, lookahead=0.004, release=0.08, sr=SR):
    ceil = db(ceiling_db)
    xs = x if x.ndim == 2 else x[:, None]
    n = len(xs)
    la = max(int(lookahead * sr), 1)
    pk = maximum_filter1d(np.abs(xs).max(axis=1), size=la * 2 + 1)
    need = np.minimum(1.0, ceil / (pk + 1e-9))
    need = uniform_filter1d(minimum_filter1d(need, size=la * 2 + 1), size=la + 1)
    k = np.exp(-1.0 / max(int(release * sr), 1))
    out = 1.0 - _release_follow(1.0 - need, k)
    y = np.clip(xs * np.minimum(out, need)[:, None], -ceil, ceil)
    return y if x.ndim == 2 else y[:, 0]


def _release_follow(red, k):
    """envelope follower: instant attack, exponential release (python loop over ~n/64 blocks)"""
    blk = 32
    n = len(red)
    nb = (n + blk - 1) // blk
    pk = np.pad(red, (0, nb * blk - n)).reshape(nb, blk).max(axis=1)
    kb = k ** blk
    env = np.zeros(nb)
    cur = 0.0
    for i in range(nb):
        cur = pk[i] if pk[i] > cur else cur * kb
        env[i] = cur
    full = np.interp(np.arange(n), np.arange(nb) * blk + blk / 2, env)
    return np.maximum(full, red)


def normalize(x, peak_db=-1.0):
    p = np.abs(x).max()
    return x if p < 1e-9 else x * (db(peak_db) / p)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-12)


def riser(dur, f0=200, f1=6000, sr=SR, noise=0.8):
    n = int(dur * sr)
    t = np.linspace(0, 1, n)
    nz = np.random.uniform(-1, 1, n)
    y = sweep_lp(nz, f0 * (f1 / f0) ** t, sr, order=2) * noise
    tone = np.sin(TAU * np.cumsum(f0 * 0.5 * (f1 / f0) ** t) / sr) * 0.15
    return (y + tone) * (t ** 2.0)


def downlifter(dur, sr=SR):
    return riser(dur, 200, 6000, sr)[::-1]

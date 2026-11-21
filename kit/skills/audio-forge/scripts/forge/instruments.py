"""instruments.py -- synthesised melodic voices. note(inst, midi, dur_s, vel) -> array (mono or stereo, incl. release tail).
Every instrument is built from oscillators/FM/filters/physical modelling; no samples.

V2 (2026-11-19): Karplus-Strong guitars, 3 pianos, 3 organs, 4 bells, 303 acid,
chip lead, pulsing/Y2K basses, formant sax, marimba, rave stab/shout, orchestral
hit, heartbeat, siren, clock tick. All old INSTRUMENTS keys still exist.
"""
import numpy as np
from . import dsp
from .dsp import SR, mtof, TAU

VOWELS = {  # formant (Hz, bandwidth, gain)
    "a": [(800, 90, 1.0), (1150, 110, 0.5), (2900, 140, 0.15)],
    "o": [(450, 80, 1.0), (800, 90, 0.4), (2830, 130, 0.1)],
    "u": [(325, 70, 1.0), (700, 80, 0.3), (2700, 120, 0.05)],
    "e": [(400, 70, 1.0), (1600, 100, 0.4), (2700, 120, 0.2)],
    "ha": [(700, 110, 1.0), (1220, 140, 0.7), (2600, 180, 0.25)],
}


def _tail(dur, r, sr=SR):
    return max(2, int((dur + r) * sr))


def _t(n, sr=SR):
    return np.arange(n) / sr


def _out(y, peak=0.80, sr=SR, fade_out=0.02):
    y = np.asarray(y, dtype=float)
    if y.ndim == 1:
        y = dsp.fade(y, 0.002, fade_out, sr)
    else:
        y = dsp.fade(y, 0.002, fade_out, sr)
    p = np.max(np.abs(y))
    return y * (peak / p) if p > 1e-9 else y


def render(inst, midi, dur, vel=0.8, sr=SR, **kw):
    f = float(mtof(midi))
    fn = INSTRUMENTS[inst]
    y = fn(f, dur, sr, **kw)
    return y * vel


# ── basses ──────────────────────────────────────────────────────────────────
def sine_sub(f, dur, sr, **kw):
    n = _tail(dur, 0.08)
    return _out(dsp.osc("sine", f, n, sr) * dsp.adsr(n, 0.004, 0.05, 0.95, 0.08, sr), 0.75)


def saw_bass(f, dur, sr, cutoff=700, drive=1.8, **kw):
    n = _tail(dur, 0.06)
    y = dsp.osc("saw", f, n, sr) * 0.7 + dsp.osc("square", f / 2, n, sr) * 0.4
    env = dsp.adsr(n, 0.003, 0.18, 0.55, 0.06, sr)
    cut = cutoff * (0.5 + 2.5 * np.exp(-np.arange(n) / (0.12 * sr)))
    y = dsp.svf_lp(y, cut, 1.4, sr)
    return _out(dsp.asym_drive(y, drive) * env, 0.76)


def reese(f, dur, sr, **kw):
    n = _tail(dur, 0.12)
    y = (dsp.osc("saw", f, n, sr) + dsp.osc("saw", f * 1.012, n, sr) +
         dsp.osc("saw", f * 0.988, n, sr)) / 3
    y = dsp.svf_lp(y, 900, 1.1, sr)
    y = dsp.asym_drive(y * 1.5, 2.5)
    return _out(y * dsp.adsr(n, 0.01, 0.1, 0.9, 0.12, sr), 0.78)


def sub_drop(f, dur, sr, **kw):
    n = _tail(dur, 0.1)
    t = _t(n, sr)
    fr = f * np.exp(-t * 1.5) + f * 0.4
    return _out(np.sin(TAU * np.cumsum(fr) / sr) * dsp.adsr(n, 0.005, 0.1, 0.9, 0.1, sr), 0.8)


def acid_303(f, dur, sr, accent=False, **kw):
    """TB-303: 45% sine sub + a saw through a resonant sweeping SVF, accent overdrive."""
    n = _tail(dur, 0.07)
    t = _t(n, sr)
    sub = np.sin(TAU * f * t)
    sawy = dsp.osc("saw", f, n, sr) * 0.8 + dsp.osc("square", f * 0.5, n, sr) * 0.2
    base, top = (4.0, 22.0) if accent else (2.8, 13.0)
    cut = f * (base + top * np.exp(-t / (0.075 if accent else 0.12)))
    cut = np.clip(cut, 60.0, sr * 0.42)
    y = dsp.svf_lp(sawy * 0.55 + sub * 0.45, cut, 4.0 if accent else 2.8, sr)
    y = dsp.asym_drive(y * (1.9 if accent else 1.15), 2.2 if accent else 1.3, 0.08)
    env = (1.0 - np.exp(-t * 900.0)) * np.exp(-t * (3.0 if accent else 4.5))
    return _out(y * env, 0.80)


def pulsing_bass(f, dur, sr, **kw):
    """Dark 16th-note bass: filtered saw+square with a fast amplitude pulse."""
    n = _tail(dur, 0.04)
    t = _t(n, sr)
    y = dsp.osc("saw", f, n, sr) * 0.65 + dsp.osc("square", f, n, sr, pw=0.35) * 0.35
    cut = f * (2.2 + 5.5 * np.exp(-t * 9.0))
    y = dsp.svf_lp(y, cut, 1.8, sr)
    pulse = 0.62 + 0.38 * np.cos(TAU * 8.0 * t) ** 2
    env = (1.0 - np.exp(-t * 700.0)) * np.exp(-t * 6.0)
    return _out(dsp.asym_drive(y, 1.6) * env * pulse, 0.78)


def y2k_bass(f, dur, sr, **kw):
    """Sub + rubbery filtered pluck: the bouncy late-90s jungle sub."""
    n = _tail(dur, 0.08)
    t = _t(n, sr)
    blip = 1.0 + 0.35 * np.exp(-t * 45.0)
    phase = np.cumsum(f * blip / sr)
    sub = np.sin(TAU * phase)
    ph = phase % 1.0
    sawp = 2.0 * ph - 1.0
    sqp = np.where(ph < 0.42, 1.0, -1.0)
    body = dsp.svf_lp(sawp * 0.55 + sqp * 0.45, 420.0, 2.2, sr)
    y = np.tanh((0.85 * sub + 0.45 * body) * 1.6)
    y *= (1.0 - np.exp(-t * 400.0)) * np.exp(-t * 9.0)
    return _out(y, 0.80)


# ── plucks, leads, pads ─────────────────────────────────────────────────────
def pluck(f, dur, sr, bright=0.7, **kw):
    n = _tail(dur, 0.25)
    y = dsp.osc("saw", f, n, sr) * 0.6 + dsp.osc("square", f * 2.0, n, sr) * 0.2
    cut = f * (2 + 9 * bright * np.exp(-np.arange(n) / (0.09 * sr)))
    y = dsp.svf_lp(y, cut, 1.1, sr)
    return _out(y * dsp.decay(n, max(dur * 0.9, 0.18), sr), 0.75)


def lead_saw(f, dur, sr, vib=0.15, detune=0.12, **kw):
    n = _tail(dur, 0.12)
    y = dsp.supersaw(f, n, 5, detune, sr, vib_delay_s=0.16, vib_depth=vib * 0.9)
    y = dsp.svf_lp(y, min(f * 8, 9000), 0.9, sr)
    return _out(y * dsp.adsr(n, 0.008, 0.12, 0.7, 0.12, sr), 0.78)


def lead_square(f, dur, sr, duty=0.5, **kw):
    n = _tail(dur, 0.04)
    y = dsp.osc("pulse", f, n, sr, pw=duty, vib_delay_s=0.12, vib_depth=0.08)
    return _out(y * dsp.adsr(n, 0.002, 0.05, 0.8, 0.04, sr), 0.70)


def chip_tri(f, dur, sr, **kw):
    n = _tail(dur, 0.03)
    return _out(dsp.osc("tri", f, n, sr) * dsp.adsr(n, 0.002, 0.02, 0.95, 0.03, sr), 0.75)


def chip_lead(f, dur, sr, **kw):
    """Pulse + detuned saw, delayed vibrato, a touch of bitcrush (NES/Genesis lead)."""
    n = _tail(dur, 0.05)
    y = (dsp.osc("pulse", f, n, sr, pw=0.28, vib_delay_s=0.20, vib_depth=0.20) * 0.65 +
         dsp.osc("saw", f * 1.004, n, sr, vib_delay_s=0.20, vib_depth=0.20) * 0.35)
    y = dsp.svf_lp(y, min(f * 9, 12000), 0.9, sr)
    y = dsp.bitcrush(y, 10, 1)
    return _out(y * dsp.adsr(n, 0.002, 0.06, 0.82, 0.05, sr), 0.76)


def pad(f, dur, sr, bright=0.5, **kw):
    n = _tail(dur, 0.6)
    t = _t(n, sr)
    y = dsp.supersaw(f, n, 6, 0.22, sr, vib_delay_s=0.4, vib_depth=0.06)
    cut = f * (2 + 6 * bright) * (0.6 + 0.4 * np.minimum(t / max(dur, 0.1), 1))
    y = dsp.svf_lp(y, cut, 0.8, sr)
    y = dsp.adsr(n, 0.35, 0.3, 0.8, 0.6, sr) * y
    st = np.column_stack([dsp.widen(np.column_stack([y, y]), 0.009, sr)[:, 0], y])
    return _out(st, 0.60)


def strings(f, dur, sr, **kw):
    n = _tail(dur, 0.4)
    y = dsp.supersaw(f, n, 5, 0.09, sr, vib_delay_s=0.22, vib_rate=5.5, vib_depth=0.16)
    y = dsp.svf_lp(y, min(f * 6, 7000), 0.85, sr)
    y = y * dsp.adsr(n, 0.12, 0.2, 0.85, 0.4, sr)
    return _out(np.column_stack([y, np.roll(y, 19)]), 0.55, fade_out=0.05)


def brass(f, dur, sr, **kw):
    n = _tail(dur, 0.12)
    t = _t(n, sr)
    y = dsp.osc("saw", f, n, sr) + dsp.osc("saw", f * 1.004, n, sr)
    cut = f * (1.5 + 7 * np.minimum(t / 0.09, 1))
    y = dsp.svf_lp(y * 0.5, cut, 1.5, sr)
    return _out(y * dsp.adsr(n, 0.04, 0.1, 0.8, 0.12, sr), 0.72)


def choir(f, dur, sr, vowel="a", **kw):
    n = _tail(dur, 0.5)
    src = dsp.supersaw(f, n, 4, 0.12, sr, vib_delay_s=0.3, vib_depth=0.12)
    y = dsp.formant(src, VOWELS.get(vowel, VOWELS["a"]), sr)
    y = y * dsp.adsr(n, 0.25, 0.2, 0.9, 0.5, sr)
    return _out(y, 0.58, fade_out=0.06)


def wobble(f, dur, sr, lfo=2.0, **kw):
    n = _tail(dur, 0.08)
    t = _t(n, sr)
    y = dsp.osc("saw", f, n, sr) + dsp.osc("saw", f * 1.007, n, sr) * 0.8 + dsp.osc("square", f * 0.5, n, sr) * 0.5
    cut = 180 + 2600 * (0.5 + 0.5 * np.sin(TAU * lfo * t - np.pi / 2)) ** 1.5
    y = dsp.asym_drive(dsp.svf_lp(y * 0.5, cut, 1.6, sr), 2.2)
    return _out(y * dsp.adsr(n, 0.005, 0.1, 0.95, 0.08, sr), 0.80)


# ── guitars (Karplus-Strong) ────────────────────────────────────────────────
def _ks_guitar(f, dur, sr, kind="power", mute=False, drive=7.0, bright=0.65, **kw):
    n = _tail(dur, 0.045 if mute else 0.5)
    damp = 0.968 if mute else 0.996
    br = 0.35 if mute else bright
    parts = [(1.0, 1.0), (1.4983, 0.55), (2.0, 0.30)] if kind == "power" else [(1.0, 1.0), (2.0, 0.22)]
    y = np.zeros(n)
    for mult, amp in parts:
        if f * mult < sr * 0.44:
            y += amp * dsp.ks_string(f * mult, n, damp, br, sr)
    y = dsp.asym_drive(y * 0.55, drive, 0.10)
    st = dsp.cab_filter(np.column_stack([y, y]), sr, 130, 4000)
    y = st.mean(1)
    t = _t(n, sr)
    if mute:
        y *= np.exp(-t * 13.0)
    y *= (1.0 - np.exp(-t * 1500.0))
    return _out(y, 0.85 if mute else 0.80)


def guitar_dist(f, dur, sr, drive=9.0, **kw):
    """Distorted power chord: KS root/5th/oct -> asymmetric tube drive -> cabinet."""
    bright = kw.pop("bright", 0.70)
    return _ks_guitar(f, dur, sr, kind="power", mute=False, drive=drive, bright=bright, **kw)


def guitar_mute(f, dur, sr, **kw):
    drive = kw.pop("drive", 9.0)
    kw.pop("bright", None)
    return _ks_guitar(f, dur, sr, kind="power", mute=True, drive=drive, bright=0.40, **kw)


def guitar_elec(f, dur, sr, drive=6.0, mute=0.0, bright=0.7, **kw):
    """Electric guitar: KS string(s) -> amp-style soft clipping -> cabinet.
    mute 0..1 shortens the note (palm mute)."""
    return _ks_guitar(f, dur * (1.0 - 0.55 * mute), sr, kind="single", mute=mute > 0.5,
                      drive=drive, bright=bright, **kw)


def guitar_pluck(f, dur, sr, bright=0.6, sustain=1.0, **kw):
    """Clean/acoustic plucked string: KS with a longer, brighter ring + pick transient."""
    n = _tail(dur, 0.35)
    y = dsp.ks_string(f, n, 0.9975, 0.55 + 0.35 * bright, sr)
    t = _t(n, sr)
    y *= np.exp(-t / max(0.6 * sustain, 0.05))
    return _out(y, 0.78)


# ── pianos ──────────────────────────────────────────────────────────────────
def _piano(f, dur, sr, variant="bright", **kw):
    tail = 1.1 if variant != "m1" else 0.45
    n = _tail(dur, tail)
    t = _t(n, sr)
    B = 0.00035 if variant != "m1" else 0.0006
    kmax = 8
    y = np.zeros(n)
    base_tau = {"bright": 1.3, "m1": 0.55, "ep": 1.0}.get(variant, 1.2)
    for k in range(1, kmax + 1):
        fk = k * f * np.sqrt(1.0 + B * k * k)
        if fk >= sr * 0.44:
            break
        amp = (1.0 / k ** (1.15 if variant == "bright" else 1.0)) * (1.0 if k % 7 else 0.55)
        tau = max(base_tau / (1.0 + 0.55 * (k - 1)), 0.06)
        det = 0.0 if variant == "m1" else 3.0
        for d in ((0.0,) if det == 0 else (-det, 0.0, det)):
            fk2 = fk * 2 ** (d / 1200.0)
            if fk2 < sr * 0.44:
                y += amp * np.sin(TAU * fk2 * t + 0.7 * k) * np.exp(-t / tau)
    y = y / (sum(1.0 / k ** 1.15 for k in range(1, kmax + 1)) * 1.25)
    # unison beating on the fundamental
    y += 0.18 * np.sin(TAU * f * 1.0015 * t) * np.exp(-t / base_tau)
    # 10 ms hammer thump
    nh = min(n, int(0.012 * sr))
    if nh > 4:
        rng = np.random.RandomState(int(f) % 4093 + 3)
        thump = dsp.bp(rng.randn(nh), max(120.0, f * 1.5), min(9000.0, f * 8 + 900), sr) * np.exp(-np.arange(nh) / (0.0028 * sr))
        y[:nh] += thump * (0.35 if variant != "m1" else 0.6)
    if variant == "m1":
        y = dsp.chorus(y, rate=0.9, depth=0.0025, mix=0.35, sr=sr)
    y *= (1.0 - np.exp(-t * 900.0))
    st = np.column_stack([y, np.roll(y, 7)])
    if variant != "ep":
        st = dsp.hall_reverb(st, 0.18 if variant == "bright" else 0.10, 1.6, sr, taps=6)
    return _out(st, 0.72, fade_out=0.03)


def piano(f, dur, sr, **kw):
    return _piano(f, dur, sr, "bright", **kw)


def piano_m1(f, dur, sr, **kw):
    """90s punchy house piano stab (M1-style): bright, short, chorused."""
    return _piano(f, min(dur, 0.45), sr, "m1", **kw)


def ep(f, dur, sr, **kw):
    """DX7 Rhodes: 1:1 FM body + 14:1 tine ping + chorus."""
    n = _tail(dur, 0.5)
    t = _t(n, sr)
    body = dsp.fm(f, n, 1.0, 1.7, dsp.decay(n, 0.6, sr), sr)
    tine = dsp.fm(f, n, 14.0, 0.55, dsp.decay(n, 0.035, sr), sr)
    y = body * np.exp(-t / max(dur, 0.45)) + 0.32 * tine * np.exp(-t * 6.0)
    y = dsp.chorus(y, rate=0.55, depth=0.0028, mix=0.4, sr=sr)
    return _out(np.column_stack([y, np.roll(y, 11)]), 0.72, fade_out=0.04)


# ── organs ──────────────────────────────────────────────────────────────────
_DRAWBARS = [(0.5, 0.50), (1.0, 1.00), (1.5, 0.85), (2.0, 0.70), (3.0, 0.45), (4.0, 0.35), (6.0, 0.22), (8.0, 0.15)]


def _organ(f, dur, sr, rock=False, pipe=False, **kw):
    tail = 0.9 if pipe else 0.18
    n = _tail(dur, tail)
    t = _t(n, sr)
    yL = np.zeros(n)
    yR = np.zeros(n)
    for i, (mult, amp) in enumerate(_DRAWBARS):
        fk = f * mult
        if fk >= sr * 0.44:
            continue
        det = 0.12 if i % 2 else -0.12
        yL += amp * np.sin(TAU * fk * 2 ** (-det / 1200.0) * t)
        yR += amp * np.sin(TAU * fk * 2 ** (det / 1200.0) * t)
    yL /= 3.2
    yR /= 3.2
    if pipe:
        nb = min(n, int(0.04 * sr))
        rng = np.random.RandomState(91)
        breath = dsp.bp(rng.randn(nb), 500, 5000, sr) * np.linspace(0, 1, nb) ** 1.5
        yL[:nb] += breath * 0.30
        yR[:nb] += breath * 0.26
        wet = dsp.hall_reverb(np.column_stack([yL, yR]), 0.5, 3.2, sr, damp=5500)
        yL, yR = wet[:, 0], wet[:, 1]
    # 20 ms key click
    nk = min(n, int(0.02 * sr))
    if nk:
        rng = np.random.RandomState(int(f) % 2003 + 7)
        click = dsp.hp(rng.randn(nk), 2200, sr) * np.exp(-np.arange(nk) / (0.004 * sr)) * 0.5
        yL[:nk] += click
        yR[:nk] += click * 0.8
    y = np.column_stack([yL, yR])
    if rock:
        y = np.column_stack([dsp.asym_drive(y[:, c] * 1.8, 3.2) for c in range(2)])
        rot = 0.82 + 0.18 * np.sin(TAU * 6.0 * t)
        y = np.column_stack([y[:, 0] * rot, y[:, 1] * (1.82 - rot)])
        y = dsp.chorus(y, rate=6.0, depth=0.0012, mix=0.25, sr=sr)
    env = dsp.adsr(n, 0.008, 0.03 if not pipe else 0.05, 1.0, 0.35 if pipe else 0.10, sr)
    return _out(y * env[:, None], 0.62 if pipe else 0.66)


def organ(f, dur, sr, **kw):
    """90s house drawbar organ with key click and stereo shimmer."""
    return _organ(f, dur, sr, **kw)


def organ_rock(f, dur, sr, **kw):
    """Overdriven B3 through a 6 Hz rotary tremolo."""
    return _organ(f, dur, sr, rock=True, **kw)


def organ_pipe(f, dur, sr, **kw):
    """Church pipe organ: 35 ms breath onset, bright upper ranks, cathedral reverb."""
    return _organ(f, dur, sr, pipe=True, **kw)


# ── bells and chimes ────────────────────────────────────────────────────────
def bell(f, dur, sr, **kw):
    """Y2K FM bell with ping-pong delay and hall reverb."""
    n = _tail(dur, 1.5)
    t = _t(n, sr)
    ienv = dsp.decay(n, 0.8, sr)
    y = dsp.fm(f, n, 3.5, 2.2, ienv, sr) + 0.4 * dsp.fm(f * 2.0, n, 1.4, 1.0, ienv, sr)
    y *= np.exp(-t / 1.25) * (1.0 - np.exp(-t * 800.0))
    st = np.column_stack([y, y])
    st = dsp.ping_pong_delay(st, 0.30, 0.32, 0.30, sr)
    st = dsp.hall_reverb(st, 0.24, 1.8, sr, taps=7)
    return _out(st, 0.62, fade_out=0.05)


def bell_tubular(f, dur, sr, **kw):
    """Tubular bell: metallic partials [1, 2.76, 4.07, 5.43] with long decays."""
    n = _tail(dur, 2.4)
    t = _t(n, sr)
    y = np.zeros(n)
    for mult, amp, tau in ((1.0, 1.0, 2.6), (2.76, 0.55, 1.8), (4.07, 0.35, 1.2), (5.43, 0.22, 0.9), (7.1, 0.10, 0.6)):
        if f * mult < sr * 0.44:
            y += amp * np.sin(TAU * f * mult * t) * np.exp(-t / tau)
    rng = np.random.RandomState(int(f) % 3001 + 5)
    ns = min(n, int(0.02 * sr))
    y[:ns] += dsp.hp(rng.randn(ns), 2500, sr) * np.exp(-np.arange(ns) / (0.004 * sr)) * 0.35
    st = dsp.hall_reverb(np.column_stack([y, y]), 0.3, 2.4, sr, taps=8)
    return _out(st, 0.58, fade_out=0.06)


def music_box(f, dur, sr, **kw):
    """Eerie cold celesta: 4:1 FM tine with a detuned upper sparkle."""
    n = _tail(dur, 0.8)
    t = _t(n, sr)
    y = dsp.fm(f, n, 4.0, 1.3, dsp.decay(n, 0.12, sr), sr)
    y += 0.22 * np.sin(TAU * f * 7.02 * t) * np.exp(-t / 0.10)
    y *= np.exp(-t / 0.45) * (1.0 - np.exp(-t * 1200.0))
    st = np.column_stack([y, np.roll(y, 5)])
    st = dsp.hall_reverb(st, 0.16, 1.4, sr, taps=5)
    return _out(st, 0.55, fade_out=0.04)


def clock_bell(f, dur, sr, **kw):
    """A Grave Soul-style deep church/clock bell: octave-down hum, felt+metal strike, cathedral tail."""
    n = _tail(dur, 2.6)
    t = _t(n, sr)
    y = np.zeros(n)
    for mult, amp, tau in ((0.5, 0.95, 3.6), (1.0, 0.85, 3.0), (1.2, 0.45, 2.2),
                           (1.5, 0.32, 1.8), (2.0, 0.35, 1.5), (2.74, 0.18, 1.0),
                           (3.4, 0.12, 0.8), (4.1, 0.08, 0.6)):
        fk = f * mult
        if fk < sr * 0.44:
            y += amp * np.sin(TAU * fk * t + 0.3 * mult) * np.exp(-t / tau)
    rng = np.random.RandomState(int(f) % 4001 + 9)
    ns = min(n, int(0.05 * sr))
    felt = dsp.lp(rng.randn(ns), 1400, sr) * np.exp(-np.arange(ns) / (0.012 * sr)) * 0.7
    metal = dsp.hp(rng.randn(ns), 3500, sr) * np.exp(-np.arange(ns) / (0.004 * sr)) * 0.35
    y[:ns] += felt + metal
    st = dsp.hall_reverb(np.column_stack([y, np.roll(y, 23)]), 0.42, 3.6, sr, damp=4500, taps=12)
    return _out(st, 0.70, fade_out=0.09)


# ── orchestral / FX / percussion voices ────────────────────────────────────
def stab(f, dur, sr, **kw):
    n = _tail(dur, 0.15)
    y = dsp.supersaw(f, n, 5, 0.25, sr)
    y = dsp.svf_lp(y, f * (3 + 12 * np.exp(-np.arange(n) / (0.08 * sr))), 1.6, sr)
    return _out(y * dsp.adsr(n, 0.002, 0.12, 0.2, 0.15, sr), 0.72)


def rave_stab(f, dur, sr, **kw):
    """90s rave minor-chord snap (root + minor third + fifth + octave)."""
    n = _tail(dur, 0.22)
    y = np.zeros(n)
    for mult in (1.0, 2 ** (3 / 12), 2 ** (7 / 12), 2.0):
        y += dsp.osc("saw", f * mult, n, sr) + dsp.osc("square", f * mult * 1.004, n, sr) * 0.35
    cut = f * (4 + 18 * np.exp(-np.arange(n) / (0.06 * sr)))
    y = dsp.svf_lp(y, cut, 1.8, sr)
    y = dsp.chorus(np.column_stack([y, y]), rate=5.0, depth=0.001, mix=0.3, sr=sr)
    env = dsp.adsr(n, 0.002, 0.16, 0.0, 0.18, sr)
    return _out(y * env[:, None], 0.78)


def orch_hit(f, dur, sr, **kw):
    """Orchestral hit: detuned string chord + timpani thump + noise transient."""
    n = _tail(dur, 0.8)
    t = _t(n, sr)
    y = np.zeros(n)
    for mult in (1.0, 2 ** (3 / 12), 2 ** (7 / 12), 2.0, 2 ** (10 / 12)):
        y += dsp.supersaw(f * mult, n, 3, 0.10, sr)
    y = dsp.svf_lp(y, 4800, 0.9, sr) * np.exp(-t / 0.55)
    thump = np.sin(TAU * np.cumsum(f * 0.5 * np.exp(-t * 5) + 45) / sr) * np.exp(-t * 4.0)
    rng = np.random.RandomState(41)
    y += 0.6 * thump + 0.25 * dsp.hp(rng.randn(n), 2000, sr) * np.exp(-t * 30.0)
    st = dsp.hall_reverb(np.column_stack([y, y]), 0.25, 2.0, sr, taps=7)
    return _out(st, 0.76, fade_out=0.05)


def rave_shout(f, dur, sr, **kw):
    """Dual/triple band-pass formant 'Ha!' (short vocal shout)."""
    n = _tail(min(dur, 0.22), 0.10)
    t = _t(n, sr)
    rng = np.random.RandomState(77)
    src = rng.randn(n)
    y = dsp.formant(src, VOWELS["ha"], sr)
    y += 0.3 * dsp.formant(dsp.osc("saw", f, n, sr), VOWELS["ha"], sr)
    env = (1.0 - np.exp(-t * 900.0)) * (np.exp(-t * 9.0) + 0.35 * np.exp(-((t - 0.09) / 0.03) ** 2))
    return _out(y * env, 0.72)


def marimba(f, dur, sr, **kw):
    """Woody mallet: fundamental + 4th + 9th partial, fast decay, soft mallet click."""
    n = _tail(dur, 0.45)
    t = _t(n, sr)
    y = (np.sin(TAU * f * t) + 0.35 * np.sin(TAU * f * 3.93 * t) * np.exp(-t * 18)
         + 0.15 * np.sin(TAU * f * 9.2 * t) * np.exp(-t * 30))
    y *= np.exp(-t / 0.38) * (1.0 - np.exp(-t * 700.0))
    rng = np.random.RandomState(int(f) % 1709 + 2)
    ns = min(n, int(0.008 * sr))
    y[:ns] += dsp.bp(rng.randn(ns), 800, 3500, sr) * np.exp(-np.arange(ns) / (0.002 * sr)) * 0.3
    return _out(y, 0.70)


def heartbeat(f, dur, sr, **kw):
    """Two low thumps (lub-dub)."""
    n = _tail(max(dur, 0.55), 0.15)
    t = _t(n, sr)
    y = np.zeros(n)
    for off, g in ((0.0, 1.0), (0.20, 0.72)):
        tt = np.maximum(t - off, 0.0)
        on = (t >= off)
        y += np.sin(TAU * (52 + 34 * np.exp(-tt * 42)) * tt) * np.exp(-tt * 19) * g * on
    return _out(np.tanh(y * 1.5), 0.72)


def siren_riser(f, dur, sr, **kw):
    """Rising siren: pitch climbs an octave+, with tremolo and air."""
    n = _tail(dur, 0.10)
    t = _t(n, sr)
    fr = f * (1.0 + 3.0 * (t / max(dur, 0.05)) ** 1.6)
    y = np.sin(TAU * np.cumsum(fr) / sr) * 0.6 + dsp.osc("saw", fr, n, sr) * 0.25
    y *= 0.55 + 0.45 * np.sin(TAU * 7.0 * t) ** 2
    rng = np.random.RandomState(15)
    y += 0.18 * dsp.hp(rng.randn(n), 2000, sr) * (t / max(dur, 0.05))
    return _out(y * (t / max(dur, 0.05)) ** 1.3, 0.68)


def clock_tick(f, dur, sr, **kw):
    """Woodblock/clock tick: short filtered click with a pitched body."""
    n = _tail(min(dur, 0.12), 0.05)
    t = _t(n, sr)
    rng = np.random.RandomState(int(f) % 811 + 4)
    y = dsp.bp(rng.randn(n), 1200, 6000, sr) * np.exp(-t * 90.0)
    y += 0.5 * np.sin(TAU * f * t) * np.exp(-t * 55.0)
    return _out(y, 0.62)


def drone(f, dur, sr, **kw):
    n = _tail(dur, 1.0)
    t = _t(n, sr)
    y = dsp.osc("saw", f * (1 + 0.002 * np.sin(TAU * 0.13 * t)), n, sr) + dsp.osc("saw", f * 1.0145, n, sr) * 0.8
    y = dsp.svf_lp(y * 0.5, 250 + 500 * (0.5 + 0.5 * np.sin(TAU * 0.09 * t)), 1.1, sr)
    return _out(dsp.asym_drive(y, 1.5) * dsp.adsr(n, 0.8, 0.5, 0.9, 1.0, sr), 0.62)


def showtime_sax(f, dur, sr, **kw):
    """Theatrical formant synth-sax: 35 ms upward scoop, breath transient, delayed vibrato."""
    n = _tail(dur, 0.18)
    t = _t(n, sr)
    sawy = dsp.osc("saw", f, n, sr, glide_from=f * 0.94, glide_s=0.035,
                   vib_delay_s=0.18, vib_rate=5.2, vib_depth=0.18)
    sawy += 0.35 * dsp.osc("square", f * 2.0, n, sr)
    body = dsp.formant(sawy, VOWELS["a"], sr) * 1.4
    breath = dsp.bp(np.random.RandomState(int(f) % 997 + 8).randn(n), 900, 4200, sr)
    breath *= np.exp(-t * 22.0) * 0.35
    y = body + breath
    y *= (1.0 - np.exp(-t * 160.0)) * np.exp(-t * 1.6)
    y = dsp.svf_lp(y, 5200, 0.8, sr)
    st = dsp.hall_reverb(np.column_stack([y, np.roll(y, 9)]), 0.16, 1.5, sr, taps=6)
    return _out(st, 0.66, fade_out=0.04)


INSTRUMENTS = {k: v for k, v in dict(
    # legacy keys (kept working, upgraded DSP)
    sine_sub=sine_sub, saw_bass=saw_bass, reese=reese, pluck=pluck, lead_saw=lead_saw,
    lead_square=lead_square, chip_tri=chip_tri, pad=pad, strings=strings, brass=brass,
    ep=ep, bell=bell, piano=piano, organ=organ, choir=choir, guitar=guitar_dist,
    guitar_mute=guitar_mute, sub_drop=sub_drop, stab=stab, drone=drone,
    music_box=music_box, wobble=wobble, guitar_pluck=guitar_pluck, guitar_elec=guitar_elec,
    # V2 additions
    piano_m1=piano_m1, organ_rock=organ_rock, organ_pipe=organ_pipe,
    bell_tubular=bell_tubular, clock_bell=clock_bell, acid_303=acid_303,
    chip_lead=chip_lead, pulsing_bass=pulsing_bass, y2k_bass=y2k_bass,
    showtime_sax=showtime_sax, marimba=marimba, rave_stab=rave_stab,
    orch_hit=orch_hit, rave_shout=rave_shout, heartbeat=heartbeat,
    siren_riser=siren_riser, clock_tick=clock_tick).items()}


# ── v3 merge: the buzz-free engine (forge/instruments_v3.py: PolyBLEP oscillators, Karplus-Strong guitars,
# physical bells/organs, Y2K voices). Its voices take (freq, dur, velocity, sr); adapt them to V2's (f, dur, sr).
# Applied BEFORE the v1.4 real/voices merge below, so those newer voices still win any shared name.
# `strings` and `choir` stay V2's: the v3 versions failed the selftest peak check (too quiet / non-finite).
from . import instruments_v3 as _v3  # noqa: E402

_V3_KEEP_V2 = {"strings", "choir"}


def _adapt_v3(fn):
    def voice(f, dur, sr=SR, **kw):
        y = np.asarray(fn(f, dur, 0.85, sr, **kw), dtype=float)
        pk = float(np.max(np.abs(y))) if y.size else 0.0
        if 1e-6 < pk < 0.3:          # some v3 pads render very quietly: bring them up to a usable level
            y = y * (0.55 / pk)
        return y
    voice.__doc__ = getattr(fn, "__doc__", None)
    return voice


for _k, _fn in _v3.INSTRUMENTS.items():
    if _k not in _V3_KEEP_V2:
        INSTRUMENTS[_k] = _adapt_v3(_fn)


# ── v1.4 merge: the "real" voices (forge/real.py, forge/voices.py). V2's own names are untouched so both can be A/B tested.
from . import real as _real, voices as _voices  # noqa: E402
INSTRUMENTS.update(_real.NEW)
INSTRUMENTS.update(_voices.NEW)
INSTRUMENTS.update(rhodes=_voices.ep_rhodes, harp_pluck=_voices.harp, strings_real=_voices.string_ensemble,
                   brass_real=_voices.brass_section, bass_pick=_voices.bass_guitar, glockenspiel=_real.glock,
                   organ_pipe_real=_real.organ_church, tubular_bell=_real.bell_tubular)

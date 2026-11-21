"""theory.py -- scales, chords, progressions, melody generation.

V2 (2026-11-19): melodies get a call-and-response motif structure, syncopated
onsets, octave leaps and expressive phrasing (velocity accents, phrase-end
breaths, grace notes). `melody(...)` keeps its old signature; the new controls
are optional keyword arguments with sensible defaults.
"""
import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
FLAT = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "pent_minor": [0, 3, 5, 7, 10],
    "pent_major": [0, 2, 4, 7, 9],
    "blues": [0, 3, 5, 6, 7, 10],
    "locrian": [0, 1, 3, 5, 6, 8, 10],
}


def key_to_pc(name):
    name = FLAT.get(name, name)
    return NOTE_NAMES.index(name)


def note_to_midi(name, octave=4):
    return 12 * (octave + 1) + key_to_pc(name)


def scale_note(root_pc, scale, degree, octave=4):
    """degree may exceed the scale length / be negative -> wraps octaves. returns MIDI."""
    s = SCALES[scale]
    n = len(s)
    o, d = divmod(int(degree), n)
    return 12 * (octave + 1 + o) + root_pc + s[d]


def chord(root_pc, scale, degree, octave=3, kind="triad", inversion=0):
    """chord built by stacking scale thirds on `degree`. kind: triad seventh sus2 sus4 power ninth"""
    if kind == "power":
        r = scale_note(root_pc, scale, degree, octave)
        return [r, r + 7, r + 12]
    steps = {"triad": [0, 2, 4], "seventh": [0, 2, 4, 6], "ninth": [0, 2, 4, 6, 8],
             "sus2": [0, 1, 4], "sus4": [0, 3, 4]}[kind]
    notes = [scale_note(root_pc, scale, degree + s, octave) for s in steps]
    for _ in range(inversion):
        notes = notes[1:] + [notes[0] + 12]
    return notes


def chord_quality(root_pc, scale, degree):
    t = chord(root_pc, scale, degree, 3)
    third, fifth = t[1] - t[0], t[2] - t[0]
    return {(4, 7): "maj", (3, 7): "min", (3, 6): "dim", (4, 8): "aug"}.get((third, fifth), "?")


# progressions as scale-degree roots (0-based). several per mood so seeds vary.
PROGRESSIONS = {
    "minor": [[0, 5, 2, 6], [0, 6, 5, 6], [0, 3, 6, 5], [0, 0, 5, 6], [0, 5, 3, 6], [0, 2, 5, 6]],
    "major": [[0, 4, 5, 3], [0, 5, 3, 4], [0, 3, 4, 4], [0, 4, 1, 3], [0, 5, 1, 4]],
    "dorian": [[0, 3, 0, 6], [0, 1, 3, 0]],
    "phrygian": [[0, 1, 0, 6], [0, 1, 6, 0]],
    "lydian": [[0, 1, 0, 4], [0, 4, 1, 0]],
    "mixolydian": [[0, 6, 3, 0], [0, 6, 4, 0]],
    "harmonic_minor": [[0, 5, 4, 0], [0, 3, 4, 0]],
    "pent_minor": [[0, 0, 0, 0]],
    "blues": [[0, 0, 3, 0, 4, 3, 0, 4]],
}


def _contour(k, contour):
    """target heights in scale degrees for k onsets"""
    x = np.linspace(0, 1, max(k, 1))
    if contour == "arch":
        return np.sin(x * np.pi) * 4.0
    if contour == "rise":
        return x * 5.0
    if contour == "fall":
        return (1 - x) * 5.0
    if contour == "wave":
        return np.sin(x * 2 * np.pi) * 3.0
    return np.zeros(max(k, 1))


def _motif(rng, mspan, steps_per_bar, density, rest, syncopation, leap, contour):
    """one motif: syncopated onset grid + contour degrees.

    Syncopation pushes some onsets off the grid: a note lands on the 'a' of the
    beat or ties a strong beat to a weak one, which is what makes a line groove
    instead of marching. Returns (onsets, degrees, accents, ties)."""
    onsets = []
    for s in range(mspan):
        strong = (s % 4 == 0)
        off8 = (s % 2 == 0)
        p = density * (1.0 if strong else 0.7 if off8 else 0.34)
        if s % 16 == 0:
            p = 1.0
        # syncopation: prefer the 'a' (step 3 of 4) and '&' (step 2) of a beat
        if syncopation > 0 and s % 4 in (2, 3):
            p *= 1.0 + 0.9 * syncopation
            if s % 4 == 3:
                p *= 1.0 + 0.4 * syncopation
        if rng.rand() < p * (1 - rest * (0 if strong else 1)):
            onsets.append(s)
    if len(onsets) < 3:
        onsets = sorted(set(onsets + [0, steps_per_bar // 2, mspan - steps_per_bar // 4]))
    k = len(onsets)
    base = _contour(k, contour)
    degs = np.round(base + rng.randint(-1, 2, k) + (rng.rand(k) < leap) * rng.choice([-7, -3, 3, 4], k)).astype(int)
    # phrase shape: start and end near chord tones (degree 0/2/4), peak in the middle
    degs[0] = int(np.clip(degs[0], -2, 2))
    degs[-1] = int(np.clip(degs[-1], 0, 4))
    accents = np.array([1.0 if s % 4 == 0 else 0.82 if s % 2 == 0 else 0.68 for s in onsets])
    return onsets, degs, accents


def melody(rng, root_pc, scale, bars, steps_per_bar=16, octave=5, density=0.5, prog=None,
           contour="arch", motif_bars=2, leap=0.2, rest=0.25,
           call_response=True, syncopation=0.35, octave_leap=0.10, phrasing=1.0):
    """Generate a motif and repeat/vary it. returns list of (step, dur_steps, midi, vel)

    Chord tones land on strong steps; the motif repeats every motif_bars with
    small variations. V2 adds:
      call_response  bars 2-4 answer bars 1-2 (transposed/contrary motion) instead of a plain repeat
      syncopation    0..1, how strongly onsets are pushed off the beat (the 'a' of the beat)
      octave_leap    0..1, chance an expressive note jumps an octave
      phrasing       >0 adds velocity shaping and a breath (rest) at phrase ends
    """
    sc = SCALES[scale]
    n_deg = len(sc)
    prog = prog or PROGRESSIONS.get(scale, PROGRESSIONS["minor"])[0]
    total = bars * steps_per_bar
    mspan = motif_bars * steps_per_bar
    onsets, degs, accents = _motif(rng, mspan, steps_per_bar, density, rest,
                                   float(np.clip(syncopation, 0, 1)), leap, contour)
    out = []
    for rep in range(0, total, mspan):
        phrase = rep // mspan
        answer = call_response and phrase % 2 == 1
        # the answer restates the call a fourth up (or down) and ends on the tonic
        shift = 0
        if answer:
            shift = 3 if rng.rand() < 0.5 else -2
        for i, s in enumerate(onsets):
            step = rep + s
            if step >= total:
                continue
            bar = step // steps_per_bar
            ch_root = prog[bar % len(prog)]
            d = ch_root + degs[i] + shift
            # variation on repeats
            if rep > 0 and rng.rand() < 0.2:
                d += rng.choice([-1, 1])
            # strong beats snap to chord tones (root/3rd/5th of the current chord)
            if (s % steps_per_bar) % 8 == 0:
                tones = np.array([0, 2, 4])
                rel = (d - ch_root) % n_deg
                d = d + int(tones[np.argmin(np.abs(tones - rel))] - rel)
            # expressive octave leap, mostly in the second half of a phrase
            oct_shift = 0
            if octave_leap > 0 and i > len(onsets) // 2 and rng.rand() < octave_leap:
                oct_shift = 12 * rng.choice([-1, 1])
            midi = scale_note(root_pc, scale, d, octave) + oct_shift
            nxt = onsets[i + 1] if i + 1 < len(onsets) else mspan
            dur = max(1, min(nxt - s, 8))
            # phrasing: legato overlap on weak steps, short detached notes elsewhere
            if phrasing > 0 and s % 4 == 0 and dur >= 2:
                dur = min(dur + 1, 8)
            vel = float(np.clip(accents[i] * (0.72 + 0.30 * phrasing) + rng.randn() * 0.04, 0.25, 1.0))
            if answer and i == len(onsets) - 1:
                dur = max(dur, 3)                        # let the answer ring
            out.append((step, dur, midi, round(vel, 3)))
    # grace notes: a fast approach note a step below a strong phrase note
    if phrasing > 0 and len(out) > 4:
        extra = []
        for j in (1, len(out) // 2):
            step, dur, midi, vel = out[j]
            if step >= 2 and dur >= 2:
                extra.append((step - 1, 1, midi - 2, vel * 0.55))
        out.extend(extra)
        out.sort(key=lambda e: e[0])
    return out


def arp(rng, root_pc, scale, bars, steps_per_bar=16, octave=4, rate=1, pattern="updown",
        kind="triad", prog=None, accent=0.25, humanize_vel=0.08):
    """Arpeggiate the current chord. V2: accents, a slight velocity humanisation
    and an optional octave jump on the last repetition (classic chip/trance lift)."""
    prog = prog or PROGRESSIONS.get(scale, PROGRESSIONS["minor"])[0]
    out = []
    steps = max(1, int(rate))
    for bar in range(bars):
        root = prog[bar % len(prog)]
        notes = chord(root_pc, scale, root, octave, kind=kind)
        seq = []
        if pattern == "updown":
            seq = notes + notes[-2:0:-1]
        elif pattern == "down":
            seq = notes[::-1]
        elif pattern == "up":
            seq = notes
        elif pattern == "random":
            seq = notes
        for s in range(0, steps_per_bar, steps):
            if pattern == "random":
                m = notes[rng.randint(len(notes))]
            else:
                m = seq[(s // steps) % len(seq)]
            step = bar * steps_per_bar + s
            v = 0.8 + accent * (1.0 if s % 4 == 0 else 0.0) + rng.randn() * humanize_vel
            out.append((step, steps, m, float(np.clip(v, 0.2, 1.0))))
    return out


def humanize(events, rng, timing=0.0, vel=0.0):
    """events: [(step, dur, midi, vel)]; timing in steps (float), vel in 0-1"""
    return [(s + rng.randn() * timing, d, m, float(np.clip(v + rng.randn() * vel, 0.05, 1.0))) for s, d, m, v in events]

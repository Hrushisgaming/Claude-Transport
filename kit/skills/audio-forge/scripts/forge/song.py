"""song.py -- sequence events on a 16th-note grid, mix tracks with FX sends, master, export stems + beatmap.

V2 (2026-11-19) mixing:
  * automatic 150 Hz high-pass on every non-bass, non-drum track (kills low-mid mud)
  * mono low end below 140 Hz on the master
  * automatic stereo widening on guitars / pads / supersaws
  * kick-triggered sidechain ducking on bass / pads / guitars
  * gentle bus saturation + look-ahead limiter, then peak normalise
All of it can be overridden per track with fx=... (auto_hp=False, widen=0.0, sidechain=0.0).
"""
import json
import numpy as np
from scipy.io import wavfile
from . import dsp, drums, instruments
from .dsp import SR

# loudness trims so every instrument sits at a similar level before mixing
TRIM = dict(choir=5.0, pad=3.0, lead_saw=3.5, stab=4.0, strings=3.0, pluck=2.0, guitar=0.85,
            bell=1.3, music_box=1.3, lead_square=1.0, drone=0.9,
            # V2 voices
            organ=1.6, organ_rock=1.6, organ_pipe=2.2, piano=2.0, piano_m1=2.2, ep=1.8,
            bell_tubular=1.8, clock_bell=1.2, acid_303=1.1, chip_lead=1.2, pulsing_bass=1.15,
            y2k_bass=1.1, showtime_sax=1.7, marimba=1.4, rave_stab=1.6, orch_hit=1.2,
            rave_shout=2.2, heartbeat=1.2, siren_riser=1.6, clock_tick=1.4,
            guitar_elec=0.95, guitar_pluck=1.1, brass=1.4, saw_bass=1.05, reese=1.0)

BASS_INST = {"sine_sub", "saw_bass", "reese", "sub_drop", "wobble", "acid_303", "pulsing_bass", "y2k_bass", "chip_tri", "bass_guitar", "bass_pick"}
PAD_INST = {"pad", "strings", "choir", "drone", "string_ensemble", "strings_real"}
GUITAR_INST = {"guitar", "guitar_mute", "guitar_elec", "guitar_pluck", "guitar_amp", "guitar_crunch", "guitar_heavy", "guitar_lead", "guitar_ks"}
WIDE_INST = PAD_INST | GUITAR_INST | {"lead_saw", "stab", "rave_stab", "orch_hit", "brass", "showtime_sax", "organ"}


def _is_bass(name, kinds):
    return bool(kinds & BASS_INST) or any(k in name.lower() for k in ("bass", "sub", "808"))


class Track:
    def __init__(self, name, n, **fx):
        self.name = name
        self.buf = np.zeros((n, 2))
        self.fx = fx  # gain_db pan hp lp reverb delay chorus drive comp sidechain widen crush auto_hp
        self.kinds = set()
        self.is_drum = bool(fx.pop("is_drum", False))


class Song:
    def __init__(self, bpm, total_bars, beats_per_bar=4, swing=0.0, seed=0, sr=SR, tail=3.0):
        self.bpm, self.bars, self.bpb, self.swing, self.sr = float(bpm), int(total_bars), beats_per_bar, swing, sr
        self.spb = 4  # steps per beat (16ths)
        self.swing_grid = 1  # 1 = swing the off-16ths, 2 = swing the off-8ths (jazz)
        self.steps_per_bar = beats_per_bar * self.spb
        self.step_s = 60.0 / self.bpm / self.spb
        self.dur_s = self.bars * self.steps_per_bar * self.step_s
        self.n = int((self.dur_s + tail) * sr)
        self.rng = np.random.RandomState(seed)
        self.tracks = {}
        self.sections = []  # (name, start_bar, bars)
        self.hits = {}      # kick sample positions for sidechain
        self._cache = {}
        self.events = []  # (track, kind, step, dur_steps, midi_or_drum, vel) for MIDI export
        np.random.seed(seed)

    # ── timing ──
    def t_of(self, step):
        """seconds of a (possibly fractional) 16th-step, with swing on off-16ths"""
        s = float(step)
        g = self.swing_grid
        if self.swing and int(round(s)) % (2 * g) == g and abs(s - round(s)) < 1e-6:
            s += self.swing * g
        return s * self.step_s

    def track(self, name, **fx):
        if name not in self.tracks:
            is_drum = fx.pop("is_drum", False)
            self.tracks[name] = Track(name, self.n, **fx)
            self.tracks[name].is_drum = is_drum
        elif fx:
            self.tracks[name].fx.update(fx)
        return self.tracks[name]

    def _mix_in(self, tr, y, at_s, gain=1.0, pan=0.0):
        i = int(at_s * self.sr)
        if i >= self.n or i < 0:
            return
        ys = dsp.stereo(y, pan) if y.ndim == 1 else y
        j = min(i + len(ys), self.n)
        tr.buf[i:j] += ys[:j - i] * gain

    # ── events ──
    def drum(self, track, name, step, vel=1.0, kit="808", pan=0.0):
        self.events.append((track, "drum", step, 0.25, name, vel))
        tr = self.track(track, is_drum=True)
        tr.is_drum = True
        t = self.t_of(step)
        self._mix_in(tr, drums.hit(name, kit, vel), t, 1.0, pan)
        if name == "kick":
            self.hits.setdefault(track, []).append(int(t * self.sr))

    def note(self, track, inst, step, dur_steps, midi, vel=0.8, pan=0.0, **kw):
        self.events.append((track, inst, step, dur_steps, int(midi), vel))
        tr = self.track(track)
        tr.kinds.add(inst)
        dur = max(dur_steps * self.step_s, 0.03)
        key = (inst, int(midi), round(dur, 3), tuple(sorted(kw.items())))
        if key not in self._cache:
            self._cache[key] = instruments.render(inst, midi, dur, 1.0, self.sr, **kw) * TRIM.get(inst, 1.0)
        self._mix_in(tr, self._cache[key], self.t_of(step), vel, pan)

    def sample(self, track, y, step, gain=1.0, pan=0.0):
        self._mix_in(self.track(track), y, self.t_of(step), gain, pan)

    def mark(self, name, start_bar, bars):
        self.sections.append((name, int(start_bar), int(bars)))

    # ── per-track processing ──
    def _process(self, tr, sc_hits):
        fx, y = tr.fx, tr.buf
        name = tr.name
        bass = _is_bass(name, tr.kinds)
        if fx.get("hp"):
            y = dsp.hp(y, fx["hp"], self.sr)
        elif fx.get("auto_hp", True) and not bass and not tr.is_drum:
            y = dsp.hp(y, 150, self.sr, 2)          # stop low-mid mud on everything melodic
        if fx.get("lp"):
            y = dsp.lp(y, fx["lp"], self.sr)
        if fx.get("chorus"):
            y = dsp.chorus(y, mix=fx["chorus"])
        if fx.get("drive"):
            y = dsp.distort(y, fx["drive"], fx.get("drive_mode", "tanh"))
        if fx.get("crush"):
            y = dsp.bitcrush(y, fx["crush"], fx.get("crush_hold", 1))
        if fx.get("comp"):
            y = dsp.compress(y, *fx["comp"], sr=self.sr)
        # kick sidechain: explicit value, else automatic on bass / pads / guitars
        sc = fx.get("sidechain")
        if sc is None and sc_hits and not tr.is_drum:
            if bass:
                sc = 0.34
            elif tr.kinds & (PAD_INST | GUITAR_INST):
                sc = 0.22
        if sc and sc_hits:
            y = y * dsp.sidechain_curve(self.n, sc_hits, sc, fx.get("sc_release", 0.16), sr=self.sr)[:, None]
        # stereo width: explicit, else auto on guitars / pads / supersaws
        w = fx.get("widen")
        if w is None and not bass and not tr.is_drum and (tr.kinds & WIDE_INST):
            w = 0.009 if tr.kinds & PAD_INST else 0.007
        if w:
            y = dsp.widen(y, float(w), self.sr)
        return y * dsp.db(fx.get("gain_db", 0.0))

    # loudness shape per section type, in dB: a constant, or (start_db, end_db) for a ramp across the section
    SECTION_DB = dict(intro=-5.0, build=(-9.0, -1.0), drop=0.0, chase=0.0, climax=0.0, main=0.0, chorus=0.0, verse=-2.0,
                      **{"break": -6.0}, outro=(-1.5, -14.0))

    def dynamics_curve(self, amount=1.0, xfade=0.18):
        """per-sample gain (linear) that shapes the song's energy arc: quiet intro, rising build, full drop, dipped break"""
        if not self.sections or amount <= 0:
            return None
        bar_s = self.bpb * 60.0 / self.bpm
        xs, ys = [0.0], []
        pts = []
        for name, sb, nb in self.sections:
            g = self.SECTION_DB.get(name, 0.0)
            g0, g1 = (g if isinstance(g, tuple) else (g, g))
            t0, t1 = sb * bar_s, (sb + nb) * bar_s
            pts.append((t0 + (xfade if pts else 0.0), g0 * amount))
            pts.append((t1, g1 * amount))
        pts.insert(0, (0.0, pts[0][1]))
        pts.append((self.n / self.sr, pts[-1][1]))
        t = np.arange(self.n) / self.sr
        gdb = np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
        return 10 ** (gdb / 20.0)

    def mixdown(self, stems_dir=None, master=True, reverb_rt60=1.8, reverb_damp=6500, delay_beats=0.75, dynamics=1.0,
                mono_bass_hz=160.0, auto_mix=True):
        sc_hits = []
        for tn, h in self.hits.items():
            sc_hits += h
        sc_hits = sorted(sc_hits) if auto_mix else []
        dry = np.zeros((self.n, 2))
        rev_bus = np.zeros((self.n, 2))
        dly_bus = np.zeros((self.n, 2))
        stems = {}
        for name, tr in self.tracks.items():
            if not np.any(tr.buf):
                continue
            y = self._process(tr, sc_hits)
            stems[name] = y
            dry += y
            if tr.fx.get("reverb"):
                rev_bus += y * tr.fx["reverb"]
            if tr.fx.get("delay"):
                dly_bus += y * tr.fx["delay"]
        out = dry
        if np.any(rev_bus):
            out = out + dsp.reverb(rev_bus, 1.0, reverb_rt60, self.sr, damp=reverb_damp) - rev_bus * 0.4
        if np.any(dly_bus):
            d = 60.0 / self.bpm * delay_beats
            out = out + (dsp.delay(dly_bus, d, 0.38, 1.0, self.sr, 5000) - dly_bus * 0.5)
        if mono_bass_hz:
            out = dsp.mono_below(out, mono_bass_hz, self.sr)
        if master:
            out = self.master(out)
        curve = self.dynamics_curve(dynamics)  # applied AFTER mastering so the limiter cannot flatten the energy arc
        if curve is not None:
            out = out * curve[:, None]
        if stems_dir:
            import os
            os.makedirs(stems_dir, exist_ok=True)
            for name, y in stems.items():
                write_wav(os.path.join(stems_dir, f"{name}.wav"), dsp.normalize(y, -3.0) if np.any(y) else y, self.sr)
        return out

    def master(self, x, ceiling=-1.5, saturate=True):
        x = dsp.hp(x, 28, self.sr, 2)
        # light glue only: preserve the transient crest instead of squashing it
        x = dsp.compress(x, -16, 1.55, 0.025, 0.25, 0.6, self.sr)
        if saturate:
            # gentle even-harmonic bus saturation, blended so it thickens without fizz
            sat = dsp.asym_drive(x * 0.85, 1.25, 0.05)
            x = 0.78 * x + 0.22 * sat * (np.max(np.abs(x)) + 1e-9)
        x = np.tanh(x * 1.05) / np.tanh(1.05)
        x = dsp.limiter(x, ceiling, sr=self.sr)
        return dsp.normalize(x, ceiling)

    # ── beatmap ──
    def beatmap(self, energy=None):
        beat_s = 60.0 / self.bpm
        nbeats = self.bars * self.bpb
        beats = [round(self.t_of(0) + i * beat_s, 4) for i in range(nbeats)]
        downs = [round(b * self.bpb * beat_s, 4) for b in range(self.bars)]
        secs = [dict(name=n, start=round(sb * self.bpb * beat_s, 4), end=round((sb + nb) * self.bpb * beat_s, 4),
                     bars=nb) for n, sb, nb in self.sections]
        drops = [s["start"] for s in secs if s["name"] in ("drop", "chorus", "chase", "climax", "main")]
        return dict(schema="audio-forge/beatmap@1", source="compose", duration=round(self.dur_s, 3),
                    bpm=self.bpm, beats_per_bar=self.bpb, swing=self.swing, beats=beats, downbeats=downs,
                    sections=secs, drops=drops)


def write_wav(path, x, sr=SR, bits=16):
    x = np.clip(x, -1, 1)
    if bits == 16:
        d = (x * 32767).astype(np.int16)
    else:
        d = x.astype(np.float32)
    wavfile.write(path, sr, d)


def read_wav(path):
    sr, d = wavfile.read(path)
    if d.dtype == np.int16:
        d = d / 32768.0
    elif d.dtype == np.int32:
        d = d / 2147483648.0
    elif d.dtype == np.uint8:
        d = (d - 128) / 128.0
    return sr, d.astype(float)


GM_PROGRAM = dict(saw_bass=38, sine_sub=38, reese=39, sub_drop=38, wobble=39, pluck=84, lead_saw=81, lead_square=80, chip_tri=80,
                  pad=89, strings=48, brass=61, ep=4, bell=14, piano=0, organ=19, choir=52, guitar=30, guitar_mute=28, stab=62,
                  drone=94, music_box=10,
                  piano_m1=0, organ_rock=16, organ_pipe=19, bell_tubular=14, clock_bell=14, acid_303=38,
                  chip_lead=80, pulsing_bass=38, y2k_bass=38, showtime_sax=65, marimba=12, rave_stab=62,
                  orch_hit=55, rave_shout=53, heartbeat=116, siren_riser=119, clock_tick=114,
                  guitar_elec=30, guitar_pluck=25)
GM_DRUM = dict(kick=36, snare=38, clap=39, hat=42, ohat=46, ride=51, crash=49, tom=45, tom_hi=50, tom_lo=41, rim=37, perc=56,
               metal=56, impact=49)


def _vlq(n):
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def write_midi(path, song, ppq=480):
    """Standard MIDI file (format 1): tempo track + one track per instrument layer (drums on channel 10)."""
    import struct
    tpstep = ppq / song.spb
    tracks = {}
    for tr, inst, step, dur, m, vel in song.events:
        tracks.setdefault(tr, []).append((inst, step, dur, m, vel))
    chunks = []
    tempo = int(60_000_000 / song.bpm)
    meta = b"\x00\xff\x51\x03" + tempo.to_bytes(3, "big") + b"\x00\xff\x58\x04" + bytes([song.bpb, 2, 24, 8]) + b"\x00\xff\x2f\x00"
    chunks.append(b"MTrk" + struct.pack(">I", len(meta)) + meta)
    ch = 0
    for name, evs in tracks.items():
        is_drum = evs[0][0] == "drum"
        channel = 9 if is_drum else ch
        if not is_drum:
            ch = ch + 1 if ch + 1 != 9 else 10
        raw = []
        nm = name.encode()
        raw.append((0, b"\xff\x03" + bytes([len(nm)]) + nm))
        if not is_drum:
            raw.append((0, bytes([0xC0 | channel, GM_PROGRAM.get(evs[0][0], 0)])))
        for inst, step, dur, m, vel in evs:
            note = GM_DRUM.get(m, 38) if is_drum else int(m)
            on = int(round(song.t_of(step) / song.step_s * tpstep))
            off = on + max(int(dur * tpstep * 0.95), 10)
            v = int(np.clip(vel * 110, 1, 127))
            raw.append((on, bytes([0x90 | channel, note & 127, v])))
            raw.append((off, bytes([0x80 | channel, note & 127, 0])))
        raw.sort(key=lambda x: (x[0], x[1][0] & 0xF0 == 0x90))
        body, last = b"", 0
        for t, data in raw:
            body += _vlq(max(t - last, 0)) + data
            last = max(t, last)
        body += b"\x00\xff\x2f\x00"
        chunks.append(b"MTrk" + struct.pack(">I", len(body)) + body)
    with open(path, "wb") as f:
        f.write(b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), ppq))
        for c in chunks:
            f.write(c)

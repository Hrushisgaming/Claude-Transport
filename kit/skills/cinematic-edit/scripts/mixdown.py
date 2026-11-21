#!/usr/bin/env python3
"""mixdown.py - build the finished soundtrack for a plan.

  mixdown.py <plan.json> <outdir>      -> <outdir>/mix.wav (48 kHz stereo, before final loudness)

Layers: the source's own audio (time-remapped through speed ramps: slow-mo drops pitch, holds go quiet),
a music bed that ducks under the action and SUCKS OUT right before a big hit, per-event sfx
(riser -> impact, boom, tick), and a tension layer (drone + heartbeat that speeds up act by act).
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import *
import synth, devices

SR = 48000


def env_follow(x, win=0.05):
    m = np.abs(x).max(1) if x.ndim > 1 else np.abs(x); n = int(win * SR)
    c = np.cumsum(np.concatenate([[0], m])); e = (c[n:] - c[:-n]) / n
    return np.concatenate([e, np.full(n, e[-1] if len(e) else 0)])[:len(m)]


def add(mix, snd, t, gain=1.0):
    i = int(round(t * SR))
    if i >= len(mix) or i + len(snd) <= 0: return
    a = max(0, -i); b = min(len(snd), len(mix) - i)
    mix[i + a:i + b] += snd[a:b] * gain


def curve(n, pts):
    """piecewise-linear gain curve over n samples from [(time_s, gain)]"""
    ts = np.array([p[0] for p in pts]) * SR; gs = np.array([p[1] for p in pts])
    return np.interp(np.arange(n), ts, gs).astype(np.float32)


def _abs(plan, p):
    return p if os.path.isabs(p) else os.path.join(plan.get('_dir', '.'), p)


def build(plan, outdir):
    tm = TimeMap(plan); n = int(tm.D_out * SR); A = plan.get('audio', {}); mix = np.zeros((n, 2), np.float32)
    ref = db(-18)                                                       # stems sit around -18 dBFS RMS, then offsets
    # 1 - the source's own audio, remapped through the speed ramps
    src = read_audio(plan['source'], SR, 2, plan.get('start', 0), plan['dur'])
    game = np.zeros((n, 2), np.float32)
    if len(src):
        pos = (tm.to_src(np.arange(n) / SR) - tm.start) * SR
        for c in range(2): game[:, c] = np.interp(pos, np.arange(len(src)), src[:, c], right=0)
        r = np.sqrt(np.mean(src ** 2) + 1e-12); game *= ref / r * db(A.get('game_db', -4))
        spd = tm.speed_at_out(np.arange(n) / SR); game *= np.where(spd < 0.1, 0.0, np.where(spd < 0.6, 0.55, 1.0))[:, None]
    mix += game
    # 1b - an optional separate voice track (e.g. audio-forge subs2speech): plan.voice (path), voice_at (out seconds), audio.voice_db
    vbuf = None
    if plan.get('voice'):
        v = read_audio(_abs(plan, plan['voice']), SR, 2)
        if len(v):
            at = int(float(plan.get('voice_at', 0)) * SR); seg = v[:max(0, n - at)]
            vbuf = np.zeros((n, 2), np.float32); vbuf[at:at + len(seg)] = seg
            vbuf *= ref / (np.sqrt(np.mean(v ** 2)) + 1e-9) * db(A.get('voice_db', 0)); mix += vbuf
    # 2 - music bed: loop to length, duck under the game audio, suck out before big hits
    if plan.get('music'):
        m = read_audio(_abs(plan, plan['music']), SR, 2)
        m = m[int(float(plan.get('music_start', 0)) * SR):]                 # music_start = song time that plays at video time 0 (audio-forge song_at)
        if len(m) and len(m) < n: print(f"mixdown: WARNING the music ({len(m) / SR:.1f}s after music_start) is shorter than the video ({n / SR:.1f}s): it will loop", file=sys.stderr)
        if len(m):
            m = np.tile(m, (n // len(m) + 1, 1))[:n]; m *= ref / (np.sqrt(np.mean(m ** 2)) + 1e-9) * db(A.get('music_db', -13))
            e = env_follow(game); e = e / (np.percentile(e, 95) + 1e-9)
            duck = 1 - (1 - db(A.get('duck_db', -7))) * np.clip(e, 0, 1)
            pts = [(0, 0.0), (0.6, 1.0), (tm.D_out - 1.5, 1.0), (tm.D_out, 0.0)]
            g = curve(n, pts) * duck
            if vbuf is not None:                                           # the bed gets out of the way of the voice
                ev_v = env_follow(vbuf, 0.25); nz = ev_v[ev_v > 1e-4]; ev_v = ev_v / (np.percentile(nz, 90) + 1e-9) if len(nz) else ev_v
                g *= 1 - (1 - db(A.get('voice_duck_db', -12))) * np.clip(ev_v, 0, 1)
            for ev in plan.get('events', []):
                if ev.get('sfx') == 'impact':
                    to = float(tm.to_out(ev['t'])); i0, i1 = int(max(0, to - 0.28) * SR), int(min(tm.D_out, to + 0.04) * SR)
                    g[i0:i1] *= np.linspace(1, 0.0, i1 - i0) ** 2           # the bed drops out under the hit
                    j1 = int(min(tm.D_out, to + 0.5) * SR); g[i1:j1] *= np.linspace(0.0, 1, max(j1 - i1, 1))  # then swells back
            mix += m * g[:, None]
    # 3 - tension layer: drone + heartbeat that quickens act by act
    acts = sorted(plan.get('acts', []), key=lambda a: a['t'])
    if acts:
        dr = synth.get('drone'); loop = np.tile(dr, (n // len(dr) + 1, 1))[:n]
        pts = []
        for a in acts:
            to = float(tm.to_out(a['t'] + tm.start)); pts += [(max(0, to - 0.01), a.get('drone', 0.1)), (to + 1.5, a.get('drone', 0.1))]
        mix += loop * curve(n, pts)[:, None] * 0.6
        hb = synth.get('heartbeat')
        for i, a in enumerate(acts):
            if not a.get('heart_bpm'): continue
            t0 = float(tm.to_out(a['t'] + tm.start))
            t1 = float(tm.to_out(acts[i + 1]['t'] + tm.start)) if i + 1 < len(acts) else tm.D_out
            step = 60.0 / a['heart_bpm']; g = 0.22 + 0.4 * (i / max(1, len(acts) - 1)); t = t0
            while t < t1 - 0.2: add(mix, hb, t, g); t += step
    # 4 - per-event sfx; risers land exactly on the hit
    sg = db(A.get('sfx_db', -3)) * (db(-3) if A.get('mode') == 'voice' else 1.0)   # speech-led styles keep effects under the voice
    for ev in plan.get('events', []):
        to = float(tm.to_out(ev['t'])); s = float(ev.get('strength', 0.7)); g = sg * (0.55 + 0.45 * s)
        if ev.get('pre') == 'reverse': add(mix, synth.get('reverse'), to - 1.2, g * 0.7)
        if ev.get('riser', 0) > 0: add(mix, synth.get('riser', float(ev['riser'])), to - ev['riser'], g * 0.75)
        if ev.get('sfx'): add(mix, synth.get(ev['sfx']), to, g)
        if 'glitch' in ev.get('fx', []): add(mix, synth.get('glitch'), to + 0.01, g * 0.5)
        if ev.get('ramp'): add(mix, synth.get('sweepdown'), to - 0.3, g * 0.45)
    if plan.get('sfx_cues'):                                              # cue sheet: <video_seconds> <wav path> <gain>  (audio-forge sfx-cues / editor-v1 format)
        sheet = _abs(plan, plan['sfx_cues']); base = os.path.dirname(os.path.abspath(sheet))
        for line in open(sheet):
            line = line.strip()
            if not line or line.startswith('#'): continue
            parts = line.split(None, 2)
            if len(parts) < 2: continue
            wp = parts[1] if os.path.isabs(parts[1]) else os.path.join(base, parts[1])
            try: add(mix, read_audio(wp, SR, 2), float(parts[0]), sg * float(parts[2] if len(parts) > 2 else 0.8))
            except Exception as ex: print(f'mixdown: skipped cue {line!r}: {ex}', file=sys.stderr)
    for tt, name, gg in devices.all_cues(plan, tm):
        add(mix, synth.get(name), tt, sg * gg)
    for ov in plan.get('overlays', []):
        to = float(tm.to_out(ov['t'] + tm.start)); add(mix, synth.get('swish' if ov['type'] in ('title', 'lower_third') else 'tick'), to - 0.04, sg * 0.6)
    pk = np.abs(mix).max()
    if pk > 0.97: mix *= 0.97 / pk
    os.makedirs(outdir, exist_ok=True); write_wav(os.path.join(outdir, 'mix.wav'), mix)
    print(f'mixdown: {tm.D_out:.2f}s out ({tm.D_src:.2f}s source)  peak {np.abs(mix).max():.2f}  -> {outdir}/mix.wav')
    return tm


if __name__ == '__main__':
    plan = json.load(open(sys.argv[1])); plan.setdefault('_dir', os.path.dirname(os.path.abspath(sys.argv[1]))); build(plan, sys.argv[2])

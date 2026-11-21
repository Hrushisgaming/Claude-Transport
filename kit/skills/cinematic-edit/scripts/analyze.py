#!/usr/bin/env python3
"""analyze.py - find the moments worth hitting in ANY footage (no speech needed), and draft a plan.

  analyze.py <video> [--music track.mp3] [--out work] [--n 24] [--format 9:16] [--plan plan.json]

Finds: audio hits (spectral flux), motion spikes (frame difference), a music beat grid + BPM,
an intensity curve over time. Writes <out>/events.json and, with --plan, a DRAFT plan.json
(acts, events with fx + sfx, speed ramps on the biggest moments, visualizer) for you to edit.
"""
import argparse, json, os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import *
import styles as stylemod

SR = 22050; N = 1024; HOP = 256


def spectral_flux(x):
    w = np.hanning(N).astype(np.float32)
    n = 1 + (len(x) - N) // HOP
    if n < 4: return np.zeros(1, np.float32)
    idx = np.arange(N)[None, :] + HOP * np.arange(n)[:, None]
    mag = np.abs(np.fft.rfft(x[idx] * w, axis=1)); lm = np.log1p(mag * 20)
    return np.maximum(0, np.diff(lm, axis=0, prepend=lm[:1])).sum(1)


def pick_peaks(f, fps, k=2.2, min_gap=0.09, win=1.0):
    """local maxima above an adaptive threshold (moving median + k * MAD). -> [(t, strength 0..1)]"""
    if len(f) < 8: return []
    w = max(3, int(win * fps)); out = []; last = -9
    pad = np.pad(f, (w // 2, w // 2), mode='edge')
    for i in range(1, len(f) - 1):
        if f[i] < f[i - 1] or f[i] < f[i + 1]: continue
        seg = pad[i:i + w]; med = np.median(seg); mad = np.median(np.abs(seg - med)) + 1e-6
        if f[i] > med + k * 1.4826 * mad and i / fps - last >= min_gap:
            out.append((i / fps, float(f[i]))); last = i / fps
    if not out: return []
    mx = max(s for _, s in out)
    return [(round(t, 3), round(s / mx, 3)) for t, s in out]


def tempo(f, fps):
    """BPM + phase from autocorrelation of the flux envelope. -> (bpm, grid times) or (None, [])"""
    if len(f) < fps * 6: return None, []
    e = f - np.convolve(f, np.ones(int(fps * 0.5)) / int(fps * 0.5), 'same'); e = np.maximum(e, 0)
    ac = np.correlate(e, e, 'full')[len(e) - 1:]
    lo, hi = int(fps * 60 / 180), int(fps * 60 / 60)
    lag = lo + int(np.argmax(ac[lo:hi])); bpm = 60 * fps / lag
    while bpm < 80: bpm *= 2
    while bpm > 170: bpm /= 2
    per = 60 / bpm; best, ph = -1, 0
    for p in np.arange(0, per, 0.01):
        t = np.arange(p, len(f) / fps, per); s = e[np.clip((t * fps).astype(int), 0, len(e) - 1)].sum()
        if s > best: best, ph = s, p
    return round(bpm, 1), [round(float(t), 3) for t in np.arange(ph, len(f) / fps, per)]


def motion(path, dur, fps=10):
    r = subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', path, '-vf', f'fps={fps},scale=96:96,format=gray',
                        '-f', 'rawvideo', '-'], capture_output=True)
    fr = np.frombuffer(r.stdout, np.uint8); n = len(fr) // (96 * 96)
    if n < 3: return np.zeros(1, np.float32)
    fr = fr[:n * 96 * 96].reshape(n, 96, 96).astype(np.float32)
    return np.abs(np.diff(fr, axis=0)).mean((1, 2))


def smooth(x, n):
    return np.convolve(x, np.ones(n) / n, 'same') if len(x) >= n else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('--music'); ap.add_argument('--out', default='work')
    ap.add_argument('--n', type=int, default=None, help='max moments to keep (default 24, or from --style)')
    ap.add_argument('--gap', type=float, default=None, help='min seconds between moments (default 1.4, or from --style)')
    ap.add_argument('--style', help='preset: ' + ' | '.join(sorted(stylemod.STYLES)) + ' (see styles.py list)')
    ap.add_argument('--format', default=None); ap.add_argument('--plan'); ap.add_argument('--start', type=float, default=0)
    ap.add_argument('--dur', type=float)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    st = None
    if a.style: a.style, st = stylemod.get(a.style)
    info = probe(a.video); D = min(a.dur or 1e9, info['duration'] - a.start)
    fps_f = SR / HOP
    if a.format is None: a.format = st['format'] if st else '9:16'
    if a.n is None: a.n = max(8, int(round(2 * st['events']['per_min'] * (min(a.dur or 1e9, info['duration'] - a.start)) / 60.0))) if st and st['events']['per_min'] else (8 if st else 24)
    if a.gap is None: a.gap = st['events']['gap'] if st else 1.4

    x = read_audio(a.video, SR, 1, a.start, D)[:, 0] if info['has_audio'] else np.zeros(int(D * SR), np.float32)
    flux = spectral_flux(x); hits = pick_peaks(flux, fps_f)
    rms = np.array([np.sqrt(np.mean(x[i:i + SR // 2] ** 2) + 1e-12) for i in range(0, max(len(x) - SR // 2, 1), SR // 2)])
    mot = motion(a.video, D) if True else None
    mt = [(i / 10, float(v)) for i, v in enumerate(mot)]
    mz = (mot - np.median(mot)) / (np.median(np.abs(mot - np.median(mot))) * 1.4826 + 1e-6)
    spikes = [(round((i + 1) / 10, 2), float(min(1, z / 8))) for i, z in enumerate(mz) if z > 3.5 and i > 0 and mot[i] >= mot[i - 1]]

    bpm, grid = (None, [])
    if a.music:
        m = read_audio(a.music, SR, 1)[:, 0]; bpm, grid = tempo(spectral_flux(m), fps_f)
    elif st and st['events']['mode'] == 'beats' and len(x) > SR * 6:      # beat-led style, no separate track: the video's own audio is the music
        bpm, grid = tempo(flux, fps_f)
    # intensity per second 0..1: loudness + motion + hit density
    secs = int(np.ceil(D)); inten = np.zeros(secs)
    for i in range(secs):
        r_ = rms[min(len(rms) - 1, 2 * i):2 * i + 2].mean() if len(rms) else 0
        m_ = mot[min(len(mot) - 1, 10 * i):10 * i + 10].mean() if len(mot) else 0
        h_ = sum(1 for t, _ in hits if i <= t < i + 1)
        inten[i] = r_ / (rms.max() + 1e-9) * 0.4 + m_ / (mot.max() + 1e-9) * 0.35 + min(h_, 6) / 6 * 0.25
    inten = smooth(inten, 5); inten = (inten - inten.min()) / (np.ptp(inten) + 1e-9)

    # moments: audio hits and motion spikes merged, strongest first, spaced apart
    cand = [(t, 0.65 * s + 0.35 * float(inten[min(secs - 1, int(t))]), 'audio') for t, s in hits]
    cand += [(t, 0.55 * s + 0.45 * float(inten[min(secs - 1, int(t))]), 'motion') for t, s in spikes]
    cand.sort(key=lambda c: -c[1]); keep = []
    for t, s, k in cand:
        if all(abs(t - u) >= a.gap for u, _, _ in keep): keep.append((t, s, k))
        if len(keep) >= a.n: break
    keep.sort()
    mx = max([s for _, s, _ in keep] or [1])
    moments = [dict(t=round(t + 0.0, 3), strength=round(s / mx, 3), kind=k) for t, s, k in keep]
    ev = dict(source=a.video, start=a.start, duration=round(D, 2), bpm=bpm, beats=grid, hits=hits[:400],
              motion_spikes=spikes, intensity=[round(float(v), 3) for v in inten], moments=moments)
    json.dump(ev, open(os.path.join(a.out, 'events.json'), 'w'), indent=1)
    print(f'analyze: {D:.1f}s  {len(hits)} audio hits  {len(spikes)} motion spikes  {len(moments)} moments kept' +
          (f'  {bpm} BPM' if bpm else ''))
    for m_ in moments: print(f"  {m_['t']:7.2f}s  {m_['strength']:.2f}  {m_['kind']}")
    if a.plan:
        plan = stylemod.build_plan(a.style, ev, info, os.path.abspath(a.video), os.path.abspath(a.music) if a.music else None, a.format, a.start) if st else draft_plan(a, ev, info)
        json.dump(plan, open(a.plan, 'w'), indent=1); print('analyze: draft plan ->', a.plan + (f'  (style {a.style}: {st["pacing"]})' if st else ''))


ACTS = [('calm', 0.00, 'cold', 0.10, 55), ('the hunt', 0.14, 'teal', 0.30, 70), ('escalation', 0.42, 'teal', 0.55, 90),
        ('finale', 0.72, 'bleach', 0.85, 115), ('payoff', 0.92, 'warm', 0.25, 60)]


def draft_plan(a, ev, info):
    D = ev['duration']; moms = ev['moments']; order = sorted(range(len(moms)), key=lambda i: -moms[i]['strength'])
    big = set(order[:max(1, len(moms) // 8)]); ramp = set(order[:min(3, len(order))])
    events = []
    for i, m in enumerate(moms):
        s = m['strength']
        if i in big:
            e = dict(t=m['t'], strength=s, fx=['punch', 'shake', 'flash', 'chroma'], sfx='impact', riser=1.2)
            if i in ramp and m['t'] > 6: e['ramp'] = dict(speed=0.3, dur=1.0)
        elif s > 0.45:
            e = dict(t=m['t'], strength=s, fx=['punch', 'shake'], sfx='boom', riser=0.0)
        else:
            e = dict(t=m['t'], strength=s, fx=['punch'], sfx='tick', riser=0.0)
        events.append(e)
    acts = [dict(name=n, t=round(f * D, 2), look=lk, drone=dr, heart_bpm=hb) for n, f, lk, dr, hb in ACTS]
    return dict(source=os.path.abspath(a.video), music=os.path.abspath(a.music) if a.music else None, format=a.format, fps=30,
                start=a.start, dur=round(D, 2), reframe=dict(mode='cover', x=0.5, bg='blur'),
                look=dict(grain=0.05, vignette=0.45, letterbox=0.0, bloom=0.25), acts=acts, events=events, overlays=[],
                visualizer=dict(style='bars', pos='bottom', color='#ffffff', opacity=0.8),
                audio=dict(game_db=-4, music_db=-13, duck_db=-7, sfx_db=-3, lufs=-14, music_beat_sync=bool(a.music)))


if __name__ == '__main__':
    main()

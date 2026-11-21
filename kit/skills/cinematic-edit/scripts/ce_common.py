"""ce_common.py - shared helpers for cinematic-edit. Needs only numpy, opencv, pillow, ffmpeg."""
import json, os, subprocess, sys
import numpy as np

FORMATS = {'9:16': (1080, 1920), '16:9': (1920, 1080), '1:1': (1080, 1080), '4:5': (1080, 1350)}


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def probe(path):
    """-> dict(duration, width, height, fps, has_audio)"""
    o = json.loads(sh(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]).stdout)
    v = next(s for s in o['streams'] if s['codec_type'] == 'video')
    n, d = (v.get('avg_frame_rate') or '30/1').split('/')
    fps = float(n) / float(d) if float(d) else 30.0
    return dict(duration=float(o['format']['duration']), width=int(v['width']), height=int(v['height']),
                fps=fps, has_audio=any(s['codec_type'] == 'audio' for s in o['streams']))


def read_audio(path, sr=48000, ch=2, ss=0.0, dur=None):
    """decode any file's first audio stream to float32 array (n, ch); silence if none."""
    cmd = ['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{ss:.4f}']
    if dur: cmd += ['-t', f'{dur:.4f}']
    cmd += ['-i', path, '-map', '0:a:0', '-ac', str(ch), '-ar', str(sr), '-f', 'f32le', '-']
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode or not r.stdout:
        return np.zeros((0, ch), np.float32)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, ch).copy()


def write_wav(path, x, sr=48000):
    x = np.clip(x.astype(np.float32), -1.0, 1.0)
    p = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(sr), '-ac', str(x.shape[1]),
                          '-i', '-', '-c:a', 'pcm_f32le', path], stdin=subprocess.PIPE)
    p.communicate(x.tobytes())
    if p.returncode: raise RuntimeError('ffmpeg could not write ' + path)


def db(x):  return 10 ** (x / 20.0)


def ease(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def load_json(p, default=None):
    return json.load(open(p)) if os.path.exists(p) else default


def skill_dir():
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


class TimeMap:
    """Speed ramps / holds. Plan times are SOURCE seconds; the edit runs on OUTPUT seconds.
    ramp: {speed, dur} on an event at t -> window starts `lead` before the event. speed<=0.1 = hold."""
    DT = 1 / 480

    def __init__(self, plan):
        self.start = float(plan.get('start', 0)); D = float(plan['dur'])
        g = np.arange(0, D + self.DT, self.DT); sp = np.ones_like(g); self.holds = []
        for e in plan.get('events', []):
            r = e.get('ramp')
            if not r: continue
            d = float(r.get('dur', 1.0)); lead = float(r.get('lead', 0.35 * d)); s = float(r.get('speed', 0.3))
            a = e['t'] - self.start - lead; b = a + d; k = min(0.15, d / 3)
            prof = np.where((g >= a) & (g <= b), 1.0, 0.0)
            prof = np.minimum(prof, np.minimum((g - a) / k, (b - g) / k).clip(0, 1))
            sp = np.minimum(sp, 1 - (1 - max(s, 0.03)) * ease(prof))
            if s <= 0.1: self.holds.append((a, b))
        self.speed_src = sp; self.g = g
        self.out = np.concatenate([[0], np.cumsum(self.DT / sp[:-1])])
        self.D_src = D; self.D_out = float(self.out[-1])

    def to_out(self, ts):  return np.interp(np.asarray(ts) - self.start, self.g, self.out)
    def to_src(self, to):  return np.interp(to, self.out, self.g) + self.start
    def speed_at_out(self, to):  return np.interp(np.asarray(to), self.out, self.speed_src)


def hex_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

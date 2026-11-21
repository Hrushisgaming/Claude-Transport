#!/usr/bin/env python3
"""render.py - plan.json -> finished cinematic video (any aspect: 9:16, 16:9, 1:1, 4:5).

  render.py <plan.json> <outdir> [--preview] [--range a,b] [--out file.mp4] [--png]

  --preview   half-size, fast encode: check the plan before the full render
  --range a,b render only output seconds a..b (with --png: write a still every 0.25 s instead)
Pipeline: mixdown (audio, with speed ramps) -> decode source -> per frame: reframe, zoom/shake/chroma/
glitch/flash on each event, act-by-act grade, bloom, vignette, grain, letterbox, audio-reactive
visualizer, text overlays -> x264 + the mix, loudness-normalised (-14 LUFS by default).
"""
import argparse, json, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import *
import mixdown, looks, devices, captions as capmod, plancheck, follow as followmod
from looks import LOOKS, lerp_look, apply_look, Halftone

FONTS = ['/usr/share/fonts/opentype/inter/Inter-Bold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
         '/Library/Fonts/Arial Bold.ttf', '/System/Library/Fonts/Helvetica.ttc', 'C:/Windows/Fonts/arialbd.ttf']


class Grader:
    def __init__(self, plan, tm, W, H):
        self.acts = sorted(plan.get('acts', []), key=lambda a: a['t']); self.tm = tm
        self.times = [float(tm.to_out(a['t'] + tm.start)) for a in self.acts]
        self.looks = [LOOKS.get(a.get('look', 'natural'), LOOKS['natural']) for a in self.acts]
        L = plan.get('look', {}); self.grain = L.get('grain', 0.05); self.vig = L.get('vignette', 0.45)
        self.bloom = L.get('bloom', 0.25); self.bars = L.get('letterbox', 0.0); self.beat_zoom = L.get('beat_zoom', 0.015)
        self.W, self.H = W, H
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vmask = np.clip((r - 0.45) / 0.95, 0, 1)[..., None] ** 1.6
        rg = np.random.default_rng(3); self.tiles = [rg.standard_normal((H // 2, W // 2)).astype(np.float32) for _ in range(5)]

    def look_at(self, to):
        if not self.acts: return LOOKS['natural']
        i = max([k for k, t in enumerate(self.times) if t <= to] or [0]); cur = self.looks[i]
        if i > 0 and to - self.times[i] < 1.2: return lerp_look(self.looks[i - 1], cur, ease((to - self.times[i]) / 1.2))
        return cur

    def act_at(self, to):
        if not self.acts: return {}
        return self.acts[max([k for k, t in enumerate(self.times) if t <= to] or [0])]

    def __call__(self, f8, to, i, slow, bass):
        W, H = self.W, self.H; lk = self.look_at(to)
        ht = float(self.act_at(to).get('halftone', 0))
        if ht > 0:
            if not hasattr(self, 'ht'): self.ht = Halftone(W, H)
            f8 = self.ht(f8, ht)
        f = apply_look(f8, lk, 1.5 if slow else 1.0)
        if self.bloom > 0:
            s = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA); s = np.maximum(s - 0.62, 0)
            s = cv2.GaussianBlur(s, (0, 0), max(W, H) / 90); f += cv2.resize(s, (W, H)) * self.bloom * (1.6 if slow else 1.0)
        v = self.vig * (1.25 if slow else 1.0); f *= 1 - v * self.vmask
        if self.grain > 0:
            g = cv2.resize(self.tiles[i % 5], (W, H), interpolation=cv2.INTER_LINEAR); f += (g * self.grain * 0.5)[..., None]
        out = np.clip(f * 255, 0, 255).astype(np.uint8)
        if self.bars > 0:
            b = int(H * self.bars); out[:b] = 0; out[H - b:] = 0
        return out


def reframe(src, W, H, mode, fx, fy, z, dx, dy, bgcache):
    """cover or fit the source into WxH with zoom z and shake offset (dx, dy) in output px."""
    h0, w0 = src.shape[:2]
    if mode == 'fit':
        s = min(W / w0, H / h0) * z
        if 'bg' not in bgcache or bgcache['k'] != id(src):
            sc = max(W / w0, H / h0); small = cv2.resize(src, (max(8, int(w0 * sc / 10)), max(8, int(h0 * sc / 10))))
            small = cv2.GaussianBlur(small, (0, 0), 3); big = cv2.resize(small, (int(w0 * sc), int(h0 * sc)))
            y0, x0 = (big.shape[0] - H) // 2, (big.shape[1] - W) // 2
            bgcache['bg'] = (big[y0:y0 + H, x0:x0 + W] * 0.45).astype(np.uint8); bgcache['k'] = id(src)
        M = np.float32([[s, 0, W / 2 - w0 * s / 2 + dx], [0, s, H / 2 - h0 * s / 2 + dy]])
        fg = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        m = cv2.warpAffine(np.full((h0, w0), 255, np.uint8), M, (W, H), flags=cv2.INTER_LINEAR)
        m = m[..., None].astype(np.float32) / 255
        return (fg * m + bgcache['bg'] * (1 - m)).astype(np.uint8)
    s = max(W / w0, H / h0) * z; cw, ch = W / s, H / s
    cx = min(max(fx * w0, cw / 2), w0 - cw / 2) if w0 > cw else w0 / 2; cy = min(max(fy * h0, ch / 2), h0 - ch / 2) if h0 > ch else h0 / 2
    M = np.float32([[s, 0, W / 2 - cx * s + dx], [0, s, H / 2 - cy * s + dy]])
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def chroma(f, px):
    px = int(round(px))
    if px < 1: return f
    o = f.copy(); o[:, px:, 2] = f[:, :-px, 2]; o[:, :-px, 0] = f[:, px:, 0]; return o


def glitch(f, i, amt, u):
    r = np.random.default_rng(i * 7 + 1); o = f.copy(); H = f.shape[0]
    for _ in range(7):
        y = int(r.integers(0, H - 8)); h = int(r.integers(6, max(7, H // 18))); sx = int(r.integers(-1, 2) * r.integers(20, 70) * amt * u)
        o[y:y + h] = np.roll(f[y:y + h], sx, axis=1)
    return o


class Spectrum:
    """per-frame band energies of the FINAL mix, for the reactive visualizer + bass pulse."""
    def __init__(self, mixpath, fps, nb=48, ss=0.0):
        x = read_audio(mixpath, 48000, 1, ss)[:, 0]; self.fps, self.nb, self.x = fps, nb, x
        self.edges = np.geomspace(45, 12000, nb + 1); self.prev = np.zeros(nb); self.w = np.hanning(2048)
        self.freqs = np.fft.rfftfreq(2048, 1 / 48000)
        self.band = [(self.freqs >= self.edges[k]) & (self.freqs < self.edges[k + 1]) for k in range(nb)]
        self.ref = np.percentile(np.abs(x), 99.5) + 1e-6

    def at(self, i):
        c = int(i / self.fps * 48000); seg = self.x[max(0, c - 1024):c + 1024]
        if len(seg) < 2048: seg = np.pad(seg, (0, 2048 - len(seg)))
        m = np.abs(np.fft.rfft(seg * self.w)) / (1024 * self.ref)
        v = np.array([m[b].mean() if b.any() else 0 for b in self.band]); v = np.clip(np.log1p(v * 40) / np.log1p(40) * 1.5, 0, 1)
        self.prev = np.where(v > self.prev, v, self.prev * 0.80 + v * 0.20); return self.prev


def draw_vis(f, spec, cfg, u):
    W, H = f.shape[1], f.shape[0]; col = hex_rgb(cfg.get('color', '#ffffff'))[::-1]; op = cfg.get('opacity', 0.8)
    pos = cfg.get('pos', 'bottom'); nb = len(spec); o = f.copy(); style = cfg.get('style', 'bars')
    if style == 'ring':
        cx, cy = W // 2, int(H * {'top': 0.2, 'center': 0.5, 'bottom': 0.8}[pos]); r0 = int(W * 0.17)
        for k in range(nb * 2):
            a = 2 * np.pi * k / (nb * 2) - np.pi / 2; v = spec[k % nb if k < nb else nb - 1 - (k - nb)]; r1 = r0 + int(v * W * 0.12)
            cv2.line(o, (int(cx + r0 * np.cos(a)), int(cy + r0 * np.sin(a))), (int(cx + r1 * np.cos(a)), int(cy + r1 * np.sin(a))), col, max(2, int(5 * u)), cv2.LINE_AA)
    elif style == 'line':
        y0 = int(H * {'top': 0.1, 'center': 0.5, 'bottom': 0.9}[pos]); xs = np.linspace(W * 0.06, W * 0.94, nb)
        pts = np.stack([xs, y0 - spec * H * 0.09 * np.where(np.arange(nb) % 2, 1, -1)], 1).astype(np.int32)
        cv2.polylines(o, [pts.reshape(-1, 1, 2)], False, col, max(2, int(4 * u)), cv2.LINE_AA)
    else:
        base = int(H * {'top': 0.12, 'center': 0.55, 'bottom': 0.92}[pos]); mh = H * 0.13; bw = W * 0.88 / nb; x0 = W * 0.06
        for k in range(nb):
            h = max(2, int(spec[k] * mh)); xa = int(x0 + k * bw)
            cv2.rectangle(o, (xa, base - h), (int(xa + bw * 0.62), base), col, -1)
            if cfg.get('mirror', True): cv2.rectangle(o, (xa, base), (int(xa + bw * 0.62), base + h // 3), col, -1)
    return cv2.addWeighted(o, op, f, 1 - op, 0)


class Overlay:
    def __init__(self, ov, tm, W, H, font):
        self.ov, self.W, self.H = ov, W, H; self.t0 = float(tm.to_out(ov['t'] + tm.start)); self.dur = float(ov.get('dur', 2.0))
        u = min(W, H) / 1080; kind = ov['type']; txt = ov['text']
        size = int({'title': 150, 'counter': 62, 'lower_third': 64, 'caption': 58}[kind] * u * ov.get('scale', 1.0))
        fnt = ImageFont.truetype(font, size); pad = int(size * 0.35); st = max(2, size // 14)
        tmp = Image.new('RGBA', (10, 10)); bb = ImageDraw.Draw(tmp).textbbox((0, 0), txt, font=fnt, stroke_width=st)
        w, h = int(bb[2] - bb[0] + 2 * pad), int(bb[3] - bb[1] + 2 * pad)
        if w > W * 0.92:                                           # wrap long text
            words = txt.split(); lines = ['']; 
            for wd in words:
                t2 = (lines[-1] + ' ' + wd).strip()
                if ImageDraw.Draw(tmp).textlength(t2, font=fnt) < W * 0.8: lines[-1] = t2
                else: lines.append(wd)
            txt = '\n'.join(lines); bb = ImageDraw.Draw(tmp).multiline_textbbox((0, 0), txt, font=fnt, stroke_width=st, align='center')
            w, h = int(bb[2] - bb[0] + 2 * pad), int(bb[3] - bb[1] + 2 * pad)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        col = hex_rgb(ov.get('color', '#ffffff')) + (255,)
        if kind in ('counter', 'lower_third'): d.rounded_rectangle((0, 0, w - 1, h - 1), int(size * 0.3), fill=(0, 0, 0, 150))
        d.multiline_text((pad - bb[0], pad - bb[1]), txt, font=fnt, fill=col, stroke_width=st, stroke_fill=(0, 0, 0, 255), align='center')
        a = np.array(im); self.rgb = cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2BGR); self.a = a[..., 3].astype(np.float32) / 255
        pos = ov.get('pos', {'title': 'center', 'counter': 'top', 'lower_third': 'lowerleft', 'caption': 'lower'}[kind]); self.pos = pos

    def apply(self, f, to):
        dt = to - self.t0
        if dt < 0 or dt > self.dur: return f
        k = ease(dt / 0.18); out = ease((self.dur - dt) / 0.25); alpha = min(k, out)
        sc = (1.25 - 0.25 * k) if self.ov['type'] in ('title', 'counter') else 1.0
        rgb, a = self.rgb, self.a
        if abs(sc - 1) > 0.01:
            rgb = cv2.resize(rgb, None, fx=sc, fy=sc); a = cv2.resize(a, None, fx=sc, fy=sc)
        h, w = a.shape; W, H = self.W, self.H
        x = {'lowerleft': int(W * 0.06)}.get(self.pos, (W - w) // 2)
        y = {'center': (H - h) // 2, 'top': int(H * 0.09), 'lower': int(H * 0.72), 'lowerleft': int(H * 0.70), 'bottom': int(H * 0.82)}.get(self.pos, (H - h) // 2)
        if self.ov['type'] == 'lower_third': x += int((1 - k) * -w * 0.3)
        x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
        if x1 <= x0 or y1 <= y0: return f
        sa = a[y0 - y:y1 - y, x0 - x:x1 - x] * alpha; sr = rgb[y0 - y:y1 - y, x0 - x:x1 - x]
        roi = f[y0:y1, x0:x1].astype(np.float32); f[y0:y1, x0:x1] = (roi * (1 - sa[..., None]) + sr * sa[..., None]).astype(np.uint8)
        return f


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('outdir')
    ap.add_argument('--preview', action='store_true'); ap.add_argument('--range'); ap.add_argument('--out'); ap.add_argument('--png', action='store_true'); ap.add_argument('--force-rights', action='store_true')
    a = ap.parse_args(); plan = json.load(open(a.plan)); plan['_dir'] = os.path.dirname(os.path.abspath(a.plan)); os.makedirs(a.outdir, exist_ok=True)
    plancheck.gate(plan, strict=not (a.preview or a.png or a.force_rights))
    fps = int(plan.get('fps', 30)); tm = mixdown.build(plan, a.outdir); mixp = os.path.join(a.outdir, 'mix.wav')
    W, H = FORMATS.get(plan.get('format', '9:16'), (1080, 1920))
    if a.preview: W, H = W // 2, H // 2
    u = min(W, H) / 1080; r0, r1 = (0.0, tm.D_out)
    if a.range: r0, r1 = [float(v) for v in a.range.split(',')]; r1 = min(r1, tm.D_out)
    n0, n1 = int(r0 * fps), int(r1 * fps); step = 8 if (a.png and a.range) else 1
    font = plan.get('font') or next((f for f in FONTS if os.path.exists(f)), None)
    if not font and plan.get('overlays'): sys.exit('render: no font found, set "font" in the plan')
    G = Grader(plan, tm, W, H); spec = Spectrum(mixp, fps, ss=0.0); vis = plan.get('visualizer')
    devs = devices.build(plan, tm, W, H, fps); caps = capmod.Captions(plan['captions'], tm, W, H, os.path.dirname(os.path.abspath(a.plan))) if plan.get('captions') else None
    ovs = [Overlay(o, tm, W, H, font) for o in plan.get('overlays', [])]
    evs = [dict(to=float(tm.to_out(e['t'])), s=float(e.get('strength', 0.7)), fx=e.get('fx', [])) for e in plan.get('events', [])]
    rf = plan.get('reframe', {}); mode = rf.get('mode', 'cover'); fx_ = rf.get('x', 0.5); fy_ = rf.get('y', 0.5)
    fol = None
    if rf.get('follow') and mode == 'cover':
        cfg = rf['follow'] if isinstance(rf['follow'], dict) else {}; fol = followmod.Follower(followmod.track(plan['source'], plan.get('start', 0), plan['dur'], **cfg))
    ss_src = float(tm.to_src(n0 / fps))                                           # absolute source seconds
    dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{ss_src:.4f}', '-i', plan['source'], '-vf', f'fps={fps}',
                            '-an', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    info = probe(plan['source']); w0, h0 = info['width'], info['height']; fsz = w0 * h0 * 3
    enc = None
    if not a.png:
        out = a.out or os.path.join(a.outdir, 'final_preview.mp4' if a.preview else 'final.mp4'); lufs = plan.get('audio', {}).get('lufs', -14)
        enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(fps),
                                '-i', '-', '-ss', f'{r0:.4f}', '-t', f'{r1 - r0:.4f}', '-i', mixp, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264',
                                '-preset', 'veryfast' if a.preview else 'medium', '-crf', '27' if a.preview else '17', '-pix_fmt', 'yuv420p',
                                '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-af', f'loudnorm=I={lufs}:TP=-1.0:LRA=11',
                                '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', '-shortest', out], stdin=subprocess.PIPE)
    cur, cur_idx, cache = None, -1, {}
    for i in range(n0, n1, step):
        to = i / fps; want = int(round((float(tm.to_src(to)) - ss_src) * fps))
        while cur_idx < want:
            b = dec.stdout.read(fsz)
            if len(b) < fsz: break
            cur = np.frombuffer(b, np.uint8).reshape(h0, w0, 3); cur_idx += 1
        if cur is None: break
        sp = spec.at(i); bass = float(sp[:8].mean()); z = 1.0 + G.beat_zoom * bass; dx = dy = 0.0; flash = 0.0; ch_px = 0.0; gl = 0.0
        for e in evs:
            dt = to - e['to']
            if -0.2 <= dt < 0 and 'punch' in e['fx']: z += 0.03 * e['s'] * (1 + dt / 0.2)               # suction before the hit
            if 0 <= dt < 0.7:
                if 'punch' in e['fx']: z += 0.15 * e['s'] * np.exp(-dt / 0.14)
                if 'shake' in e['fx']:
                    amp = 26 * u * e['s'] * np.exp(-dt / 0.13); dx += amp * np.sin(i * 37.1); dy += amp * np.cos(i * 53.7)
                if 'flash' in e['fx'] and dt < 0.11: flash = max(flash, 0.85 * e['s'] * (1 - dt / 0.11))
                if 'chroma' in e['fx']: ch_px = max(ch_px, 16 * u * e['s'] * np.exp(-dt / 0.2))
                if 'glitch' in e['fx'] and dt < 0.16: gl = max(gl, e['s'])
        fxx, fyy = fol.at(float(tm.to_src(to))) if fol else (fx_, fy_)
        fr = reframe(cur, W, H, mode, fxx, fyy, z, dx, dy, cache)
        if ch_px: fr = chroma(fr, ch_px)
        if gl: fr = glitch(fr, i, gl, u)
        for dv in devs:
            if dv.active(to): fr = dv.frame(to, fr)
        fr = fr if G.act_at(to).get('raw') else G(fr, to, i, tm.speed_at_out(to) < 0.6, bass)
        for dv in devs:
            rl = getattr(dv, 'raw_layer', None)
            if rl is not None and dv.active(to):
                m = (rl[1].astype(np.float32) / 255)[..., None]; fr = (fr * (1 - m) + rl[0] * m).astype(np.uint8); dv.raw_layer = None
        if vis: fr = draw_vis(fr, sp, vis, u)
        if caps: fr = caps.apply(fr, to)
        for o in ovs: fr = o.apply(fr, to)
        if flash: fr = cv2.addWeighted(fr, 1 - flash, np.full_like(fr, 255), flash, 0)
        if a.png: cv2.imwrite(os.path.join(a.outdir, f'frame_{to:06.2f}.png'), fr)
        else: enc.stdin.write(fr.tobytes())
        if (i - n0) % 150 == 0: print(f'  render {i - n0}/{n1 - n0} frames', file=sys.stderr, flush=True)
    dec.kill()
    if enc: enc.stdin.close(); enc.wait(); print(f'render: {out}  {r1 - r0:.1f}s  {W}x{H}')


if __name__ == '__main__':
    main()

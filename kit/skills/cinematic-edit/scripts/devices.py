"""devices.py - editor-v1's signature moves, rebuilt natively (numpy/OpenCV, no browser, no HyperFrames).

Plan entry: {"type": ..., "t": SOURCE seconds, "dur": output seconds, "images": [path | {"path":..,"treat":..}], ...}
  tile_reveal   a chapter/world swap: a 3x3 grid of panes flash white then show the picture, one pane per frame, a click each
  strobe        2-3 frame images, ideally SHAPE-MATCHED (all circles, all banknotes), a click each
  wall3d        a perspective wall of cards the camera sweeps across (silent)
  pop_collage   cards pop in one every `every` s (default 0.23), a click each
  cutout_world  the speaker (matte) stays while the world behind changes, a huge word BEHIND the head (mega)
Each device = cues() for the mixer + frame() for the renderer.
"""
import os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from ce_common import ease, hex_rgb
import looks

_FONTS = ['/usr/share/fonts/opentype/inter/Inter-Black.otf', '/usr/share/fonts/opentype/inter/Inter-Bold.otf',
          '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/System/Library/Fonts/Helvetica.ttc', 'C:/Windows/Fonts/arialbd.ttf']
_img_cache = {}


def find_font(pref=None):
    return next((f for f in ([pref] if pref else []) + _FONTS if f and os.path.exists(f)), None)


def load_image(spec, W, H, default_treat=None):
    path, treat = (spec, default_treat) if isinstance(spec, str) else (spec['path'], spec.get('treat', default_treat))
    key = (path, W, H, treat)
    if key not in _img_cache:
        im = cv2.imread(path)
        if im is None: raise FileNotFoundError(f'device image not found/readable: {path}')
        _img_cache[key] = looks.treat_image(im, W, H, treat)
    return _img_cache[key]


class Dev:
    kind = ''
    def __init__(s, d, tm, W, H, fps):
        s.d, s.tm, s.W, s.H, s.fps = d, tm, W, H, fps; s.u = min(W, H) / 1080
        s.t0 = float(tm.to_out(d['t'] + tm.start)); s.dur = float(d.get('dur', s.default_dur()))
    def default_dur(s): return 1.5
    def active(s, to): return s.t0 <= to < s.t0 + s.dur
    def cues(s): return []
    def img(s, k): return load_image(s.d['images'][k % len(s.d['images'])], s.W, s.H, s.d.get('treat'))
    def frame(s, to, base): raise NotImplementedError


class TileReveal(Dev):
    kind = 'tile_reveal'
    def __init__(s, *a):
        super().__init__(*a); g = int(s.d.get('grid', 3)); s.g = g
        s.order = np.random.default_rng(int(s.d.get('seed', 3))).permutation(g * g)        # pane k is revealed at frame rank[k]
        s.rank = np.empty(g * g, int); s.rank[s.order] = np.arange(g * g)
    def cues(s): return [(s.t0 + k / s.fps, 'tick', 0.35) for k in range(s.g * s.g)]
    def frame(s, to, base):
        j = int((to - s.t0) * s.fps + 1e-6); pic = s.img(0); out = base.copy(); H, W = s.H, s.W; g = s.g
        push = 1 + float(s.d.get('push', 0.04)) * (to - s.t0)
        if push > 1.001:
            M = np.float32([[push, 0, W / 2 * (1 - push)], [0, push, H / 2 * (1 - push)]]); pic = cv2.warpAffine(pic, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        for k in range(g * g):
            r, c = divmod(k, g); y0, y1, x0, x1 = r * H // g, (r + 1) * H // g, c * W // g, (c + 1) * W // g
            if s.rank[k] < j: out[y0:y1, x0:x1] = pic[y0:y1, x0:x1]
            elif s.rank[k] == j: out[y0:y1, x0:x1] = 255
        return out


class Strobe(Dev):
    kind = 'strobe'
    def default_dur(s): return len(s.d['images']) * int(s.d.get('per', 3)) / s.fps
    def cues(s):
        per = int(s.d.get('per', 3)); return [(s.t0 + k * per / s.fps, 'tick', 0.45) for k in range(len(s.d['images']))]
    def frame(s, to, base):
        per = int(s.d.get('per', 3)); k = min(int((to - s.t0) * s.fps / per + 1e-6), len(s.d['images']) - 1); return s.img(k).copy()


class Wall3D(Dev):
    kind = 'wall3d'
    def default_dur(s): return 1.8
    def _canvas(s):
        if hasattr(s, 'cv'): return s.cv
        cols, rows = int(s.d.get('cols', 4)), int(s.d.get('rows', 3)); cw, ch = 480, 300; gap = 24
        cv = np.full((rows * (ch + gap) + gap, cols * (cw + gap) + gap, 3), 14, np.uint8)
        for k in range(cols * rows):
            r, c = divmod(k, cols); tile = looks.cover(load_image(s.d['images'][k % len(s.d['images'])], 960, 600, s.d.get('treat')), cw, ch)
            cv[gap + r * (ch + gap):gap + r * (ch + gap) + ch, gap + c * (cw + gap):gap + c * (cw + gap) + cw] = tile
        s.cv = cv; return cv
    def frame(s, to, base):
        cv = s._canvas(); h, w = cv.shape[:2]; p = float(ease((to - s.t0) / s.dur)); W, H = s.W, s.H
        scale = 1.9 * W / w; hw, hh = w * scale / 2, h * scale / 2
        yaw = np.radians(-48 + 36 * p); pit = np.radians(10); f = W * 1.1; z0 = W * 1.25; tx = W * (0.55 - 1.1 * p)
        pts = []
        for x, y in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)):
            X = x * np.cos(yaw); Z = x * np.sin(yaw); Y = y * np.cos(pit) - Z * np.sin(pit); Z = Z * np.cos(pit) + y * np.sin(pit)
            pts.append([f * (X + tx) / (Z + z0) + W / 2, f * Y / (Z + z0) + H / 2])
        M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(pts))
        out = cv2.warpPerspective(cv, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(14, 14, 14))
        mv = abs(float(ease((to - s.t0 + 0.03) / s.dur)) - p) * s.fps * s.dur
        return cv2.GaussianBlur(out, (0, 0), max(0.1, mv * 6)) if mv * 6 > 0.6 else out


class PopCollage(Dev):
    kind = 'pop_collage'
    def __init__(s, *a):
        super().__init__(*a); n = len(s.d['images']); s.every = float(s.d.get('every', 0.23)); r = np.random.default_rng(int(s.d.get('seed', 5)))
        s.rot = r.uniform(-5, 5, n); cols = 3; s.pos = [((0.2 + 0.3 * (k % cols)) * s.W + r.uniform(-0.04, 0.04) * s.W, (0.28 + 0.2 * (k // cols % 3)) * s.H + r.uniform(-0.03, 0.03) * s.H) for k in range(n)]
    def default_dur(s): return len(s.d['images']) * float(s.d.get('every', 0.23)) + 0.9
    def cues(s): return [(s.t0 + k * s.every, 'tick', 0.45) for k in range(len(s.d['images']))]
    def frame(s, to, base):
        out = (base.astype(np.float32) * 0.3).astype(np.uint8); cw = int(s.W * float(s.d.get('card', 0.5)))
        for k in range(len(s.d['images'])):
            dt = to - (s.t0 + k * s.every)
            if dt < 0: continue
            card = looks.cover(load_image(s.d['images'][k], 960, 720, s.d.get('treat')), cw, int(cw * 0.75))
            e = ease(dt / 0.18); sc = (0.55 + 0.45 * e) * (1 + 0.08 * np.sin(np.pi * min(1, dt / 0.18)))
            h, w = card.shape[:2]; M = cv2.getRotationMatrix2D((w / 2, h / 2), s.rot[k], sc); M[:, 2] += (s.pos[k][0] - w / 2, s.pos[k][1] - h / 2)
            warped = cv2.warpAffine(card, M, (s.W, s.H)); mask = cv2.warpAffine(np.full((h, w), 255, np.uint8), M, (s.W, s.H))
            sh = cv2.GaussianBlur(mask, (0, 0), 14 * s.u); sh = np.roll(sh, int(10 * s.u), axis=0)
            out = (out.astype(np.float32) * (1 - 0.45 * (sh / 255.0)[..., None])).astype(np.uint8)
            m = (mask / 255.0)[..., None]; out = (out * (1 - m) + warped * m).astype(np.uint8)
            if dt < 1 / s.fps: out[mask > 0] = 255                       # a white box one frame before each card, as in the references
        return out


class CutoutWorld(Dev):
    """needs an alpha matte video from matte.py (gray mp4, 1 = speaker). The speaker plate is the live source frame."""
    kind = 'cutout_world'
    def default_dur(s): return 3.0
    def __init__(s, *a):
        super().__init__(*a); s.every = float(s.d.get('every', 0.9)); s.dec = None; s.last = -99; s.cur = None
    def cues(s): return [(s.t0 + k * s.every, 'tick', 0.45) for k in range(1, int(s.dur / s.every) + 1)]
    def _alpha(s, to):
        ts = float(s.tm.to_src(to)); idx = int(round((ts - float(s.d.get('matte_start', s.d['t']))) * s.fps))
        if s.dec is None or idx != s.last + 1:
            if s.dec: s.dec.kill()
            s.dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{max(0, idx) / s.fps:.4f}', '-i', s.d['matte'], '-vf', f'scale={s.W}:{s.H},format=gray',
                                      '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            s.last = idx - 1
        b = s.dec.stdout.read(s.W * s.H)
        if len(b) == s.W * s.H: s.cur = np.frombuffer(b, np.uint8).reshape(s.H, s.W)
        s.last += 1; return s.cur
    def _mega(s):
        if hasattr(s, 'mg'): return s.mg
        txt = s.d.get('mega', ''); im = Image.new('L', (s.W, s.H), 0)
        if txt:
            f = find_font(s.d.get('font')); size = int(s.H * 0.34)
            while size > 20:
                fnt = ImageFont.truetype(f, size)
                if ImageDraw.Draw(im).textlength(txt, font=fnt) < s.W * 0.96: break
                size -= 8
            d = ImageDraw.Draw(im); bb = d.textbbox((0, 0), txt, font=fnt); d.text(((s.W - (bb[2] - bb[0])) // 2 - bb[0], int(s.H * 0.30) - bb[1]), txt, font=fnt, fill=255)
        s.mg = (np.array(im).astype(np.float32) / 255)[..., None]; return s.mg
    def frame(s, to, base):
        k = int((to - s.t0) / s.every); fr_in = (to - s.t0) - k * s.every; world = s.img(k).copy()
        if k > 0 and fr_in < 1 / s.fps: world[:] = 255                                   # white frame on each swap
        col = np.array(hex_rgb(s.d.get('mega_color', '#e11d2e'))[::-1], np.float32)
        mg = s._mega() * float(s.d.get('mega_opacity', 1.0)); world = (world * (1 - mg) + col * mg).astype(np.uint8)
        a = s._alpha(to)
        if a is None: return world
        if s.d.get('raw_speaker'): s.raw_layer = (base.copy(), a)               # speaker pasted back AFTER the grade: raw, as in editor-v1
        a = (a.astype(np.float32) / 255)[..., None]; return (base * a + world * (1 - a)).astype(np.uint8)


MONO = ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', '/System/Library/Fonts/Menlo.ttc', 'C:/Windows/Fonts/consolab.ttf']


def _wrap(txt, fnt, maxw):
    d0 = ImageDraw.Draw(Image.new('RGB', (4, 4))); out = []
    for para in txt.split('\n'):
        cur = ''
        for wd in para.split(' '):
            t = (cur + ' ' + wd).strip()
            if d0.textlength(t, font=fnt) <= maxw or not cur: cur = t
            else: out.append(cur); cur = wd
        out.append(cur)
    return out


def _to_bgr(im): return cv2.cvtColor(np.array(im.convert('RGB')), cv2.COLOR_RGB2BGR)


class Typewriter(Dev):
    """a quoted line typed out with a blinking caret on a solid panel (real text only). Silent, as in the references."""
    kind = 'typewriter'
    def default_dur(s): return len(s.d['text']) / float(s.d.get('cps', 22)) + 0.9
    def frame(s, to, base):
        bg = s.d.get('bg', '#0a0a0a'); ink = s.d.get('color', '#f2f2f2'); n = int(max(0, to - s.t0) * float(s.d.get('cps', 22)))
        fnt = ImageFont.truetype(find_font(s.d.get('font')) or MONO[0], int(s.H * float(s.d.get('size', 0.05)))); lines = _wrap(s.d['text'], fnt, s.W * 0.84)
        im = Image.new('RGB', (s.W, s.H), bg); dr = ImageDraw.Draw(im); lh = int(fnt.size * 1.35); y = (s.H - lh * len(lines)) // 2; left = n
        caret = int((to - s.t0) * 2) % 2 == 0
        for ln in lines:
            shown = ln[:max(0, left)]; dr.text((s.W * 0.08, y), shown, font=fnt, fill=ink)
            if left <= len(ln) and left >= 0 and caret: dr.rectangle((s.W * 0.08 + dr.textlength(shown, font=fnt) + 4, y + 4, s.W * 0.08 + dr.textlength(shown, font=fnt) + 4 + fnt.size * 0.12, y + lh - 6), fill=ink)
            left -= len(ln) + 1; y += lh
        return _to_bgr(im)


class Terminal(Dev):
    """lines starting with '$' are typed; others print after the previous one finishes. Real text/commands/responses only."""
    kind = 'terminal'
    def default_dur(s): return sum(len(l) / float(s.d.get('cps', 34)) + 0.3 for l in s.d['lines']) + 0.8
    def frame(s, to, base):
        cps = float(s.d.get('cps', 34)); t = to - s.t0; shown = []
        for l in s.d['lines']:
            need = len(l) / cps if l.startswith('$') else 0.0
            if t <= 0: break
            if t >= need: shown.append(l); t -= need + 0.3
            else: shown.append(l[:int(t * cps)] + ('_' if int(to * 2) % 2 == 0 else '')); break
        fnt = ImageFont.truetype(find_font(s.d.get('font')) or MONO[0], int(s.H * 0.026)); im = Image.new('RGB', (s.W, s.H), '#0b0d10'); dr = ImageDraw.Draw(im)
        x0, y0, x1, y1 = int(s.W * 0.05), int(s.H * 0.18), int(s.W * 0.95), int(s.H * 0.82)
        dr.rounded_rectangle((x0, y0, x1, y1), 18, fill='#14181d', outline='#2a313a', width=2); dr.rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + 56), fill='#1c222a')
        for k, c in enumerate(('#ff5f56', '#ffbd2e', '#27c93f')): dr.ellipse((x0 + 24 + k * 36, y0 + 18, x0 + 44 + k * 36, y0 + 38), fill=c)
        lines = []
        for l in shown: lines += _wrap(l, fnt, x1 - x0 - 60)
        lh = int(fnt.size * 1.45); maxl = (y1 - y0 - 90) // lh
        for k, l in enumerate(lines[-maxl:]): dr.text((x0 + 30, y0 + 76 + k * lh), l, font=fnt, fill='#7ee787' if l.startswith('$') else '#d6dde6')
        return _to_bgr(im)


class CodeScroll(Dev):
    """real code scrolls up and stops; `mark` = line numbers swept by a highlighter once it has stopped."""
    kind = 'code_scroll'
    def default_dur(s): return 3.0
    def frame(s, to, base):
        lines = s.d['code'].split('\n'); fnt = ImageFont.truetype(find_font(s.d.get('font')) or MONO[0], int(s.H * 0.024)); lh = int(fnt.size * 1.5)
        im = Image.new('RGB', (s.W, s.H), '#0d1117'); dr = ImageDraw.Draw(im); p = float(ease((to - s.t0) / (s.dur * 0.6))); vis = int(s.H * 0.8 / lh)
        end = max(0, len(lines) - vis); top = p * end; y_off = int(s.H * 0.08) - int((top % 1) * lh)
        for k in range(int(top), min(len(lines), int(top) + vis + 2)):
            y = y_off + (k - int(top)) * lh
            for j, mk in enumerate(s.d.get('mark', [])):
                dt = (to - s.t0) - s.dur * 0.6 - j * 0.35
                if mk == k and dt > 0:
                    w = int((s.W * 0.9) * ease(dt / 0.35)); ov = Image.new('RGBA', (s.W, s.H), (0, 0, 0, 0)); ImageDraw.Draw(ov).rectangle((s.W * 0.04, y - 2, s.W * 0.04 + w, y + lh - 4), fill=(255, 214, 10, 90)); im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'); dr = ImageDraw.Draw(im)
            dr.text((s.W * 0.05, y), lines[k][:int(s.W / (fnt.size * 0.62))], font=fnt, fill='#c9d1d9')
        return _to_bgr(im)


TYPES = {c.kind: c for c in (TileReveal, Strobe, Wall3D, PopCollage, CutoutWorld, Typewriter, Terminal, CodeScroll)}


def build(plan, tm, W, H, fps):
    out = []
    for d in plan.get('devices', []):
        if d['type'] not in TYPES: raise ValueError(f"unknown device {d['type']}: {sorted(TYPES)}")
        out.append(TYPES[d['type']](d, tm, W, H, fps))
    return out


def all_cues(plan, tm, fps=30):
    return [c for dv in build(plan, tm, 1080, 1920, fps) for c in dv.cues()]

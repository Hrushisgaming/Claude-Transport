"""captions.py - word-by-word captions, editor-v1 style, with three tiers.

plan["captions"] = {
  "words": "work/tx/words.json" | [{"w","s","e"}, ...]      (SOURCE seconds, from transcribe.py)
  "pos": "lower" | "center" | "top",  "size": 62,  "max_words": 5,
  "keywords": ["claude", "billion"],     a word that gets BIG (2.3x, bold, key_color)
  "stress": ["that changed everything"], a phrase in italic serif
  "key_color": "#ffffff", "color": "#ffffff", "font": null, "serif": null }
Words appear one at a time at their onset (cumulative in the line) and clear after the line ends.
Every word on screen was said: captions are built only from the transcript.
"""
import json, os, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from ce_common import hex_rgb

SANS = ['/usr/share/fonts/opentype/inter/Inter-Bold.otf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/System/Library/Fonts/Helvetica.ttc', 'C:/Windows/Fonts/arialbd.ttf']
SERIF = ['/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf', '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf',
         '/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf', 'C:/Windows/Fonts/georgiaz.ttf']
norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())


def pick(cands, pref=None):
    return next((f for f in ([pref] if pref else []) + cands if f and os.path.exists(f)), None)


class Captions:
    def __init__(s, cfg, tm, W, H, plan_dir='.'):
        w = cfg['words']; w = json.load(open(w if os.path.isabs(w) else os.path.join(plan_dir, w))) if isinstance(w, str) else w
        lo, hi = tm.start, tm.start + tm.D_src
        s.words = [dict(w=x['w'].strip(), t=float(tm.to_out(x['s'])), te=float(tm.to_out(x['e']))) for x in w if lo - 0.01 <= x['s'] <= hi and x['w'].strip()]
        s.cfg, s.W, s.H, s.u = cfg, W, H, min(W, H) / 1080
        kws = {norm(k) for k in cfg.get('keywords', [])}
        for x in s.words: x['kind'] = 'key' if norm(x['w']) in kws else 'base'
        toks = [norm(x['w']) for x in s.words]
        for ph in cfg.get('stress', []):
            p = [norm(t) for t in ph.split()]
            for i in range(len(toks) - len(p) + 1):
                if toks[i:i + len(p)] == p:
                    for j in range(i, i + len(p)):
                        if s.words[j]['kind'] == 'base': s.words[j]['kind'] = 'stress'
        s.groups, cur = [], []
        for x in s.words:
            if cur and (x['t'] - cur[-1]['te'] > 0.45 or len(cur) >= int(cfg.get('max_words', 5)) or re.search(r'[.?!]$', cur[-1]['w'])): s.groups.append(cur); cur = []
            cur.append(x)
        if cur: s.groups.append(cur)
        size = int(cfg.get('size', 62) * s.u); sans, ser = pick(SANS, cfg.get('font')), pick(SERIF, cfg.get('serif'))
        if not sans: raise RuntimeError('captions: no font found, set captions.font')
        s.f = dict(base=ImageFont.truetype(sans, size), key=ImageFont.truetype(sans, int(size * 2.3)), stress=ImageFont.truetype(ser or sans, int(size * 1.15)))
        s.size, s.cache = size, {}

    def _sprite(s, gi, n):
        k = (gi, n)
        if k in s.cache: return s.cache[k]
        W = s.W; words = s.groups[gi][:n]; d0 = ImageDraw.Draw(Image.new('RGBA', (4, 4))); lines, cur, cw = [], [], 0; gap = int(s.size * 0.3)
        for x in words:
            wd = d0.textlength(x['w'], font=s.f[x['kind']])
            if x['kind'] == 'key':
                if cur: lines.append(cur); cur, cw = [], 0
                lines.append([(x, wd)]); continue
            if cur and cw + gap + wd > W * 0.88: lines.append(cur); cur, cw = [], 0
            cur.append((x, wd)); cw += wd + (gap if len(cur) > 1 else 0)
        if cur: lines.append(cur)
        hts = [max(s.f[x['kind']].size for x, _ in ln) * 1.25 for ln in lines]; H = int(sum(hts) + 20); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); y = 10
        for ln, h in zip(lines, hts):
            tw = sum(w for _, w in ln) + gap * (len(ln) - 1); x0 = (W - tw) / 2
            for x, wd in ln:
                col = hex_rgb(s.cfg.get('key_color' if x['kind'] == 'key' else 'color', '#ffffff')) + (255,); fnt = s.f[x['kind']]
                d.text((x0, y), x['w'], font=fnt, fill=col, stroke_width=max(2, fnt.size // 16), stroke_fill=(0, 0, 0, 255)); x0 += wd + gap
            y += h
        a = np.array(im); sp = (cv2.cvtColor(a[..., :3], cv2.COLOR_RGB2BGR), a[..., 3].astype(np.float32) / 255); s.cache[k] = sp; return sp

    def apply(s, f, to):
        for gi, g in enumerate(s.groups):
            if g[0]['t'] <= to < g[-1]['te'] + 0.25:
                n = sum(1 for x in g if x['t'] <= to)
                if n == 0: return f
                rgb, a = s._sprite(gi, n); h = a.shape[0]
                y = {'lower': int(s.H * 0.70), 'center': (s.H - h) // 2, 'top': int(s.H * 0.12)}.get(s.cfg.get('pos', 'lower'), int(s.H * 0.70)); y = max(0, min(s.H - h, y))
                roi = f[y:y + h].astype(np.float32); f[y:y + h] = (roi * (1 - a[..., None]) + rgb * a[..., None]).astype(np.uint8); return f
        return f

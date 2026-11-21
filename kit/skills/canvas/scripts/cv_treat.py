#!/usr/bin/env python3
"""cv_treat.py — every texture and image treatment the Canvas style uses.

Numbers come from reference/style.md, measured off the 9:16 reference reel, and re-composed for 16:9. Colours were sampled from full-resolution frames.

    py cv_treat.py grounds  <outdir> [--portrait]          paper.jpg, dark.jpg, blue.jpg, blue_vig.jpg (2304x1296)
                                                           --portrait: paper_v.jpg ... (1296x2304) for 9:16 short form
    py cv_treat.py painting <src> <out.jpg> [--side right|left|full] [--focus 0.5] [--fx 0.5] [--portrait]
                                                           9:16: --side full --portrait --fx <subject x 0..1>: the painting
                                                           fills the frame like the reel, words over its quiet area
    py cv_treat.py figure   <rgba.png> <out_fig.png> <out_halo.png> [--fade 0.22]
    py cv_treat.py photo    <src> <out.jpg> [--bw] [--maxw 1400]

Grounds are 1.2x the frame so the camera can slide, pan and push without showing an edge.
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps

W, H = 2304, 1296                     # 1.2 x 1920x1080: room for camera moves
PAPER = (0xee, 0xec, 0xf0)            # seen: #edebef / #e6e6f0 / #f9f6fa on the paper scenes (r_23.9, r_27.9, r_34.9)
DARK = (0x16, 0x18, 0x18)             # seen: #191a1a / #141616 on the graph and line scenes (r_4.5, r_16.9)
BLUE = (0x21, 0x48, 0xe0)             # seen: #1f4beb .. #2f5ef4 blue ground (r_45.9), #2045de the figure (r_23.9)
BLUE_DEEP = (0x0a, 0x16, 0x43)        # seen: #0a1643 quote-scene corners (r_50.9)
RNG = np.random.default_rng(7)


def blur(a, r):
    if r <= 0:
        return a
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255


def noise(h, w, r, seed=None):
    g = np.random.default_rng(seed) if seed is not None else RNG
    n = g.random((h, w)).astype(np.float32)
    n = blur(n, r) if r else n
    n -= n.mean()
    return n / (n.std() + 1e-6)


def mottle(h, w, seed=1):
    """Cloudy low-frequency paper mottling, three octaves (seen on every paper scene)."""
    return (0.55 * noise(h, w, 60, seed) + 0.3 * noise(h, w, 22, seed + 1) + 0.15 * noise(h, w, 6, seed + 2))


def vignette(h, w, strength=0.35, power=2.2):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    return 1 - strength * np.clip(d, 0, 1) ** power


def save(a, path, q=93):
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))
    if path.endswith('.png'):
        im.save(path)
    else:
        im.convert('RGB').save(path, quality=q, subsampling=0)


def grounds(out, portrait=False):
    os.makedirs(out, exist_ok=True)
    h, w = (W, H) if portrait else (H, W)
    sfx = '_v' if portrait else ''
    # PAPER: cool off-white, cloudy mottling +-2.5%, fine grain +-1.5%, a faint dot grid every 14 px (seen 33.0-39.2 s)
    base = np.array(PAPER, np.float32) / 255
    m = mottle(h, w, 3)[..., None] * 0.012
    g = noise(h, w, 0.6, 4)[..., None] * 0.015
    yy, xx = np.mgrid[0:h, 0:w]
    dots = (((xx % 14) < 2) & ((yy % 14) < 2)).astype(np.float32)[..., None] * 0.045
    paper = base * (1 + m + g) - dots
    paper *= vignette(h, w, 0.035)[..., None]
    save(paper, f'{out}/paper{sfx}.jpg')
    # DARK: near-black, grain, faint ruled lines every 54 px (the graph and line scenes, 2.1-6.0 s and 15.2-17.1 s)
    base = np.array(DARK, np.float32) / 255
    d = base * (1 + mottle(h, w, 5)[..., None] * 0.18 + noise(h, w, 0.7, 6)[..., None] * 0.22)
    rule = ((yy % 54) == 0).astype(np.float32)[..., None] * 0.018
    d = d + rule
    d *= vignette(h, w, 0.45)[..., None]
    save(d, f'{out}/dark{sfx}.jpg')
    # BLUE: ultramarine with a rough grain (the orbit scene, 43.3-47.1 s); BLUE_VIG: the quote scene's heavy vignette (49.0 s)
    base = np.array(BLUE, np.float32) / 255
    rough = noise(h, w, 0.8, 8)[..., None] * 0.07 + mottle(h, w, 9)[..., None] * 0.05
    speck = (RNG.random((h, w)) > 0.985).astype(np.float32)[..., None] * 0.10
    b = base * (1 + rough) + speck * 0.5
    save(b * vignette(h, w, 0.18)[..., None], f'{out}/blue{sfx}.jpg')
    vig = vignette(h, w, 1.0, 1.6)[..., None]
    deep = np.array(BLUE_DEEP, np.float32) / 255
    bv = b * vig + deep * (1 - vig)
    save(bv, f'{out}/blue_vig{sfx}.jpg')
    print('grounds ->', out)


def painting(src, out, side='right', focus=0.5, fx=0.5, portrait=False):
    """A painting on the dark ground: paint + rough paper texture, darkened edges, blurred edges.
    16:9 recomposition: a portrait/square painting fills the frame HEIGHT on one side and falls off into the dark on the
    other, where the text sits (the reel's text always sits in the painting's quiet area, 11.2-14.1 s, 17.2-19.9 s)."""
    im = Image.open(src).convert('RGB')
    h, w = (W, H) if portrait else (H, W)
    if side == 'full' and portrait:
        # 9:16: fit the painting to the VISIBLE height + 40 px each side (the world is 1.2x the frame, so filling the world
        # would lose the top and bottom 192 px: Van Gogh's head went), crop the width around the subject (fx), and feather
        # the top and bottom into the textured dark
        ph = int(h / 1.2) + 80
        s_ = ph / im.height
        im = im.resize((int(im.width * s_), ph), Image.LANCZOS)
        if im.width >= w:
            x0 = int(max(0, min(im.width - w, fx * im.width - w / 2)))
            im = im.crop((x0, 0, x0 + w, ph))
        ground = np.array(DARK, np.float32) / 255 * (1 + noise(h, w, 0.7, 6)[..., None] * 0.22 + mottle(h, w, 5)[..., None] * 0.18)
        canvas = ground.copy()
        y0 = (h - ph) // 2
        px0 = (w - im.width) // 2
        canvas[y0:y0 + ph, px0:px0 + im.width] = np.asarray(im).astype(np.float32) / 255
        mask = np.zeros((h, w), np.float32)
        mask[y0:y0 + ph, px0:px0 + im.width] = 1
        fe = int(ph * 0.06)
        ramp = (np.linspace(0, 1, fe, dtype=np.float32) ** 1.4)[:, None]
        mask[y0:y0 + fe] *= ramp
        mask[y0 + ph - fe:y0 + ph] *= ramp[::-1]
        canvas = canvas * mask[..., None] + ground * (1 - mask[..., None])
    elif side == 'full':
        im = ImageOps.fit(im, (w, h), centering=(fx, focus))
        p = np.asarray(im).astype(np.float32) / 255
        canvas = p
        mask = np.ones((h, w), np.float32)
    else:
        ph = 1180                                   # the frame's 1080 plus 50 px each side: the whole painting reads in frame
        s = ph / im.height
        pw = int(im.width * s)
        im = im.resize((pw, ph), Image.LANCZOS)
        # the dark side is the reel's textured near-black (#161818 + grain), never a crushed black
        ground = np.array(DARK, np.float32) / 255 * (1 + noise(h, w, 0.7, 6)[..., None] * 0.22 + mottle(h, w, 5)[..., None] * 0.18)
        p = np.ones((h, pw, 3), np.float32) * (np.array(DARK, np.float32) / 255)
        y0 = (h - ph) // 2
        p[y0:y0 + ph] = np.asarray(im).astype(np.float32) / 255
        canvas = ground.copy()
        # flush to the ground's outer edge (the frame shows the centre 1920 of 2304, so 192 px sit off-frame)
        x0 = w - pw if side == 'right' else 0
        canvas[:, x0:x0 + pw] = p
        # feather the inner edge over 22% of the painting into the ground
        mask = np.zeros((h, w), np.float32)
        mask[:, x0:x0 + pw] = 1
        fe = int(pw * 0.22)
        ramp = np.linspace(0, 1, fe, dtype=np.float32) ** 1.6
        if side == 'right':
            mask[:, x0:x0 + fe] *= ramp
        else:
            mask[:, x0 + pw - fe:x0 + pw] *= ramp[::-1]
        canvas = canvas * mask[..., None] + ground * (1 - mask[..., None])
    # slightly muted, like the reel's paintings
    lum = canvas.mean(2, keepdims=True)
    canvas = lum + (canvas - lum) * 0.88
    # paint + rough paper texture: a fine canvas weave and grain, multiplied
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = (np.sin(xx * 1.9) * np.sin(yy * 1.9)) * 0.025
    tex = 1 + mottle(h, w, 11) * 0.05 + noise(h, w, 0.8, 12) * 0.05 + weave
    canvas = canvas * tex[..., None]
    # blur the edges: blend toward a blurred copy, centre sharp (seen on every painting: the corners go soft)
    soft = np.stack([blur(canvas[..., c], 9) for c in range(3)], -1)
    r = 1 - vignette(h, w, 1.0, 2.6)
    canvas = canvas * (1 - r[..., None]) + soft * r[..., None]
    # darken the edges
    canvas *= vignette(h, w, 0.48, 1.9)[..., None]
    save(canvas, out, 92)
    print('painting ->', out)


def figure(src, out_fig, out_halo, fade=0.22):
    """The rough, painted, noisy blue cut-out (principle 7, seen 20.0-24.0 s and 43.3-47.1 s).
    Luminance mapped onto an ultramarine ramp, cloth texture, ragged edges, the bottom dissolving into the paper,
    plus a separate soft rough halo disc behind the head and shoulders."""
    im = Image.open(src).convert('RGBA')
    a = np.asarray(im).astype(np.float32) / 255
    al = a[..., 3]
    ys, xs = np.where(al > 0.2)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    pad = 40
    a = a[max(0, y0 - pad):y1 + 1, max(0, x0 - pad):x1 + pad]
    h, w = a.shape[:2]
    rgb, al = a[..., :3], a[..., 3]
    lum = (rgb * np.array([0.3, 0.55, 0.15], np.float32)).sum(2)
    lum = (lum - np.percentile(lum[al > .5], 3)) / (np.percentile(lum[al > .5], 97) - np.percentile(lum[al > .5], 3) + 1e-6)
    lum = np.clip(lum, 0, 1) ** 1.35
    deep = np.array((0x0b, 0x1a, 0x96), np.float32) / 255
    mid = np.array(BLUE, np.float32) / 255
    light = np.array((0x5c, 0x7c, 0xff), np.float32) / 255
    t = lum[..., None]
    col = np.where(t < 0.7, deep + (mid - deep) * (t / 0.7), mid + (light - mid) * ((t - 0.7) / 0.3))
    # rough cloth: two directional noises crossed, plus speckle
    cloth = 1 + 0.10 * noise(h, w, 1.2, 21) + 0.06 * np.asarray(
        Image.fromarray(((noise(h, w, 0, 22) * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(2))).astype(np.float32) / 128 - 0.06
    col = col * cloth[..., None]
    # ragged edge: push the matte through noise and re-threshold softly
    rough = noise(h, w, 3.5, 23) * 0.20 + noise(h, w, 1.6, 24) * 0.06
    b = blur(al, 2.5)
    edge = np.clip(1 - np.abs(2 * blur(al, 9) - 1), 0, 1) ** 0.7     # roughness only near the silhouette, no holes inside
    al2 = np.clip((b + rough * edge - 0.5) * 3.2 + 0.5, 0, 1)
    al2 = np.minimum(al2, np.clip(al * 1.4, 0, 1))
    # bottom dissolves into the paper over the last `fade` of the height, streaky like a dry brush
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    f = np.clip((1 - yy) / fade, 0, 1)
    vs = np.asarray(Image.fromarray(((noise(h, w, 0, 25) * 40) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(1)).resize((w, h))).astype(np.float32) / 255
    vs = blur(np.repeat(vs[::8], 8, 0)[:h], 2) - 0.5          # vertical dry-brush streaks
    streak = np.clip(f * 1.15 + vs * 0.9 * (1 - f) - 0.05, 0, 1)
    al2 = al2 * streak
    fig = np.dstack([np.clip(col, 0, 1), al2])
    Image.fromarray((fig * 255).astype(np.uint8), 'RGBA').save(out_fig)
    # halo: a rough light-blue disc, radius ~0.62 of the figure width, behind the upper body
    R = int(max(w, h) * 0.5)
    S = R * 2 + 120
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    d = np.sqrt((xx - S / 2) ** 2 + (yy - S / 2) ** 2) / R
    edge = noise(S, S, 14, 26) * 0.06 + noise(S, S, 4, 27) * 0.025
    disc = np.clip((1 - d + edge) * 6, 0, 1)
    inner = 0.6 + 0.12 * mottle(S, S, 28)
    halo_a = np.clip(disc * inner, 0, 1) * 0.62
    halo_c = np.array((0xa9, 0xb8, 0xf5), np.float32) / 255
    halo = np.dstack([np.ones((S, S, 3), np.float32) * halo_c, halo_a])
    Image.fromarray((halo * 255).astype(np.uint8), 'RGBA').save(out_halo)
    print('figure ->', out_fig, fig.shape[1], 'x', fig.shape[0], '| halo', S)


def photo(src, out, bw=False, maxw=1400):
    """A real photo for the object scenes (principle 9, seen 33.0-39.2 s): kept as-is (the white border and tilt are CSS),
    optionally a warm black-and-white like the reel's archive photos."""
    im = Image.open(src).convert('RGB')
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    if bw:
        g = np.asarray(ImageOps.grayscale(im)).astype(np.float32) / 255
        warm = np.dstack([g * 1.02, g * 0.97, g * 0.88])
        im = Image.fromarray(np.clip(warm * 255, 0, 255).astype(np.uint8))
    im.save(out, quality=92)
    print('photo ->', out, im.size)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('args', nargs='*')
    ap.add_argument('--side', default='right')
    ap.add_argument('--focus', type=float, default=0.5)
    ap.add_argument('--fade', type=float, default=0.22)
    ap.add_argument('--bw', action='store_true')
    ap.add_argument('--maxw', type=int, default=1400)
    ap.add_argument('--fx', type=float, default=0.5)
    ap.add_argument('--portrait', action='store_true')
    o = ap.parse_args()
    if o.cmd == 'grounds':
        grounds(o.args[0], o.portrait)
    elif o.cmd == 'painting':
        painting(o.args[0], o.args[1], o.side, o.focus, o.fx, o.portrait)
    elif o.cmd == 'figure':
        figure(o.args[0], o.args[1], o.args[2], o.fade)
    elif o.cmd == 'photo':
        photo(o.args[0], o.args[1], o.bw, o.maxw)
    else:
        sys.exit(__doc__)

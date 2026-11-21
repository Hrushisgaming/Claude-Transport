"""looks.py - colour looks and image treatments shared by the renderer and the devices.
Grades (cold/teal/warm/bleach/noir/horror), plus halftone (dark dot screen in the shadows) and led
(the picture rebuilt as lit dots on black), the two treatments measured in the editor-v1 references."""
import numpy as np, cv2

LOOKS = dict(
    natural=dict(sat=1.0, con=1.0, bri=1.0, sh=(0, 0, 0), hi=(0, 0, 0)),
    cold=dict(sat=0.8, con=1.12, bri=0.97, sh=(-0.02, 0.03, 0.09), hi=(0, 0.01, 0.03)),
    teal=dict(sat=1.05, con=1.2, bri=1.0, sh=(-0.05, 0.06, 0.07), hi=(0.09, 0.035, -0.05)),
    warm=dict(sat=1.1, con=1.1, bri=1.02, sh=(0.05, 0.02, 0.0), hi=(0.09, 0.045, -0.03)),
    bleach=dict(sat=0.45, con=1.38, bri=1.0, sh=(0, 0, 0.025), hi=(0.03, 0.0, 0.0)),
    noir=dict(sat=0.0, con=1.45, bri=0.98, sh=(0, 0, 0), hi=(0, 0, 0)),
    mono=dict(sat=0.0, con=1.38, bri=0.98, sh=(0, 0, 0), hi=(0, 0, 0)),
    horror=dict(sat=0.6, con=1.3, bri=0.9, sh=(0.0, 0.05, 0.02), hi=(0.12, -0.02, -0.04)),
    amber=dict(sat=0.7, con=1.15, bri=1.0, sh=(0.08, 0.03, -0.02), hi=(0.14, 0.07, -0.05)),
    # added in 3.0 for non-action styles
    vivid=dict(sat=1.3, con=1.12, bri=1.02, sh=(0.0, 0.01, 0.03), hi=(0.04, 0.02, 0.0)),        # creators, vlogs, anime edits
    clean=dict(sat=1.05, con=1.06, bri=1.03, sh=(0.0, 0.0, 0.01), hi=(0.01, 0.01, 0.0)),        # product, tutorial, real estate, news
    film=dict(sat=0.9, con=1.1, bri=1.0, sh=(0.05, 0.06, 0.07), hi=(0.03, 0.02, 0.0)),          # lifted blacks, soft cool shadows
    pastel=dict(sat=0.85, con=0.92, bri=1.06, sh=(0.08, 0.06, 0.09), hi=(0.02, 0.0, 0.03)),     # aesthetic / lofi / weddings
    golden=dict(sat=1.2, con=1.12, bri=1.02, sh=(0.03, 0.01, -0.02), hi=(0.10, 0.06, -0.02)),   # travel, golden hour
    sport=dict(sat=1.25, con=1.3, bri=1.0, sh=(0.0, 0.0, 0.02), hi=(0.03, 0.02, 0.0)),          # punchy, saturated
    cyber=dict(sat=1.3, con=1.25, bri=0.98, sh=(0.10, -0.02, 0.12), hi=(-0.03, 0.08, 0.10)),    # neon: magenta shadows, cyan highlights
    sepia=dict(sat=0.35, con=1.1, bri=1.0, sh=(0.04, 0.02, -0.02), hi=(0.10, 0.06, -0.02)),
    matte=dict(sat=0.9, con=0.9, bri=1.02, sh=(0.06, 0.06, 0.06), hi=(0.0, 0.0, 0.0)),
)


def lerp_look(a, b, k):
    return {key: (tuple(x + (y - x) * k for x, y in zip(a[key], b[key])) if isinstance(a[key], tuple) else a[key] + (b[key] - a[key]) * k)
            for key in a}


def apply_look(f8, lk, boost=1.0):
    """BGR uint8 -> BGR float32 0..1 graded (not clipped). boost>1 = a little more contrast/less colour (slow-mo)."""
    f = f8.astype(np.float32) / 255.0
    luma = (0.114 * f[..., 0] + 0.587 * f[..., 1] + 0.299 * f[..., 2])[..., None]
    f = luma + (f - luma) * (lk['sat'] * (0.8 if boost > 1 else 1.0))
    f = (f - 0.5) * (lk['con'] * (1.08 if boost > 1 else 1.0)) + 0.5
    f *= lk['bri']
    sh = np.array(lk['sh'][::-1], np.float32); hi = np.array(lk['hi'][::-1], np.float32)
    return f + sh * (1 - luma) ** 2 + hi * luma ** 2


class Halftone:
    """45-degree dot screen: dark dots in the shadows. Precomputes the screen for one frame size."""
    def __init__(self, W, H, pitch=None):
        p = pitch or max(5, round(H * 0.0075)); self.p = p
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        u = ((xx + yy) / np.sqrt(2)) % p - p / 2; v = ((xx - yy) / np.sqrt(2)) % p - p / 2
        self.r = np.sqrt(u * u + v * v) / (p / 2)

    def __call__(self, im, amount=0.35):
        f = im.astype(np.float32) / 255; lum = f[..., 0] * 0.114 + f[..., 1] * 0.587 + f[..., 2] * 0.299
        L = cv2.GaussianBlur(lum, (0, 0), self.p / 2)
        dot = cv2.GaussianBlur((self.r < np.sqrt(np.clip(1 - L, 0, 1)) * 0.95).astype(np.float32), (0, 0), 0.6)
        return (np.clip(f * (1 - amount * dot[..., None] * (1 - L[..., None]) ** 0.5), 0, 1) * 255).astype(np.uint8)


def led(im, amount=1.0, cells=110):
    """the picture rebuilt as lit dots on black (cached per image by the caller: it is slow)."""
    H, W = im.shape[:2]; cw = W / cells; rows = int(H / cw)
    small = cv2.resize(im, (cells, rows), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    out = np.zeros((H, W, 3), np.float32)
    for j in range(rows):
        for i in range(cells):
            c = small[j, i]; L = float(c.mean())
            if L < 0.06: continue
            cv2.circle(out, (int((i + 0.5) * cw), int((j + 0.5) * cw)), max(1, int(cw * 0.42 * min(1, 0.4 + L))),
                       (c * (0.6 + 0.6 * amount)).tolist(), -1, cv2.LINE_AA)
    out = out + cv2.GaussianBlur(out, (0, 0), cw * 0.8) * 0.6
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def cover(im, W, H, focus=(0.5, 0.5)):
    h, w = im.shape[:2]; s = max(W / w, H / h); r = cv2.resize(im, (max(W, int(round(w * s))), max(H, int(round(h * s)))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    y0 = int((r.shape[0] - H) * focus[1]); x0 = int((r.shape[1] - W) * focus[0]); return r[y0:y0 + H, x0:x0 + W]


def treat_image(im, W, H, treat=None):
    """fit a found picture to the frame and apply a named treatment: a look name, 'halftone', 'led', or 'teal+halftone'."""
    out = cover(im, W, H)
    for part in (treat or '').split('+'):
        part = part.strip()
        if not part: continue
        if part == 'halftone': out = Halftone(W, H)(out, 0.4)
        elif part == 'led': out = led(out)
        elif part == 'negative': out = 255 - out
        elif part.startswith('hue='):
            hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV); hsv[..., 0] = (hsv[..., 0].astype(int) + int(float(part[4:]) / 2)) % 180; out = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        elif part.startswith('duo='):
            h = part[4:].lstrip('#'); col = np.array([int(h[i:i + 2], 16) for i in (4, 2, 0)], np.float32); g = (cv2.cvtColor(out, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255)[..., None]
            out = np.where(g < 0.5, col * (g * 2), col + (255 - col) * ((g - 0.5) * 2)).clip(0, 255).astype(np.uint8)
        elif part in LOOKS: out = (np.clip(apply_look(out, LOOKS[part]), 0, 1) * 255).astype(np.uint8)
        else: raise ValueError(f'unknown treat: {part}')
    return out

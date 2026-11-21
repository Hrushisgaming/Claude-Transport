"""cv_devices.py — the Canvas device library (the premium minimal look, 16:9 and 9:16).

Every beat is one of these devices. Frame counts were read frame by frame off the 9:16 reference reel
(reference/style.md, "Transitions, frame by frame"). A device writes its own HTML, its
GSAP lines and its own SFX cue, so the sound lands on the frame the picture changes.

    import sys; sys.path.insert(0, '<skill>/components'); from cv_devices import *
    c = Comp(22.0)
    aroll(c, 0, 2.03, 'assets/cam.mp4')
    cap(c, None, 2.03, [('l', [('Honestly,', .03, 's'), ...]), ('c', [('argue', 1.39, 'b')])], y=760)
    s = Scene(c, 2.03, 5.55, ground='paper')            # a world 1.2x the frame, with its own camera + motion blur
    photo(s, 'assets/img/thumb.jpg', 2.27, x=700, y=600, w=760, rot=-3)
    s.close()
    c.write('index.html')

Coordinates are FRAME pixels (1920x1080). A scene's world is 2304x1296 centred on the frame, so the camera can slide,
pan and push 192/108 px past any edge without showing it.

Rules baked in (each bit an earlier build, see CLAUDE.md / memory):
- every time is snapped to a whole frame; clip durations are FLOORED to 4 decimals
- every clip gets an explicit z-index
- fromTo always carries immediateRender:false; initial states go in a gsap.set preamble outside the timeline
- only transforms, opacity and filter are animated (house rule 3); the motion blur is an SVG feGaussianBlur whose
  stdDeviation is tweened ("60 0" = horizontal smear), so the smear is directional like the reel's
- colours and fonts come from assets/tokens.css only (house rule 2)
"""
import math, html as _html

FPS = 30
W, H = 1920, 1080
WW, WH = 2304, 1296            # world size: 1.2x the frame
OX, OY = (WW - W) // 2, (WH - H) // 2
FMT = '16x9'

# --- measured (study, "Type") ------------------------------------------------------------------------------------------
BIG = 124        # key word: Inter 900, tracking -0.045em. Reel: ~8% of frame height, re-scaled for a 16:9 face size
SMALL = 32       # surrounding words: Inter 500. Reel: caption height 3.1% of frame (measure.py) -> 32-34 px at 1080
BLUR_BIG = 5     # frames: key word blur-in, blur 16 px -> 0, scale 1.10 -> 1 (frames 17-23 of the reel)
BLUR_SMALL = 3   # frames: small words, blur 5 px -> 0
SLIDE_IN = 5     # frames: painting slide-in, horizontal smear peak -> 0 (frames 343-348)
WHIP_OUT, WHIP_IN = 6, 7   # frames: painting-to-painting whip (frames 371-384)
POP = 5          # frames: illustration blur-pop, blur 22 -> 0, scale 1.08 -> 1 (frames 598-603)
DROP = 6         # frames: photo drop-and-settle (frames 1001-1006)
WIPE = 10        # frames: highlighter box scaleX 0 -> 1 (frames 553-563)


def set_format(fmt):
    """'16x9' (the studio default) or '9x16' (short form: the reel's own shape). Call before Comp().
    9:16 sizes are measured straight off the reel at 1080x1920: a short key word ~180 px ('four'), long ones shrink to fit the
    width ('skip around'); small words ~44 px; the caption block centred on the chest, clear of the Reels/TikTok UI."""
    global W, H, WW, WH, OX, OY, BIG, SMALL, FMT
    FMT = fmt
    if fmt == '9x16':
        W, H, BIG, SMALL = 1080, 1920, 176, 44
    else:
        W, H, BIG, SMALL = 1920, 1080, 124, 32
    WW, WH = W * 6 // 5, H * 6 // 5
    OX, OY = (WW - W) // 2, (WH - H) // 2


EM = {'b': 0.56, 'i': 0.49, 'n': 0.56}   # average advance per character in em (Inter Black at -0.045em; Playfair Black Italic)


def fit(words, maxw=None, big=None):
    """Font size for the big words of one row so the row fits maxw px (the reel shrinks a long key word to the width)."""
    big = big or BIG
    maxw = maxw or W * 0.8
    em = sum(len(w) * EM.get(st.partition('/')[0], 0) for w, _, st in words if st.partition('/')[0] in EM)
    em += 0.24 * max(0, len(words) - 1)
    return int(min(big, maxw / em)) if em else big


def fr(t):
    return round(t * FPS) / FPS


def dstr(t0, t1):
    n = round(t1 * FPS) - round(t0 * FPS)
    return f'{math.floor(n / FPS * 1e4) / 1e4:.4f}'


def esc(s):
    return _html.escape(s, quote=True)


def F(n):
    return n / FPS


class Comp:
    def __init__(self, dur, cid='main'):
        self.dur, self.cid = fr(dur), cid
        self.els, self.js, self.pre, self.css, self.cues, self.defs = [], [], [], [], [], []
        self.n = 0

    def uid(self, p='e'):
        self.n += 1
        return f'{p}{self.n}'

    def clip(self, t0, t1, inner, z, cls='cv-layer', style='', cid=None):
        cid = cid or self.uid('c')
        t0, t1 = fr(t0), fr(t1)
        self.els.append(f'<div id="{cid}" class="clip {cls}" data-start="{t0:.4f}" data-duration="{dstr(t0, t1)}" '
                        f'style="z-index:{z};{style}">{inner}</div>')
        return cid

    def video(self, t0, t1, src, media_start, z, style='', vid=None):
        vid = vid or self.uid('v')
        t0, t1 = fr(t0), fr(t1)
        self.els.append(f'<video id="{vid}" class="clip cv-fill" src="{src}" muted playsinline '
                        f'data-start="{t0:.4f}" data-duration="{dstr(t0, t1)}" data-media-start="{media_start:.4f}" '
                        f'style="z-index:{z};{style}"></video>')
        return vid

    def at(self, line):
        self.js.append(line)

    def cue(self, t, sound, gain):
        self.cues.append((round(t, 3), sound, gain))

    def write(self, path, assets='assets/cv', title='Canvas'):
        doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width={W}, height={H}">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{assets}/tokens.css">
<link rel="stylesheet" href="{assets}/canvas.css">
<script src="{assets}/vendor/gsap.min.js"></script>
<style>
{chr(10).join(self.css)}
</style></head>
<body>
<div id="root" class="cv-frame{' cv-916' if FMT == '9x16' else ''}" data-composition-id="{self.cid}" data-start="0" data-width="{W}" data-height="{H}" data-duration="{self.dur:.4f}">
<svg class="cv-defs" width="0" height="0" aria-hidden="true"><defs>
{chr(10).join(self.defs)}
</defs></svg>
{chr(10).join(self.els)}
</div>
<script>
{chr(10).join(self.pre)}
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.js)}
window.__timelines["{self.cid}"] = tl;
</script>
</body></html>
'''
        open(path, 'w').write(doc)

    def write_cues(self, path):
        with open(path, 'w') as f:
            f.write('# Canvas cue sheet, written by the devices. time = file start (pre-rolled)\n')
            for t, s, g in sorted(self.cues):
                f.write(f'{max(0, t):.3f}  {s}  {g}\n')


# ------------------------------------------------------------------ sound
# The reference's palette: "a cinematic music track, clicks for text, highlighters for graphs, whooshes for transitions". Kept at half
# the density and quiet transients (memory: sfx-restraint), so only scene changes and camera moves get a cue.
# (file in sfx/, gain, pre-roll s = file start -> transient)
SND = {   # the kit's own synthesised sounds (scripts/synth-sfx.py writes them into sfx/; no samples)
    'whoosh': ('ev1kit/swish_1', 0.10, 0.27),   # slide-in / whip / fast pan: the swell peaks on the landing
    'swish': ('ev1kit/swish_1', 0.14, 0.27),    # a short air move: camera follow, line pan
    'tick': ('ev1kit/click_1', 0.12, 0.004),    # a hard cut between scenes; a photo landing
    'pop': ('ev1kit/click_3', 0.10, 0.004),     # an illustration or an icon popping in
    'sub': ('ev1kit/subboom_1', 0.08, 0.043),   # one weight moment per minute
}


def sfx(c, t, role, gain_scale=1.0):
    name, g, pre = SND[role]
    c.cue(fr(t) - pre, name, round(g * gain_scale, 3))


# ------------------------------------------------------------------ type
STYLE = {   # code -> (class, blur px, frames, scale from)
    's': ('cv-s', 5, BLUR_SMALL, 1.0),
    'b': ('cv-b', 16, BLUR_BIG, 1.10),
    'i': ('cv-i', 16, BLUR_BIG, 1.10),
    'n': ('cv-b cv-num', 16, BLUR_BIG, 1.10),
    'q': ('cv-q', 4, 2, 1.0),          # a quotation mark set inline with the words (the quote scene, 49.0-51.0 s)
}


def _word(c, word, style):
    base, _, color = style.partition('/')
    cls = STYLE[base][0] + (f' cv-{color}' if color else '')
    wid = c.uid('w')
    return wid, f'<span id="{wid}" class="cv-w {cls}">{esc(word)}</span>'


def cap(c, scene, t_end, rows, x=None, y=None, tone='light', z=60, t_start=None, hide_at=None, sound=None, maxw=None,
        scrim=False):
    """The cinematic text block (principle 1). rows = [(align, [(word, onset, style), ...]), ...]
    align: 'l' | 'c' | 'r' inside the block. style: 's' small, 'b' big sans, 'i' big serif italic, 'n' big number;
    add '/blue' for the accent colour, e.g. 'i/blue'. Each word appears ON its onset; big words blur in over 5 frames.
    tone: 'light' = white with a soft shadow (footage, paintings, dark, blue) | 'ink' = near-black (paper).
    scene=None puts the block in its own clip over everything (A-roll); otherwise it lives in the scene's world and
    moves with its camera (the reel's words smear with the whip, frames 371-377)."""
    x = W / 2 if x is None else x
    y = H / 2 if y is None else y
    gid = c.uid('g')
    first = min(t for _, ws in rows for _, t, _ in ws) if t_start is None else t_start
    rws = []
    for align, ws in rows:
        spans = []
        size = fit(ws, maxw)
        for word, t, st in ws:
            wid, h = _word(c, word, st)
            if st.partition('/')[0] in EM and size != BIG:
                h = h.replace('">', f'" style="font-size:{size}px">', 1)
            spans.append(h)
            base = st.partition('/')[0]
            _, b, n, s0 = STYLE[base]
            c.pre.append(f'gsap.set("#{wid}",{{opacity:0,filter:"blur({b}px)",scale:{s0}}});')
            c.at(f'tl.fromTo("#{wid}",{{opacity:0,filter:"blur({b}px)",scale:{s0}}},'
                 f'{{opacity:1,filter:"blur(0px)",scale:1,duration:{F(n):.4f},ease:"power2.out",immediateRender:false}},{fr(t):.4f});')
        rws.append(f'<div class="cv-row cv-{align}">{"".join(spans)}</div>')
    # scrim: a soft local darkening behind words that sit on a bright painting (the reel darkens a painting's edges
    # so the words read; on a 9:16 crop the words often land mid-painting)
    sc = '<div class="cv-scrim"></div>' if scrim else ''
    inner = f'<div id="{gid}" class="cv-cap cv-{tone}" style="left:{{X}}px;top:{{Y}}px">{sc}{"".join(rws)}</div>'
    if scene is None:
        c.clip(first, t_end, inner.replace('{X}', str(x)).replace('{Y}', str(y)), z, cls='cv-layer cv-capclip')
    else:
        scene.add(inner.replace('{X}', str(x + OX)).replace('{Y}', str(y + OY)))
        if hide_at is not None:
            c.at(f'tl.fromTo("#{gid}",{{opacity:1}},{{opacity:0,duration:{F(1):.4f},immediateRender:false}},{fr(hide_at):.4f});')
    if sound:
        sfx(c, first, sound)
    return gid


# ------------------------------------------------------------------ A-roll
def aroll(c, t0, t1, src, media_start=None, z=1, sound='tick'):
    """The talking head, raw (no grade, no zoom on the face), full frame, hard-cut in and out.
    The reel is 35% A-roll; 'announce on the face, describe on screen' (the reference's planning rule)."""
    c.video(t0, t1, src, t0 if media_start is None else media_start, z)
    if sound:
        sfx(c, t0, sound)


# ------------------------------------------------------------------ scenes (a world with a camera)
class Scene:
    GROUNDS = {'paper': 'paper.jpg', 'dark': 'dark.jpg', 'blue': 'blue.jpg', 'blue_vig': 'blue_vig.jpg', None: None}

    def __init__(self, c, t0, t1, ground='paper', z=10, assets='assets/cv', img=None):
        self.c, self.t0, self.t1, self.z = c, fr(t0), fr(t1), z
        self.id = c.uid('s')
        self.cam = self.id + 'cam'
        self.mb = self.id + 'mb'
        self.kids = []
        tex = self.GROUNDS.get(ground)
        if tex and FMT == '9x16':
            tex = tex.replace('.jpg', '_v.jpg')
        g = img or (f'{assets}/tex/{tex}' if tex else None)
        if g:
            self.kids.append(f'<img class="cv-ground" src="{g}" alt="">')
        c.defs.append(f'<filter id="{self.mb}" x="-5%" y="-5%" width="110%" height="110%" color-interpolation-filters="sRGB">'
                      f'<feGaussianBlur id="{self.mb}g" stdDeviation="0 0" edgeMode="duplicate"/></filter>')
        self.state = (0.0, 0.0, 1.0)
        self.dr = self.id + 'dr'
        c.pre.append(f'gsap.set("#{self.cam}",{{x:0,y:0,scale:1}});')
        c.pre.append(f'gsap.set("#{self.dr}",{{x:0,y:0,scale:1}});')

    def add(self, h):
        self.kids.append(h)

    def blur(self, t, dur, frm, to, ease='power2.out'):
        """Directional motion blur on the whole world: stdDeviation 'X Y' in px."""
        self.c.at(f'tl.fromTo("#{self.mb}g",{{attr:{{stdDeviation:"{frm[0]} {frm[1]}"}}}},'
                  f'{{attr:{{stdDeviation:"{to[0]} {to[1]}"}},duration:{dur:.4f},ease:"{ease}",immediateRender:false}},{fr(t):.4f});')

    def move(self, t, dur, x=None, y=None, s=None, ease='power3.inOut', smear=0):
        """Camera move to (x, y, scale) = the world's transform. smear>0 adds a motion blur that peaks mid-move
        along the direction of travel (the reel's camera follows, frames 147-156, 1580-1592)."""
        x0, y0, s0 = self.state
        x1 = x0 if x is None else x
        y1 = y0 if y is None else y
        s1 = s0 if s is None else s
        self.c.at(f'tl.fromTo("#{self.cam}",{{x:{x0},y:{y0},scale:{s0}}},{{x:{x1},y:{y1},scale:{s1},duration:{dur:.4f},'
                  f'ease:"{ease}",immediateRender:false}},{fr(t):.4f});')
        if smear:
            dx, dy = abs(x1 - x0), abs(y1 - y0)
            n = math.hypot(dx, dy) or 1
            bx, by = round(smear * dx / n, 1), round(smear * dy / n, 1)
            self.blur(t, dur * 0.5, (0, 0), (bx, by), 'power2.in')
            self.blur(t + dur * 0.5, dur * 0.5, (bx, by), (0, 0), 'power2.out')
        self.state = (x1, y1, s1)

    def drift(self, x=0, y=0, s=1.0, t0=None, t1=None, ease='none'):
        """A continuous camera travel under everything else (its own wrapper, so it never fights move()/slide_in()).
        The reel's camera keeps tracking through the graph, line and object scenes (2.1-6.1 s, 15.2-17.1 s, 33.0-35.2 s,
        51.1-55.0 s); the paintings, the figure and the face never drift (measured: scale 1.000 across seconds)."""
        a = self.t0 if t0 is None else fr(t0)
        b = self.t1 if t1 is None else fr(t1)
        self.c.at(f'tl.fromTo("#{self.dr}",{{x:0,y:0,scale:1}},{{x:{x},y:{y},scale:{s},duration:{b - a:.4f},ease:"{ease}",'
                  f'immediateRender:false}},{a:.4f});')

    def look(self, px, py, s=1.0):
        """Camera values that centre frame point (px, py) at scale s."""
        return -(px - W / 2) * s, -(py - H / 2) * s, s

    def slide_in(self, dx=260, frames=SLIDE_IN, smear=60, sound='whoosh'):
        """The painting's 'quick camera slide in' (principle 3): already almost in place on the first frame,
        smeared horizontally, settling over 5 frames."""
        self.c.at(f'tl.fromTo("#{self.cam}",{{x:{dx}}},{{x:0,duration:{F(frames):.4f},ease:"power2.out",immediateRender:false}},{self.t0:.4f});')
        self.blur(self.t0, F(frames), (smear, 0), (0, 0))
        if sound:
            sfx(self.c, self.t0, sound)

    def whip_out(self, dx=-420, frames=WHIP_OUT, smear=80, sound='whoosh'):
        t = self.t1 - F(frames)
        x0, y0, s0 = self.state
        self.c.at(f'tl.fromTo("#{self.cam}",{{x:{x0}}},{{x:{x0 + dx},duration:{F(frames):.4f},ease:"power2.in",immediateRender:false}},{fr(t):.4f});')
        self.blur(t, F(frames), (0, 0), (smear, 0), 'power2.in')
        if sound:
            sfx(self.c, t, sound)

    def whip_in(self, dx=420, frames=WHIP_IN, smear=80):
        self.c.at(f'tl.fromTo("#{self.cam}",{{x:{dx}}},{{x:0,duration:{F(frames):.4f},ease:"power2.out",immediateRender:false}},{self.t0:.4f});')
        self.blur(self.t0, F(frames), (smear, 0), (0, 0))

    def close(self):
        inner = (f'<div class="cv-drift" id="{self.dr}"><div class="cv-world" id="{self.cam}" style="filter:url(#{self.mb})">'
                 + ''.join(self.kids) + '</div></div>')
        return self.c.clip(self.t0, self.t1, inner, self.z, cls='cv-layer cv-scene', cid=self.id)


# ------------------------------------------------------------------ the devices
def painting(c, t0, t1, src, z=10, enter='slide', exit_whip=False, sound=True):
    """Principle 3: a painting with paint + paper texture, darkened and blurred edges (cv_treat.py painting), revealed by a
    quick camera slide (5 frames) or a whip from the previous painting (13 frames). Returns the open Scene: add the
    caption with cap(c, scene, ...) in the painting's quiet side, then scene.close()."""
    s = Scene(c, t0, t1, ground=None, z=z, img=src)
    if enter == 'slide':
        s.slide_in(sound='whoosh' if sound else None)
    elif enter == 'whip':
        s.whip_in()
    elif enter == 'cut' and sound:
        sfx(c, t0, 'tick')
    if exit_whip:
        s.whip_out(sound='whoosh' if sound else None)
    return s


def photo(s, src, t, x, y, w, rot=-3.0, z=2, sound=True, border=12):
    """Principle 9 (object + text): a real photo with a white border and a slight tilt, dropping onto the paper and
    settling over 6 frames (frames 1001-1006)."""
    c = s.c
    pid = c.uid('ph')
    s.add(f'<div id="{pid}" class="cv-photo" style="left:{x + OX}px;top:{y + OY}px;width:{w}px;z-index:{z};'
          f'padding:{border}px"><img src="{src}" alt=""></div>')
    c.pre.append(f'gsap.set("#{pid}",{{xPercent:-50,yPercent:-50,opacity:0,rotation:{rot + 2.5},y:-26,scale:1.04}});')
    c.at(f'tl.fromTo("#{pid}",{{opacity:0}},{{opacity:1,duration:{F(1):.4f},immediateRender:false}},{fr(t):.4f});')
    c.at(f'tl.fromTo("#{pid}",{{rotation:{rot + 2.5},y:-26,scale:1.04}},{{rotation:{rot},y:0,scale:1,duration:{F(DROP):.4f},'
         f'ease:"power3.out",immediateRender:false}},{fr(t):.4f});')
    if sound:
        sfx(c, t, 'tick', 0.8)
    return pid


def figure(s, fig_src, halo_src, t, cx=None, bottom=None, fig_w=1011, nat=(1011, 946), halo_w=1130, halo_dy=-120, sound=True):
    """Principle 7 (centre illustration): the rough painted ultramarine cut-out (cv_treat.py figure) standing in the lower
    half and bleeding off the bottom, a soft rough halo behind the head, text in the space around it. Blur-pops in.
    nat = the cut-out's natural pixel size (cv_treat prints it); fig_w scales it."""
    c = s.c
    cx = W / 2 if cx is None else cx
    bottom = H if bottom is None else bottom
    fh = fig_w * nat[1] / nat[0]
    hid, fid = c.uid('halo'), c.uid('fig')
    top = bottom - fh + 30
    s.add(f'<img id="{hid}" class="cv-abs" src="{halo_src}" style="left:{cx - halo_w / 2 + OX:.0f}px;'
          f'top:{top + halo_dy - 70 + OY:.0f}px;width:{halo_w}px" alt="">')
    s.add(f'<img id="{fid}" class="cv-abs" src="{fig_src}" style="left:{cx - fig_w / 2 + OX:.0f}px;'
          f'top:{top + OY:.0f}px;width:{fig_w}px" alt="">')
    for el, sc in ((fid, 1.08), (hid, 0.9)):
        c.pre.append(f'gsap.set("#{el}",{{opacity:0,filter:"blur(22px)",scale:{sc}}});')
        c.at(f'tl.fromTo("#{el}",{{opacity:0,filter:"blur(22px)",scale:{sc}}},{{opacity:1,filter:"blur(0px)",scale:1,'
             f'duration:{F(POP):.4f},ease:"power2.out",immediateRender:false}},{fr(t):.4f});')
    if sound:
        sfx(c, t, 'pop')
    return fid


def line(s, d, t0, t1, width=16, color='var(--cv-line)', z=1, glow=True, segments=None):
    """Principle 4 (line + text): one thick rounded accent-blue stroke that leads to the text, gets interrupted by it
    and carries on. d is an SVG path in FRAME coords. segments=[(t, fraction), ...] draws it in pieces (the line pauses
    behind a word), otherwise it draws linearly from t0 to t1."""
    c = s.c
    lid = c.uid('ln')
    flt = 'filter:drop-shadow(0 0 6px rgba(20,102,224,.35))' if glow else ''
    s.add(f'<svg class="cv-abs" style="left:0;top:0;z-index:{z};{flt}" width="{WW}" height="{WH}" viewBox="{-OX} {-OY} {WW} {WH}">'
          f'<path id="{lid}" d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    c.pre.append(f'(()=>{{const p=document.getElementById("{lid}");const L=p.getTotalLength();p.dataset.len=L;'
                 f'gsap.set(p,{{strokeDasharray:L+" "+(L+10),strokeDashoffset:L}});}})();')
    segs = segments or [(t0, 0.0), (t1, 1.0)]
    for (ta, fa), (tb, fb) in zip(segs, segs[1:]):
        c.at(f'(()=>{{const p=document.getElementById("{lid}");const L=+p.dataset.len;'
             f'tl.fromTo(p,{{strokeDashoffset:L*{1 - fa:.4f}}},{{strokeDashoffset:L*{1 - fb:.4f},duration:{max(F(1), fr(tb) - fr(ta)):.4f},'
             f'ease:"none",immediateRender:false}},{fr(ta):.4f});}})();')
    return lid


def graph(s, pts, steps, x_label='TIME', y_label='VALUE', axis=(260, 900, 1660, 160), z=2):  # axis = x0, y0 (origin), x1, y1
    """Principle 10 (graph + statistics): flat dark ground, thin white glowing axes, a white line traced by a glowing
    blue ball (seen 2.1-6.1 s). pts = the polyline in FRAME coords; steps = [(t, index_of_pt_reached), ...] so the ball
    climbs one step on each word ('a line that climbs one step every time he says up')."""
    c = s.c
    x0, y0, x1, y1 = axis
    gid = c.uid('gr')
    segl = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    total = sum(segl)
    cum = [0.0]
    for l in segl:
        cum.append(cum[-1] + l)
    d = 'M' + ' L'.join(f'{px:.1f},{py:.1f}' for px, py in pts)
    s.add(f'<svg class="cv-abs" style="left:0;top:0;z-index:{z}" width="{WW}" height="{WH}" viewBox="{-OX} {-OY} {WW} {WH}">'
          f'<g class="cv-axis"><line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/><line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}"/></g>'
          f'<path id="{gid}p" class="cv-gline" d="{d}" fill="none" stroke-dasharray="{total:.1f} {total + 10:.1f}" stroke-dashoffset="{total:.1f}"/>'
          f'<text class="cv-axlab" x="{(x0 + x1) / 2}" y="{y0 + 46}" text-anchor="middle">{esc(x_label)}</text>'
          f'<text class="cv-axlab" x="{x0 - 30}" y="{(y0 + y1) / 2}" text-anchor="middle" transform="rotate(-90 {x0 - 30} {(y0 + y1) / 2})">{esc(y_label)}</text>'
          f'</svg>')
    bid = c.uid('ball')
    s.add(f'<div id="{bid}" class="cv-ball" style="left:{OX}px;top:{OY}px;z-index:{z + 1}"></div>')
    c.pre.append(f'gsap.set("#{bid}",{{x:{pts[0][0]},y:{pts[0][1]},xPercent:-50,yPercent:-50}});')
    prev_i, prev_t = 0, None
    for k, (t, i) in enumerate(steps):
        if prev_t is None:
            prev_t = t
            c.pre.append(f'gsap.set("#{bid}",{{opacity:0,scale:.4}});')
            c.at(f'tl.fromTo("#{bid}",{{opacity:0,scale:.4}},{{opacity:1,scale:1,duration:{F(6):.4f},ease:"back.out(2)",immediateRender:false}},{fr(t):.4f});')
            continue
        # a step lasts up to 9 frames but always ENDS before the next step starts: overlapping tweens on one property
        # resolve in reverse order when the renderer seeks backwards, and the earlier step wins (seen on the first build)
        nxt = steps[k + 1][0] if k + 1 < len(steps) else fr(t) + F(9)
        dur = max(F(3), min(F(9), fr(nxt) - fr(t) - F(1)))
        # the ball travels the path vertices prev_i -> i; the line's dashoffset follows the same arc length
        kx = [pts[k][0] for k in range(prev_i, i + 1)]
        ky = [pts[k][1] for k in range(prev_i, i + 1)]
        kf = ','.join(f'{{x:{a},y:{b}}}' for a, b in zip(kx[1:], ky[1:]))
        c.at(f'tl.fromTo("#{bid}",{{x:{kx[0]},y:{ky[0]}}},{{keyframes:[{kf}],duration:{dur:.4f},ease:"power2.inOut",immediateRender:false}},{fr(t):.4f});')
        c.at(f'tl.fromTo("#{gid}p",{{strokeDashoffset:{total - cum[prev_i]:.1f}}},{{strokeDashoffset:{total - cum[i]:.1f},duration:{dur:.4f},'
             f'ease:"power2.inOut",immediateRender:false}},{fr(t):.4f});')
        prev_i, prev_t = i, t
    return bid


def highlight(s, t, x, y, w, h, z=3):
    """The accent-blue highlighter box behind a key number (seen 18.1-19.0 s): wipes in left to right over 10 frames."""
    c = s.c
    hid = c.uid('hl')
    s.add(f'<div id="{hid}" class="cv-hl" style="left:{x + OX}px;top:{y + OY}px;width:{w}px;height:{h}px;z-index:{z}"></div>')
    c.pre.append(f'gsap.set("#{hid}",{{scaleX:0,transformOrigin:"0% 50%"}});')
    c.at(f'tl.fromTo("#{hid}",{{scaleX:0}},{{scaleX:1,duration:{F(WIPE):.4f},ease:"power2.out",immediateRender:false}},{fr(t):.4f});')
    return hid


def callout(s, t, d, z=4, color='var(--cv-white)'):
    """The thin curved hand-drawn arrow from a subject to its text (seen 17.2-19.9 s, 5.6 s): draws on in 4 frames."""
    c = s.c
    aid = c.uid('ar')
    s.add(f'<svg class="cv-abs" style="left:0;top:0;z-index:{z}" width="{WW}" height="{WH}" viewBox="{-OX} {-OY} {WW} {WH}">'
          f'<path id="{aid}" d="{d}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/></svg>')
    c.pre.append(f'(()=>{{const p=document.getElementById("{aid}");const L=p.getTotalLength();p.dataset.len=L;gsap.set(p,{{strokeDasharray:L,strokeDashoffset:L}});}})();')
    c.at(f'(()=>{{const p=document.getElementById("{aid}");tl.fromTo(p,{{strokeDashoffset:+p.dataset.len}},{{strokeDashoffset:0,duration:{F(4):.4f},ease:"power1.out",immediateRender:false}},{fr(t):.4f});}})();')
    return aid


def quote_marks(s, t, x0, x1, y, tone='light', z=5):
    """Principle 6 (text-centric): two small quotation marks around the centre of the screen (seen 49.0-51.0 s)."""
    c = s.c
    ids = []
    for x, ch in ((x0, '“'), (x1, '”')):
        q = c.uid('q')
        s.add(f'<span id="{q}" class="cv-quote cv-{tone}" style="left:{x + OX}px;top:{y + OY}px;z-index:{z}">{ch}</span>')
        c.pre.append(f'gsap.set("#{q}",{{opacity:0}});')
        c.at(f'tl.fromTo("#{q}",{{opacity:0}},{{opacity:1,duration:{F(3):.4f},immediateRender:false}},{fr(t):.4f});')
        ids.append(q)
    return ids

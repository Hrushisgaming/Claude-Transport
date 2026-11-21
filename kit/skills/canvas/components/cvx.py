"""cvx.py — the Canvas motion-graphics layer, built on cv_devices and its tokens.
On top of the core look, these add: the chapter roadmap (the blue line through five stops,
returning at every chapter), real screens in a window with a ring drawn on the thing he names, stepped counters, a stacked
share bar, a typed prompt card, spec tiles, a 5-frame blur strip, file cards, a strike, a waveform cut from his real take,
and a video card. Every colour/font is a --cv-* token (assets/cv/tokens.css), every motion is transform/opacity/filter.
All coordinates are FRAME px (1920x1080); a scene's world is offset by OX/OY like cv_devices."""
import json, math
import cv_devices as cv
from cv_devices import F, fr, esc, sfx, OX, OY, W, H, POP, WIPE

try:
    SHOTS = json.load(open('assets/img/shots.json'))    # screens captured for this video: {key: {w, h, boxes: {name: [x, y, w, h]}}}
except FileNotFoundError:
    SHOTS = {}
PORTRAIT = cv.H > cv.W        # set_format('9x16') must run BEFORE this module is imported

CSS = r"""
.cvx-win{position:absolute;overflow:hidden;border-radius:16px;background:var(--cv-dark);box-shadow:0 30px 70px var(--cv-photo-shadow),0 4px 12px var(--cv-photo-shadow)}
.cvx-win.on-dark{box-shadow:0 30px 80px var(--cv-shadow),0 0 0 1px var(--cv-axis)}
.cvx-win .cvx-in{position:absolute;left:0;top:0;transform-origin:0 0}
.cvx-win img{display:block}
.cvx-ring{position:absolute;border:5px solid var(--cv-accent);border-radius:12px;box-shadow:0 0 22px var(--cv-glow),inset 0 0 14px var(--cv-glow-soft);transform-origin:0 50%}
.cvx-chip{position:absolute;transform:translate(-50%,-50%);font-family:var(--cv-sans);font-weight:600;font-size:22px;letter-spacing:.18em;
  padding:10px 20px;border-radius:999px;white-space:nowrap;text-transform:uppercase}
.cvx-chip.ink{color:var(--cv-paper);background:var(--cv-ink)}
.cvx-chip.light{color:var(--cv-ink);background:var(--cv-white)}
.cvx-chip.blue{color:var(--cv-white);background:var(--cv-accent)}
.cvx-stop{position:absolute;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;background:var(--cv-paper);border:6px solid var(--cv-line);box-sizing:border-box}
.cvx-stop.lit{background:var(--cv-line);box-shadow:0 0 0 10px var(--cv-glow-soft),0 0 30px var(--cv-glow)}
.cvx-stopn{position:absolute;transform:translate(-50%,-50%);font-family:var(--cv-sans);font-weight:600;font-size:20px;letter-spacing:.2em;color:var(--cv-line)}
.cvx-stopl{position:absolute;transform:translate(-50%,0);text-align:center;white-space:nowrap;color:var(--cv-ink)}
.cvx-stopl .k{display:block;font-family:var(--cv-sans);font-weight:900;font-size:46px;letter-spacing:-.04em;line-height:1}
.cvx-stopl .k.i{font-family:var(--cv-serif);font-style:italic;letter-spacing:-.01em}
.cvx-num{position:absolute;transform:translate(-50%,-50%);font-family:var(--cv-sans);font-weight:900;letter-spacing:-.05em;line-height:1;white-space:nowrap}
.cvx-num.light{color:var(--cv-white);text-shadow:0 4px 40px var(--cv-shadow)}
.cvx-num.ink{color:var(--cv-ink)}
.cvx-num.blue{color:var(--cv-accent)}
.cvx-num.serif{font-family:var(--cv-serif);font-style:italic;letter-spacing:-.01em}
.cvx-lab{position:absolute;transform:translate(-50%,-50%);font-family:var(--cv-sans);font-weight:600;font-size:22px;letter-spacing:.2em;white-space:nowrap;text-transform:uppercase}
.cvx-lab.light{color:var(--cv-axis)}.cvx-lab.ink{color:var(--cv-ink);opacity:.7}
.cvx-bar{position:absolute;height:64px;transform-origin:0 50%;border-radius:4px}
.cvx-bar.b0{background:var(--cv-accent)}.cvx-bar.b1{background:var(--cv-white)}.cvx-bar.b2{background:var(--cv-axis)}
.cvx-bar.b3{background:var(--cv-blue-deep)}.cvx-bar.b4{background:var(--cv-gline)}.cvx-bar.b5{background:var(--cv-glow-soft)}
.cvx-card{position:absolute;background:var(--cv-photo);border-radius:18px;box-shadow:0 26px 60px var(--cv-photo-shadow),0 3px 10px var(--cv-photo-shadow);box-sizing:border-box}
.cvx-card.dark{background:var(--cv-dark);box-shadow:0 30px 80px var(--cv-shadow),0 0 0 1px var(--cv-axis)}
.cvx-typer{font-family:var(--cv-sans);font-weight:500;font-size:34px;line-height:1.42;color:var(--cv-white);padding:46px 54px}
.cvx-typer .pr{color:var(--cv-ball);font-weight:900;margin-right:.4em}
.cvx-typer .w{opacity:0;position:relative;display:inline-block;margin-right:.26em}
.cvx-typer .hl{position:absolute;left:-4px;right:-4px;top:4px;bottom:2px;background:var(--cv-accent);z-index:-1;transform-origin:0 50%;border-radius:4px}
.cvx-typer .t{position:relative}
.cvx-caret{display:inline-block;width:16px;height:36px;background:var(--cv-ball);vertical-align:-6px}
.cvx-tile{position:absolute;width:330px;height:250px;margin:-125px 0 0 -165px;border-radius:18px;background:var(--cv-dark);box-shadow:0 0 0 1px var(--cv-axis),0 24px 60px var(--cv-shadow);
  display:flex;flex-direction:column;justify-content:space-between;padding:28px 30px;box-sizing:border-box}
.cvx-tile .tl{font-family:var(--cv-sans);font-weight:600;font-size:20px;letter-spacing:.22em;color:var(--cv-axis);text-transform:uppercase}
.cvx-tile .tv{font-family:var(--cv-sans);font-weight:900;font-size:64px;letter-spacing:-.04em;color:var(--cv-white);line-height:1}
.cvx-tile .sw{width:100%;height:70px;border-radius:10px}
.cvx-file{position:absolute;display:flex;align-items:center;gap:22px;padding:26px 34px 26px 26px;background:var(--cv-photo);border-radius:18px;
  box-shadow:0 26px 60px var(--cv-photo-shadow),0 3px 10px var(--cv-photo-shadow);transform:translate(-50%,-50%);white-space:nowrap}
.cvx-file .ic{width:70px;height:86px;border-radius:10px;background:var(--cv-accent);position:relative;flex:none}
.cvx-file .ic.ink{background:var(--cv-ink)}
.cvx-file .ic:after{content:"";position:absolute;right:0;top:0;width:22px;height:22px;background:var(--cv-paper);border-bottom-left-radius:8px}
.cvx-file .ic span{position:absolute;left:0;right:0;bottom:12px;text-align:center;font-family:var(--cv-sans);font-weight:900;font-size:17px;color:var(--cv-white);letter-spacing:.06em}
.cvx-file .nm{font-family:var(--cv-sans);font-weight:600;font-size:32px;color:var(--cv-ink);letter-spacing:-.01em}
.cvx-file .sb{font-family:var(--cv-sans);font-weight:500;font-size:22px;color:var(--cv-ink);opacity:.55;margin-top:4px}
.cvx-strike{position:absolute;height:10px;background:var(--cv-accent);border-radius:5px;transform-origin:0 50%;box-shadow:0 0 18px var(--cv-glow)}
.cvx-wave rect{fill:var(--cv-ink)}
.cvx-wave .cut{fill:var(--cv-accent)}
.cvx-band{position:absolute;background:var(--cv-glow-soft);border:3px dashed var(--cv-accent);border-radius:10px;transform-origin:50% 50%}
.cvx-blurw{position:absolute;transform:translate(-50%,-50%);font-family:var(--cv-sans);font-weight:900;font-size:96px;letter-spacing:-.045em;color:var(--cv-white);white-space:nowrap}
.cvx-rec{position:absolute;font-family:var(--cv-sans);color:var(--cv-ink);white-space:nowrap}
.cvx-rec .row{position:absolute;left:0;right:0;display:flex;justify-content:space-between;font-size:32px;font-weight:500}
.cvx-rec .row b{font-weight:900}
.cvx-rec .rule{position:absolute;left:0;right:0;height:2px;background:var(--cv-ink);opacity:.25}
"""


def clamp(X, Y, S):
    """Keep a camera move inside the world: at scale S the world (1.2x the frame, centred) covers the frame only while
    |x| <= 1152*S - 960 and |y| <= 648*S - 540 (a push to the first roadmap stop showed the world's edge)."""
    mx, my = cv.WW / 2 * S - cv.W / 2, cv.WH / 2 * S - cv.H / 2
    return max(-mx, min(mx, X)), max(-my, min(my, Y)), S


def _pop(c, el, t, frm_scale=1.06, blur=18, dur=POP):
    c.pre.append(f'gsap.set("{el}",{{opacity:0,filter:"blur({blur}px)",scale:{frm_scale}}});')
    c.at(f'tl.fromTo("{el}",{{opacity:0,filter:"blur({blur}px)",scale:{frm_scale}}},{{opacity:1,filter:"blur(0px)",scale:1,'
         f'duration:{F(dur):.4f},ease:"power2.out",immediateRender:false}},{fr(t):.4f});')


def _show(c, el, t, t_off=None):
    c.pre.append(f'gsap.set("{el}",{{opacity:0}});')
    c.at(f'tl.set("{el}",{{opacity:1}},{fr(t):.4f});')
    if t_off is not None:
        c.at(f'tl.set("{el}",{{opacity:0}},{fr(t_off):.4f});')


def _wipe(c, el, t, frames=WIPE):
    c.pre.append(f'gsap.set("{el}",{{scaleX:0}});')
    c.at(f'tl.fromTo("{el}",{{scaleX:0}},{{scaleX:1,duration:{F(frames):.4f},ease:"power2.out",immediateRender:false}},{fr(t):.4f});')


# ---------------------------------------------------------------------------------------------------------------- screens
class Shot:
    """A real screen (the creator's own app, a web page) in a rounded window. Drops onto paper like a photo, or blur-pops on
    dark. ring(t, box) draws an accent ring onto the thing he names (box from the capture's DOM, in the JPG's px);
    scroll(t, dur, y) slides the page inside the window; at(box) gives the box centre in FRAME px for camera moves."""

    def __init__(self, s, key, t, x, y, w, h=None, rot=0.0, enter='drop', z=3, sound=True, y0=0):
        self.s, self.c = s, s.c
        info = SHOTS[key]
        self.k = w / info['w']
        self.w, self.h = w, (h if h else info['h'] * self.k)
        self.x, self.y, self.boxes, self.scroll_y = x, y, info['boxes'], y0
        self.id = self.c.uid('win')
        self.inner = self.id + 'i'
        self.kids = []
        self.src = f'assets/img/{key}.jpg'
        self.t, self.rot, self.enter, self.z, self.sound = t, rot, enter, z, sound
        self.c.pre.append(f'gsap.set("#{self.inner}",{{y:{-y0 * self.k:.1f}}});')

    def at(self, box, dy=0.0):
        bx, by, bw, bh = self.boxes[box] if isinstance(box, str) else box
        return (self.x - self.w / 2 + (bx + bw / 2) * self.k, self.y - self.h / 2 + (by + bh / 2 - self.scroll_y) * self.k + dy)

    def ring(self, t, box, pad=10):
        bx, by, bw, bh = self.boxes[box] if isinstance(box, str) else box
        rid = self.c.uid('ring')
        self.kids.append(f'<div id="{rid}" class="cvx-ring" style="left:{bx * self.k - pad:.0f}px;top:{by * self.k - pad:.0f}px;'
                         f'width:{bw * self.k + 2 * pad:.0f}px;height:{bh * self.k + 2 * pad:.0f}px"></div>')
        _wipe(self.c, f'#{rid}', t)
        return rid

    def scroll(self, t, dur, y, ease='power2.inOut'):
        self.c.at(f'tl.fromTo("#{self.inner}",{{y:{-self.scroll_y * self.k:.1f}}},{{y:{-y * self.k:.1f},duration:{dur:.4f},ease:"{ease}",'
                  f'immediateRender:false}},{fr(t):.4f});')
        self.scroll_y = y

    def close(self):
        c, s = self.c, self.s
        on_dark = ' on-dark' if self.enter == 'pop' else ''
        s.add(f'<div id="{self.id}" class="cvx-win{on_dark}" style="left:{self.x - self.w / 2 + OX:.0f}px;top:{self.y - self.h / 2 + OY:.0f}px;'
              f'width:{self.w:.0f}px;height:{self.h:.0f}px;z-index:{self.z}"><div id="{self.inner}" class="cvx-in">'
              f'<img src="{self.src}" style="width:{self.w:.0f}px" alt="">{"".join(self.kids)}</div></div>')
        if self.enter == 'drop':
            c.pre.append(f'gsap.set("#{self.id}",{{opacity:0,rotation:{self.rot + 2},y:-26,scale:1.03}});')
            c.at(f'tl.fromTo("#{self.id}",{{opacity:0}},{{opacity:1,duration:{F(1):.4f},immediateRender:false}},{fr(self.t):.4f});')
            c.at(f'tl.fromTo("#{self.id}",{{rotation:{self.rot + 2},y:-26,scale:1.03}},{{rotation:{self.rot},y:0,scale:1,duration:{F(6):.4f},'
                 f'ease:"power3.out",immediateRender:false}},{fr(self.t):.4f});')
            if self.sound:
                sfx(c, self.t, 'tick', 0.8)
        else:
            _pop(c, f'#{self.id}', self.t, 1.04, 16)
            if self.sound:
                sfx(c, self.t, 'pop')


# ---------------------------------------------------------------------------------------------------------------- roadmap
# The chapter spine. Set this video's own stops with set_stops([(small, key, 'b'|'i'), ...]) before the first roadmap().
STOP_LABELS = [('The', 'mechanism', 'b'), ('How long it', 'took', 'i'), ('How to', 'use it', 'b'), ('What it', 'costs', 'i'), ('How to', 'install', 'b')]
if PORTRAIT:   # 9:16: the line runs top to bottom, the stops zig-zag
    _XY = [(330, 420), (750, 700), (330, 980), (750, 1260), (330, 1540)]
    ROAD = 'M 540,-120 C 540,200 330,260 330,420 S 750,560 750,700 S 330,840 330,980 S 750,1120 750,1260 S 330,1400 330,1540 S 540,1900 540,2100'
else:
    _XY = [(300, 560), (640, 470), (980, 560), (1320, 470), (1660, 560)]
    ROAD = 'M -120,620 C 60,620 150,560 300,560 S 520,470 640,470 S 860,560 980,560 S 1200,470 1320,470 S 1540,560 1660,560 S 1900,620 2080,620'
STOPS = [(x, y, a, b, st) for (x, y), (a, b, st) in zip(_XY, STOP_LABELS)]


def set_stops(labels):
    """labels = up to 5 (small, key word, 'b' bold | 'i' italic): this video's chapters, in order."""
    global STOPS
    STOPS = [(x, y, a, b, st) for (x, y), (a, b, st) in zip(_XY, labels)]


def roadmap(c, t0, t1, active=None, draw=None, push=None, sound=True, lights=None):
    """The chapter spine: one thick blue line on paper through five stops. In the intro it
    draws on (draw = a time per stop) and the stops light one by one as he lists them (lights = [(stop, time)]), the camera
    travelling to each; after that it returns already drawn at every chapter, pushes to that chapter's stop and lights it."""
    s = cv.Scene(c, t0, t1, ground='paper')
    if sound:
        sfx(c, t0, 'tick')
    if active is not None and push is not None:
        lights = [(i, t0 + 0.02) for i in range(active)] + [(active, push)]
    lights = lights or []
    if draw:
        segs = [(t0, 0.0)] + [(tt, (i + 1) / 5.4) for i, tt in enumerate(draw)] + [(draw[-1] + 0.3, 1.0)]
        cv.line(s, ROAD, t0, t1, width=14, segments=segs)
    else:
        cv.line(s, ROAD, t0, t0 + F(1), width=14)
    for i, (x, y, small, key, st) in enumerate(STOPS):
        sid, nid, lid = c.uid('stop'), c.uid('sn'), c.uid('sl')
        s.add(f'<div id="{sid}" class="cvx-stop" style="left:{x + OX}px;top:{y + OY}px;z-index:3"></div>')
        s.add(f'<div id="{nid}" class="cvx-stopn" style="left:{x + OX}px;top:{y - 62 + OY}px;z-index:3">{i + 1:02d}</div>')
        k = 'k i' if st == 'i' else 'k'
        s.add(f'<div id="{lid}" class="cvx-stopl" style="left:{x + OX}px;top:{y + 44 + OY}px;z-index:3">'
              f'<span class="cv-s" style="display:block">{esc(small)}</span><span class="{k}">{esc(key)}</span></div>')
        ta = draw[i] if draw else t0
        for el in (sid, nid, lid):
            _pop(c, f'#{el}', ta, 1.1, 14)
    for n, (i, t) in enumerate(lights):
        x, y = STOPS[i][0], STOPS[i][1]
        hid = c.uid('lit')
        s.add(f'<div id="{hid}" class="cvx-stop lit" style="left:{x + OX}px;top:{y + OY}px;z-index:4"></div>')
        if t - t0 < 0.1:
            _show(c, f'#{hid}', t0)
            continue
        _pop(c, f'#{hid}', t, 1.6, 6, 8)
        X, Y, S = clamp(*s.look(x, y + 30, 1.35))
        s.move(t - 0.25, 0.55, x=X, y=Y, s=S, ease='power3.inOut', smear=30)
        sfx(c, t - 0.25, 'swish')
    s.close()
    return s


# ---------------------------------------------------------------------------------------------------------------- numbers
def counter(s, times, values, x, y, size=260, tone='light', label=None, label_dy=None, serif=False, t_end=None):
    """A number that ticks (stepped, one value per given time). values[i] shows from times[i] to times[i+1]."""
    c = s.c
    ids = []
    cls = f'cvx-num {tone}' + (' serif' if serif else '')
    for i, (t, v) in enumerate(zip(times, values)):
        nid = c.uid('n')
        s.add(f'<div id="{nid}" class="{cls}" style="left:{x + OX}px;top:{y + OY}px;font-size:{size}px;z-index:4">{esc(v)}</div>')
        nxt = times[i + 1] if i + 1 < len(times) else t_end
        if i == 0 and len(values) == 1:
            _pop(c, f'#{nid}', t, 1.08, 16)
            if nxt is not None:
                c.at(f'tl.set("#{nid}",{{opacity:0}},{fr(nxt):.4f});')
        else:
            _show(c, f'#{nid}', t, nxt)     # stepped values never tween: a pop under a 2-frame step overlaps itself (seek backwards)
        ids.append(nid)
    if label:
        lid = c.uid('lb')
        s.add(f'<div id="{lid}" class="cvx-lab {tone if tone != "blue" else "ink"}" style="left:{x + OX}px;top:{y + (label_dy or size * 0.62) + OY}px;z-index:4">{esc(label)}</div>')
        _pop(c, f'#{lid}', times[0], 1.0, 6, 4)
    return ids


def ticks(t0, t1, n):
    """n stepped times from t0 to t1 on 2s (every value holds >= 2 frames), easing out."""
    out = []
    for i in range(n):
        u = 1 - (1 - i / max(1, n - 1)) ** 2
        out.append(t0 + (t1 - t0) * u)
    q = [round(v * 15) / 15 for v in out]
    for i in range(1, len(q)):
        q[i] = max(q[i], q[i - 1] + 2 / 30)
    return q


# ---------------------------------------------------------------------------------------------------------------- bars
def sharebar(s, parts, x, y, w, tone='light'):
    """A stacked share bar that builds part by part: parts = [(t, fraction, label, cls_index)]. Labels sit under each part."""
    c = s.c
    acc = 0.0
    for t, f, lab, k in parts:
        bid, lid = c.uid('bar'), c.uid('bl')
        bx = x + acc * w
        s.add(f'<div id="{bid}" class="cvx-bar b{k}" style="left:{bx + OX:.0f}px;top:{y - 32 + OY}px;width:{f * w - 6:.0f}px;z-index:3"></div>')
        s.add(f'<div id="{lid}" class="cvx-lab {tone}" style="left:{bx + f * w / 2 + OX:.0f}px;top:{y + 78 + OY}px;z-index:3;font-size:19px">{esc(lab)}</div>')
        _wipe(c, f'#{bid}', t, 8)
        _pop(c, f'#{lid}', t + 0.1, 1.0, 6, 4)
        acc += f


# ---------------------------------------------------------------------------------------------------------------- typed prompt
def typer(s, x, y, w, h, words, marks=(), prompt='>', z=3, enter_t=None):
    """A dark terminal card (Claude Code) on paper; words = [(text, t)] appear on their times (typing, word by word);
    marks = [(t, first_word_index, last_word_index)] wipe an accent highlighter behind a phrase."""
    c = s.c
    cid = c.uid('typ')
    spans = []
    ids = []
    hl = {}
    for t, a, b in marks:
        for i in range(a, b + 1):
            hl[i] = t
    for i, (wtxt, t) in enumerate(words):
        wid = c.uid('tw')
        ids.append((wid, t))
        inner = esc(wtxt)
        if i in hl:
            hid = wid + 'h'
            inner = f'<span id="{hid}" class="hl"></span><span class="t">{inner}</span>'
            _wipe(c, f'#{hid}', hl[i], 6)
        spans.append(f'<span id="{wid}" class="w">{inner}</span>')
    s.add(f'<div id="{cid}" class="cvx-card dark cvx-typer" style="left:{x - w / 2 + OX:.0f}px;top:{y - h / 2 + OY:.0f}px;width:{w}px;height:{h}px;'
          f'z-index:{z}"><span class="pr">{esc(prompt)}</span>{"".join(spans)}</div>')
    _pop(c, f'#{cid}', enter_t if enter_t is not None else (words[0][1] - 0.2 if words else s.t0), 1.03, 10)
    for wid, t in ids:
        c.at(f'tl.set("#{wid}",{{opacity:1}},{fr(t):.4f});')
    return cid


# ---------------------------------------------------------------------------------------------------------------- tiles, chips, files
def tile(s, t, x, y, label, value=None, swatch=None, z=3):
    c = s.c
    tid = c.uid('tile')
    body = f'<div class="sw" style="background:{swatch}"></div>' if swatch else f'<div class="tv">{esc(value)}</div>'
    s.add(f'<div id="{tid}" class="cvx-tile" style="left:{x + OX}px;top:{y + OY}px;z-index:{z}"><div class="tl">{esc(label)}</div>{body}</div>')
    _pop(c, f'#{tid}', t, 1.08, 18)
    return tid


def chip(s, t, text, x, y, tone='ink', z=6):
    c = s.c
    cid = c.uid('chip')
    s.add(f'<div id="{cid}" class="cvx-chip {tone}" style="left:{x + OX}px;top:{y + OY}px;z-index:{z}">{esc(text)}</div>')
    _pop(c, f'#{cid}', t, 1.0, 8, 4)
    return cid


def filecard(s, t, x, y, name, sub, ext, ink=False, z=4, sound=True):
    c = s.c
    fid = c.uid('file')
    s.add(f'<div id="{fid}" class="cvx-file" style="left:{x + OX}px;top:{y + OY}px;z-index:{z}"><div class="ic{" ink" if ink else ""}"><span>{esc(ext)}</span></div>'
          f'<div><div class="nm">{esc(name)}</div><div class="sb">{esc(sub)}</div></div></div>')
    c.pre.append(f'gsap.set("#{fid}",{{opacity:0,y:-26,rotation:2}});')
    c.at(f'tl.fromTo("#{fid}",{{opacity:0,y:-26,rotation:2}},{{opacity:1,y:0,rotation:0,duration:{F(6):.4f},ease:"power3.out",immediateRender:false}},{fr(t):.4f});')
    if sound:
        sfx(c, t, 'tick', 0.8)
    return fid


def strike(s, t, x, y, w, rot=-8, z=6):
    c = s.c
    sid = c.uid('stk')
    s.add(f'<div style="position:absolute;left:{x + OX}px;top:{y + OY}px;transform:rotate({rot}deg);transform-origin:0 50%;z-index:{z}">'
          f'<div id="{sid}" class="cvx-strike" style="position:relative;width:{w}px"></div></div>')
    _wipe(c, f'#{sid}', t, 7)
    return sid


def band(s, t, x, y, w, h, z=5):
    c = s.c
    bid = c.uid('band')
    s.add(f'<div id="{bid}" class="cvx-band" style="left:{x + OX}px;top:{y + OY}px;width:{w}px;height:{h}px;z-index:{z}"></div>')
    _pop(c, f'#{bid}', t, 1.06, 6, 6)
    return bid


# ---------------------------------------------------------------------------------------------------------------- blur strip
def blurstrip(s, t, word, x, y, gap=330):
    """'Every word blurs in, 5 frames': the same word at frames 1..5 of its blur-in (16 px -> 0, scale 1.10 -> 1), left to right,
    each appearing 2 frames after the last, with its frame number under it."""
    c = s.c
    for i in range(5):
        u = i / 4
        b = 16 * (1 - u) ** 1.6
        sc = 1 + 0.10 * (1 - u) ** 1.6
        op = 0.25 + 0.75 * u
        wid, lid = c.uid('bw'), c.uid('bl')
        xx = x + (i - 2) * gap
        s.add(f'<div id="{wid}" class="cvx-blurw" style="left:{xx + OX}px;top:{y + OY}px;filter:blur({b:.1f}px);z-index:3">'
              f'<span style="display:inline-block;transform:scale({sc:.3f});opacity:{op:.2f}">{esc(word)}</span></div>')
        s.add(f'<div id="{lid}" class="cvx-lab light" style="left:{xx + OX}px;top:{y + 110 + OY}px;z-index:3">frame {i + 1}</div>')
        _show(c, f'#{wid}', t + i * 2 / 30)
        _show(c, f'#{lid}', t + i * 2 / 30)


# ---------------------------------------------------------------------------------------------------------------- waveform
def waveform(s, t, peaks, x, y, w, h, cuts=(), cut_t=None, collapse_t=None, z=3):
    """His real take as a waveform (peaks = list of 0..1); cuts = [(i0, i1)] bar ranges that are silences/mistakes: they turn
    accent blue at cut_t and collapse (scaleY 0) at collapse_t."""
    c = s.c
    n = len(peaks)
    bw = w / n
    wid = c.uid('wav')
    rects = []
    cut_ids = []
    for i, p in enumerate(peaks):
        hh = max(4, p * h)
        inc = any(a <= i < b for a, b in cuts)
        rid = f'{wid}r{i}'
        rects.append(f'<rect id="{rid}" class="{"cut" if inc else ""}" x="{i * bw:.1f}" y="{(h - hh) / 2:.1f}" width="{bw * 0.62:.1f}" height="{hh:.1f}" rx="2"/>')
        if inc:
            cut_ids.append(rid)
    s.add(f'<svg id="{wid}" class="cvx-wave" style="position:absolute;left:{x - w / 2 + OX:.0f}px;top:{y - h / 2 + OY:.0f}px;z-index:{z};overflow:visible" '
          f'width="{w:.0f}" height="{h}" viewBox="0 0 {w:.0f} {h}">{"".join(rects)}</svg>')
    _pop(c, f'#{wid}', t, 1.02, 10)
    if cut_ids:
        sel = ','.join('#' + r for r in cut_ids)
        c.pre.append(f'gsap.set("{sel}",{{fill:"var(--cv-ink)"}});')
        if cut_t is not None:
            c.at(f'tl.set("{sel}",{{fill:"var(--cv-accent)"}},{fr(cut_t):.4f});')
        if collapse_t is not None:
            c.pre.append(f'gsap.set("{sel}",{{transformOrigin:"50% 50%"}});')
            c.at(f'tl.fromTo("{sel}",{{scaleY:1,opacity:1}},{{scaleY:0,opacity:0,duration:{F(6):.4f},ease:"power2.in",immediateRender:false}},{fr(collapse_t):.4f});')


# ---------------------------------------------------------------------------------------------------------------- video card
def vidcard(s, src, t0, t1, media_start, x, y, w, h, radius=18, z=3, enter='pop', label=None, tone='ink'):
    """A muted video in a card inside a scene. Nested media takes COMPOSITION time (memory: nested-media-composition-time),
    so data-start = the scene start and data-media-start is shifted to match."""
    c = s.c
    vid = c.uid('vc')
    cid = c.uid('vcard')
    ms = media_start - (t0 - s.t0)
    st = s.t0
    s.add(f'<div id="{cid}" class="cvx-card{" dark" if tone == "light" else ""}" style="left:{x - w / 2 + OX:.0f}px;top:{y - h / 2 + OY:.0f}px;width:{w}px;height:{h}px;'
          f'overflow:hidden;border-radius:{radius}px;z-index:{z}"><video id="{vid}" class="clip" src="{src}" muted playsinline '
          f'data-start="{st:.4f}" data-duration="{cv.dstr(st, s.t1)}" data-media-start="{max(0.0, ms):.4f}" '
          f'style="position:absolute;left:0;top:0;width:{w}px;height:{h}px;object-fit:cover"></video></div>')
    if enter == 'pop':
        _pop(c, f'#{cid}', t0, 1.04, 14)
    else:
        _show(c, f'#{cid}', t0)
    if label:
        chip(s, t0 + 0.1, label, x, y - h / 2 - 44, tone='ink' if tone == 'ink' else 'light')
    return cid


# ---------------------------------------------------------------------------------------------------------------- receipt
def receipt(s, x, y, w, rows, total=None, z=3, t_card=None):
    """A paper receipt card; rows = [(t, left, right)] tick in on their words; total = (t, left, right) under a rule."""
    c = s.c
    rid = c.uid('rcpt')
    hh = 120 + 74 * len(rows) + (110 if total else 0)
    inner = []
    for i, (t, l, r) in enumerate(rows):
        oid = c.uid('rr')
        inner.append(f'<div id="{oid}" class="row" style="top:{60 + i * 74}px"><span>{esc(l)}</span><b>{esc(r)}</b></div>')
        _pop(c, f'#{oid}', t, 1.0, 8, 4)
        sfx(c, t, 'tick', 0.45)
    if total:
        t, l, r = total
        tid, lid = c.uid('rt'), c.uid('rl')
        top = 60 + len(rows) * 74 + 18
        inner.append(f'<div id="{lid}" class="rule" style="top:{top}px"></div>')
        inner.append(f'<div id="{tid}" class="row" style="top:{top + 24}px;font-size:52px"><b>{esc(l)}</b><b style="color:var(--cv-accent)">{esc(r)}</b></div>')
        _pop(c, f'#{tid}', t, 1.06, 12)
        _show(c, f'#{lid}', t)
    s.add(f'<div id="{rid}" class="cvx-card" style="left:{x - w / 2 + OX:.0f}px;top:{y - hh / 2 + OY:.0f}px;width:{w}px;height:{hh}px;z-index:{z}">'
          f'<div class="cvx-rec" style="left:56px;right:56px;top:0;bottom:0">{"".join(inner)}</div></div>')
    c.pre.append(f'gsap.set("#{rid}",{{opacity:0,y:-30,rotation:-2}});')
    tc = t_card if t_card is not None else rows[0][0] - 0.15
    c.at(f'tl.fromTo("#{rid}",{{opacity:0,y:-30,rotation:-2}},{{opacity:1,y:0,rotation:-1,duration:{F(6):.4f},ease:"power3.out",immediateRender:false}},{fr(tc):.4f});')
    return rid


# =========================================================================================================== explainer devices
# A creator's note on a first cut: "too many paintings and less motion graphics… change the colour
# to respect this style". These port MG V2's explainer vocabulary (icons that draw themselves with a flow line, the versus card
# whose winner steps forward, tile grids, stat cards) and MG V1's chart hits (bars, donut, line) into the canvas tokens: ink on
# paper / white on dark, ONE accent (--cv-accent), Inter for labels, Playfair italic for the key word. Lucide icons (ISC licence,
# copied from motion-graphics-v2) draw stroke by stroke.
import re as _re
import os as _os

CSS2 = r"""
.cvx-ic{position:absolute;border-radius:50%;display:flex;align-items:center;justify-content:center;box-sizing:border-box}
.cvx-ic.ink{background:var(--cv-photo);box-shadow:0 22px 50px var(--cv-photo-shadow),0 3px 8px var(--cv-photo-shadow);color:var(--cv-ink)}
.cvx-ic.light{background:var(--cv-dark);box-shadow:0 0 0 2px var(--cv-axis),0 24px 60px var(--cv-shadow);color:var(--cv-white)}
.cvx-ic.acc{background:var(--cv-accent);box-shadow:0 0 0 10px var(--cv-glow-soft),0 24px 60px var(--cv-glow-soft);color:var(--cv-white)}
.cvx-ic svg{overflow:visible}
.cvx-iclab{position:absolute;transform:translate(-50%,0);text-align:center;white-space:nowrap;font-family:var(--cv-sans);font-weight:700;font-size:42px;letter-spacing:-.02em;line-height:1.1}
.cvx-iclab.ink{color:var(--cv-ink)}.cvx-iclab.light{color:var(--cv-white)}
.cvx-iclab small{display:block;font-weight:500;font-size:28px;opacity:.6;margin-top:8px}
.cvx-persp{position:absolute;perspective:1800px}
.cvx-vs{position:absolute;border-radius:26px;box-sizing:border-box;padding:70px 56px 50px;display:flex;flex-direction:column;align-items:center;gap:24px;text-align:center}
.cvx-vs.ink{background:var(--cv-photo);box-shadow:0 30px 70px var(--cv-photo-shadow),0 4px 12px var(--cv-photo-shadow);color:var(--cv-ink)}
.cvx-vs.light{background:var(--cv-dark);box-shadow:0 0 0 2px var(--cv-axis),0 30px 80px var(--cv-shadow);color:var(--cv-white)}
.cvx-vs .ln{font-family:var(--cv-sans);font-weight:700;font-size:54px;letter-spacing:-.03em;line-height:1.05}
.cvx-vs .ln.i{font-family:var(--cv-serif);font-style:italic;font-weight:900;letter-spacing:-.01em}
.cvx-vs .ln.mute{font-weight:500;font-size:36px;opacity:.65}
.cvx-vstag{position:absolute;transform:translate(-50%,-50%);display:flex;align-items:center;gap:16px;padding:16px 34px;border-radius:999px;white-space:nowrap;
  font-family:var(--cv-sans);font-weight:700;font-size:36px;letter-spacing:-.01em}
.cvx-vstag.ink{background:var(--cv-ink);color:var(--cv-paper)}.cvx-vstag.light{background:var(--cv-white);color:var(--cv-ink)}
.cvx-vstag i{width:16px;height:16px;border-radius:50%;background:var(--cv-accent)}
.cvx-uline{position:absolute;height:10px;border-radius:5px;background:var(--cv-accent);box-shadow:0 0 18px var(--cv-glow);transform-origin:0 50%}
.cvx-tile2{position:absolute;border-radius:22px;box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;text-align:center}
.cvx-tile2.ink{background:var(--cv-photo);box-shadow:0 22px 50px var(--cv-photo-shadow),0 3px 8px var(--cv-photo-shadow);color:var(--cv-ink)}
.cvx-tile2.light{background:var(--cv-dark);box-shadow:0 0 0 2px var(--cv-axis),0 24px 60px var(--cv-shadow);color:var(--cv-white)}
.cvx-tile2 .tl{font-family:var(--cv-sans);font-weight:700;font-size:36px;letter-spacing:-.02em;line-height:1.1;padding:0 18px}
.cvx-tile2 .tl small{display:block;font-weight:500;font-size:24px;opacity:.6;margin-top:6px}
.cvx-head{position:absolute;transform:translate(-50%,-50%);white-space:nowrap;text-align:center}
.cvx-head .s{font-family:var(--cv-sans);font-weight:500;font-size:34px;display:block;margin-bottom:6px}
.cvx-head .k{font-family:var(--cv-serif);font-style:italic;font-weight:900;font-size:96px;letter-spacing:-.01em;line-height:1}
.cvx-head.ink{color:var(--cv-ink)}.cvx-head.ink .k{color:var(--cv-accent)}.cvx-head.light{color:var(--cv-white)}
.cvx-bar2{position:absolute;border-radius:12px 12px 4px 4px;transform-origin:50% 100%}
.cvx-bar2.n{background:var(--cv-axis)}.cvx-bar2.ink-n{background:var(--cv-ink);opacity:.18}.cvx-bar2.a{background:var(--cv-accent);box-shadow:0 0 30px var(--cv-glow-soft)}
.cvx-blab{position:absolute;transform:translate(-50%,0);text-align:center;white-space:nowrap;font-family:var(--cv-sans);font-weight:600;font-size:28px}
.cvx-blab.ink{color:var(--cv-ink)}.cvx-blab.light{color:var(--cv-white)}
.cvx-bval{position:absolute;transform:translate(-50%,-100%);font-family:var(--cv-sans);font-weight:900;font-size:56px;letter-spacing:-.04em;white-space:nowrap}
.cvx-bval.ink{color:var(--cv-ink)}.cvx-bval.light{color:var(--cv-white)}.cvx-bval.a{color:var(--cv-accent)}
.cvx-axisl{position:absolute;height:3px;transform-origin:0 50%}
.cvx-axisl.ink{background:var(--cv-ink);opacity:.35}.cvx-axisl.light{background:var(--cv-axis)}
.cvx-check{position:absolute;display:flex;align-items:center;gap:30px;white-space:nowrap;font-family:var(--cv-sans);font-weight:600;font-size:44px;letter-spacing:-.02em}
.cvx-check.ink{color:var(--cv-ink)}.cvx-check.light{color:var(--cv-white)}
.cvx-check .bx{width:64px;height:64px;border-radius:16px;flex:none;position:relative;box-sizing:border-box}
.cvx-check.ink .bx{border:4px solid var(--cv-ink)}.cvx-check.light .bx{border:4px solid var(--cv-axis)}
.cvx-check .fill{position:absolute;inset:-4px;border-radius:16px;background:var(--cv-accent)}
.cvx-check .n{font-weight:500;font-size:30px;opacity:.5;width:44px}
"""

_ICONS = {}


def icon_svg(name, size, sw=2.0, cls=''):
    """A Lucide icon's inner elements, scaled to `size` px, every stroke element given an id stem for the draw-on."""
    if name not in _ICONS:
        t = open(f'assets/icons/{name}.svg').read()
        _ICONS[name] = _re.sub(r'<!--.*?-->', '', t[t.index('>', t.index('<svg')) + 1:t.rindex('</svg>')], flags=_re.S).strip()
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{_ICONS[name]}</svg>')


def _draw_svg(c, sel, t, frames=14):
    """Stroke-draw every geometry element inside `sel` (path/circle/rect/line/polyline), staggered a little."""
    c.pre.append(f'document.querySelectorAll("{sel} path,{sel} circle,{sel} rect,{sel} line,{sel} polyline,{sel} ellipse,{sel} polygon").forEach(e=>{{'
                 f'const L=e.getTotalLength?e.getTotalLength():60;e.dataset.len=L;gsap.set(e,{{strokeDasharray:L+" "+(L+2),strokeDashoffset:L}});}});')
    c.at(f'document.querySelectorAll("{sel} path,{sel} circle,{sel} rect,{sel} line,{sel} polyline,{sel} ellipse,{sel} polygon").forEach((e,k)=>{{'
         f'tl.fromTo(e,{{strokeDashoffset:+e.dataset.len}},{{strokeDashoffset:0,duration:{F(frames):.4f},ease:"power2.inOut",immediateRender:false}},{fr(t):.4f}+k*{F(2):.4f});}});')


def _spring_in(c, el, t, frm=0.6, dur=12):
    c.pre.append(f'gsap.set("{el}",{{opacity:0,scale:{frm}}});')
    c.at(f'tl.fromTo("{el}",{{opacity:0,scale:{frm}}},{{opacity:1,scale:1,duration:{F(dur):.4f},ease:"back.out(1.8)",immediateRender:false}},{fr(t):.4f});')


def icon(s, name, t, x, y, size=210, tone='ink', label=None, sub=None, label_t=None, z=4, sound=False):
    """MG V2's self-drawing icon: a round card springs in, then the Lucide icon draws itself stroke by stroke; the spoken word under it."""
    c = s.c
    iid = c.uid('ic')
    s.add(f'<div id="{iid}" class="cvx-ic {tone}" style="left:{x - size / 2 + OX:.0f}px;top:{y - size / 2 + OY:.0f}px;width:{size}px;height:{size}px;z-index:{z}">'
          f'{icon_svg(name, int(size * 0.5), 2.0)}</div>')
    _spring_in(c, f'#{iid}', t)
    _draw_svg(c, f'#{iid}', t + 0.12)
    if label:
        lid = c.uid('il')
        lt = 'light' if tone == 'light' else 'ink'
        sub_h = f'<small>{esc(sub)}</small>' if sub else ''
        s.add(f'<div id="{lid}" class="cvx-iclab {lt}" style="left:{x + OX:.0f}px;top:{y + size / 2 + 26 + OY:.0f}px;z-index:{z}">{esc(label)}{sub_h}</div>')
        _pop(c, f'#{lid}', label_t if label_t is not None else t + 0.15, 1.0, 10, 5)
    if sound:
        sfx(c, t, 'pop', 0.8)
    return iid


def arrow(s, t, x0, y0, x1, y1, tone='acc', z=3, dur=None, bend=0):
    """The flow line between two icons: an accent stroke that draws on, with a small head."""
    c = s.c
    aid = c.uid('ar')
    col = 'var(--cv-accent)' if tone == 'acc' else ('var(--cv-ink)' if tone == 'ink' else 'var(--cv-axis)')
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - bend
    ang = math.atan2(y1 - my, x1 - mx)
    hx1, hy1 = x1 - 26 * math.cos(ang - 0.5), y1 - 26 * math.sin(ang - 0.5)
    hx2, hy2 = x1 - 26 * math.cos(ang + 0.5), y1 - 26 * math.sin(ang + 0.5)
    s.add(f'<svg id="{aid}" class="cv-abs" style="left:0;top:0;z-index:{z};filter:drop-shadow(0 0 6px var(--cv-glow-soft))" width="{cv.WW}" height="{cv.WH}" '
          f'viewBox="{-OX} {-OY} {cv.WW} {cv.WH}"><path d="M {x0},{y0} Q {mx},{my} {x1},{y1}" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round"/>'
          f'<path d="M {hx1:.1f},{hy1:.1f} L {x1},{y1} L {hx2:.1f},{hy2:.1f}" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    _draw_svg(c, f'#{aid}', t, frames=dur or 10)
    return aid


def icons_flow(s, items, y=None, x0=None, x1=None, tone='ink', size=None, flow=True):
    """items = [(icon, label, sub, t)]: the icons appear on their words left to right, a flow arrow drawing into each next one."""
    y = cv.H * 0.43 if y is None else y
    size = size or (190 if PORTRAIT else 210)
    x0 = cv.W * (0.2 if PORTRAIT else 0.135) if x0 is None else x0
    x1 = cv.W * (0.8 if PORTRAIT else 0.865) if x1 is None else x1
    n = len(items)
    if PORTRAIT and n > 2:      # 9:16: the flow runs top to bottom, the words beside nothing (under each icon)
        ys = [cv.H * 0.16 + (cv.H * 0.58) * i / max(1, n - 1) for i in range(n)]
        for i, (nm, lab, sub, t) in enumerate(items):
            icon(s, nm, t, cv.W / 2, ys[i], size, tone, lab, sub)
            if flow and i:
                arrow(s, t - 0.12, cv.W / 2 + 140, ys[i - 1] + size / 2 + 10, cv.W / 2 + 140, ys[i] - size / 2 - 10, bend=-60)
        return ys
    xs = [x0 + (x1 - x0) * i / max(1, n - 1) for i in range(n)] if n > 1 else [(x0 + x1) / 2]
    for i, (nm, lab, sub, t) in enumerate(items):
        icon(s, nm, t, xs[i], y, size, tone, lab, sub)
        if flow and i:
            arrow(s, t - 0.12, xs[i - 1] + size / 2 + 22, y, xs[i] - size / 2 - 22, y, bend=26)
    return xs


def loop(s, items, cx=None, cy=None, r=None, tone='ink', size=180):
    """A cycle: icons on a circle, an accent arc drawing from each to the next on its word (notes -> rules -> a better video -> …)."""
    cx = cv.W / 2 if cx is None else cx
    cy = cv.H * 0.46 if cy is None else cy
    r = min(cv.W, cv.H) * 0.26 if r is None else r
    n = len(items)
    pos = [(cx + r * math.cos(-math.pi / 2 + 2 * math.pi * i / n), cy + r * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n)]
    for i, (nm, lab, t) in enumerate(items):
        x, y = pos[i]
        icon(s, nm, t, x, y, size, tone)
        lid = s.c.uid('ll')
        lx, ly = x + (size / 2 + 30) * (1 if x >= cx + 1 else (-1 if x < cx - 1 else 0)), y + (size / 2 + 40 if abs(x - cx) < 2 else -20)
        anchor = 'translate(0,0)' if x > cx + 1 else ('translate(-100%,0)' if x < cx - 1 else 'translate(-50%,0)')
        s.add(f'<div id="{lid}" class="cvx-iclab {"ink" if tone == "ink" else "light"}" style="left:{lx + OX:.0f}px;top:{ly + OY:.0f}px;transform:{anchor};z-index:4">{esc(lab)}</div>')
        _pop(s.c, f'#{lid}', t + 0.15, 1.0, 10, 5)
        if i:
            a0 = -math.pi / 2 + 2 * math.pi * (i - 1) / n + 0.42
            a1 = -math.pi / 2 + 2 * math.pi * i / n - 0.42
            _arc(s, t - 0.15, cx, cy, r, a0, a1)
    if n > 2:
        a0 = -math.pi / 2 + 2 * math.pi * (n - 1) / n + 0.42
        a1 = -math.pi / 2 + 2 * math.pi - 0.42
        _arc(s, items[-1][2] + 0.6, cx, cy, r, a0, a1)


def _arc(s, t, cx, cy, r, a0, a1):
    c = s.c
    aid = c.uid('arc')
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    large = 1 if (a1 - a0) % (2 * math.pi) > math.pi else 0
    ang = a1 + math.pi / 2
    hx1, hy1 = x1 - 24 * math.cos(ang - 0.5), y1 - 24 * math.sin(ang - 0.5)
    hx2, hy2 = x1 - 24 * math.cos(ang + 0.5), y1 - 24 * math.sin(ang + 0.5)
    s.add(f'<svg id="{aid}" class="cv-abs" style="left:0;top:0;z-index:3" width="{cv.WW}" height="{cv.WH}" viewBox="{-OX} {-OY} {cv.WW} {cv.WH}">'
          f'<path d="M {x0:.1f},{y0:.1f} A {r},{r} 0 {large} 1 {x1:.1f},{y1:.1f}" fill="none" stroke="var(--cv-accent)" stroke-width="7" stroke-linecap="round"/>'
          f'<path d="M {hx1:.1f},{hy1:.1f} L {x1:.1f},{y1:.1f} L {hx2:.1f},{hy2:.1f}" fill="none" stroke="var(--cv-accent)" stroke-width="7" stroke-linecap="round"/></svg>')
    _draw_svg(c, f'#{aid}', t, 12)


def versus(s, left, right, t_win=None, win='right', y=520, w=700, h=470, tone='ink', gap=120):
    """MG V2's versus card: two cards swing in from depth (rotationY), a tag pill on each, the lines land on their words;
    on the verdict the winner lifts with an accent underline and the other steps back.
    left/right = {'tag', 'icon', 'lines': [(text, t, 'b'|'i'|'mute')], 't'}."""
    c = s.c
    if PORTRAIT:     # 9:16: one card above the other
        w, h = min(w, cv.W - 160), min(h, 520)
        ys = (cv.H * 0.30, cv.H * 0.30 + h + gap + 40)
        xs = (cv.W / 2, cv.W / 2)
    else:
        xs = (cv.W / 2 - gap / 2 - w / 2, cv.W / 2 + gap / 2 + w / 2)
        ys = (y, y)
    ids = []
    for k, (side, x, ry) in enumerate(((left, xs[0], 22), (right, xs[1], -22))):
        y = ys[k]
        pid, cid, tid = c.uid('vp'), c.uid('vc'), c.uid('vt')
        lines = ''
        for j, (txt, tt, st) in enumerate(side['lines']):
            lid = f'{cid}l{j}'
            cls = 'ln' + (' i' if st == 'i' else '') + (' mute' if st == 'mute' else '')
            lines += f'<span id="{lid}" class="{cls}">{esc(txt)}</span>'
            _pop(c, f'#{lid}', tt, 1.06, 12)
        ic = f'<div style="color:{"var(--cv-accent)" if (k == 1) == (win == "right") else "currentColor"}">{icon_svg(side["icon"], 96, 2.0)}</div>' if side.get('icon') else ''
        s.add(f'<div id="{pid}" class="cvx-persp" style="left:{x - w / 2 + OX:.0f}px;top:{y - h / 2 + OY:.0f}px;width:{w}px;height:{h}px;z-index:4">'
              f'<div id="{cid}" class="cvx-vs {tone}" style="width:{w}px;height:{h}px">{ic}{lines}</div></div>')
        s.add(f'<div id="{tid}" class="cvx-vstag {"ink" if tone == "ink" else "light"}" style="left:{x + OX:.0f}px;top:{y - h / 2 + OY:.0f}px;z-index:6"><i></i>{esc(side["tag"])}</div>')
        t0 = side['t']
        c.pre.append(f'gsap.set("#{cid}",{{opacity:0,rotationY:{ry * 2},z:-260,y:30}});')
        c.at(f'tl.fromTo("#{cid}",{{opacity:0,rotationY:{ry * 2},z:-260,y:30}},{{opacity:1,rotationY:{ry * 0.3:.1f},z:0,y:0,duration:{F(18):.4f},'
             f'ease:"power3.out",immediateRender:false}},{fr(t0):.4f});')
        _pop(c, f'#{tid}', t0 + 0.2, 1.1, 8, 8)
        if side.get('icon'):
            _draw_svg(c, f'#{cid} div', t0 + 0.2)
        ids.append((pid, cid, tid, x))
    if t_win is not None:
        wi = 1 if win == 'right' else 0
        pid, cid, tid, x = ids[wi]
        y = ys[wi]
        uid = c.uid('ul')
        s.add(f'<div id="{uid}" class="cvx-uline" style="left:{x - w / 2 + 60 + OX:.0f}px;top:{y + h / 2 + 26 + OY:.0f}px;width:{w - 120}px;z-index:6"></div>')
        _wipe(c, f'#{uid}', t_win, 10)
        c.at(f'tl.fromTo("#{pid}",{{scale:1}},{{scale:1.05,duration:{F(14):.4f},ease:"back.out(2)",immediateRender:false}},{fr(t_win):.4f});')
        lp, lc, lt, _ = ids[1 - wi]
        c.at(f'tl.fromTo(["#{lp}","#{lt}"],{{opacity:1}},{{opacity:0.42,duration:{F(12):.4f},immediateRender:false}},{fr(t_win):.4f});')
        sfx(c, t_win, 'pop', 0.9)


def tiles(s, items, cols=None, x=None, y=None, tw=None, th=None, gx=40, gy=40, tone='ink', title=None):
    """MG V2's grid card: tiles (icon + the spoken words) spring in on their words. items = [(icon, label, sub, t)]."""
    cols = cols or (2 if PORTRAIT else 3)
    x = cv.W / 2 if x is None else x
    y = cv.H / 2 if y is None else y
    tw = tw or 440
    th = th or 300
    c = s.c
    n = len(items)
    rows = math.ceil(n / cols)
    W_ = cols * tw + (cols - 1) * gx
    H_ = rows * th + (rows - 1) * gy
    for i, (nm, lab, sub, t) in enumerate(items):
        r_, k = divmod(i, cols)
        inrow = min(cols, n - r_ * cols)
        rw = inrow * tw + (inrow - 1) * gx
        tx = x - rw / 2 + k * (tw + gx)
        ty = y - H_ / 2 + r_ * (th + gy)
        tid = c.uid('t2')
        sub_h = f'<small>{esc(sub)}</small>' if sub else ''
        s.add(f'<div id="{tid}" class="cvx-tile2 {tone}" style="left:{tx + OX:.0f}px;top:{ty + OY:.0f}px;width:{tw}px;height:{th}px;z-index:4">'
              f'<div style="color:var(--cv-accent)">{icon_svg(nm, 96, 2.0)}</div><div class="tl">{esc(lab)}{sub_h}</div></div>')
        _spring_in(c, f'#{tid}', t, 0.7, 14)
        _draw_svg(c, f'#{tid}', t + 0.15)


def head(s, t, small, key, x=None, y=None, tone='ink'):
    """A heading over a graphic: small Inter line + the key word in Playfair italic (accent on paper)."""
    x = cv.W / 2 if x is None else x
    y = cv.H * 0.14 if y is None else y
    c = s.c
    hid = c.uid('hd')
    s.add(f'<div id="{hid}" class="cvx-head {tone}" style="left:{x + OX}px;top:{y + OY}px;z-index:5">'
          f'{f"<span class=s>{esc(small)}</span>" if small else ""}<span class="k">{esc(key)}</span></div>')
    _pop(c, f'#{hid}', t, 1.08, 14)
    return hid


def bars(s, items, x0=None, x1=None, base=None, hmax=None, bw=None, tone='light', maxv=None, unit=''):
    """MG V1's chart hit: bars grow from the baseline on their words, the value ticks up over them.
    items = [(label, value, t, accent?)]."""
    x0 = cv.W * 0.22 if x0 is None else x0
    x1 = cv.W * 0.78 if x1 is None else x1
    base = cv.H * 0.76 if base is None else base
    hmax = cv.H * (0.36 if PORTRAIT else 0.48) if hmax is None else hmax
    bw = bw or (150 if PORTRAIT else 180)
    c = s.c
    maxv = maxv or max(v for _, v, _, _ in items)
    n = len(items)
    xs = [x0 + (x1 - x0) * i / max(1, n - 1) for i in range(n)]
    aid = c.uid('ax')
    s.add(f'<div id="{aid}" class="cvx-axisl {tone}" style="left:{x0 - bw + OX}px;top:{base + OY}px;width:{x1 - x0 + 2 * bw}px;z-index:3"></div>')
    _wipe(c, f'#{aid}', items[0][2] - 0.3, 12)
    for (lab, v, t, acc), x in zip(items, xs):
        h = hmax * v / maxv
        bid, lid = c.uid('b2'), c.uid('bl')
        s.add(f'<div id="{bid}" class="cvx-bar2 {"a" if acc else ("n" if tone == "light" else "ink-n")}" style="left:{x - bw / 2 + OX:.0f}px;top:{base - h + OY:.0f}px;width:{bw}px;height:{h:.0f}px;z-index:3"></div>')
        s.add(f'<div id="{lid}" class="cvx-blab {tone}" style="left:{x + OX:.0f}px;top:{base + 20 + OY}px;z-index:3">{esc(lab)}</div>')
        c.pre.append(f'gsap.set("#{bid}",{{scaleY:0}});')
        c.at(f'tl.fromTo("#{bid}",{{scaleY:0}},{{scaleY:1,duration:{F(14):.4f},ease:"power3.out",immediateRender:false}},{fr(t):.4f});')
        _pop(c, f'#{lid}', t, 1.0, 8, 4)
        vals = [round(v * k / 6) for k in range(1, 7)] if isinstance(v, int) and v > 6 else [v]
        tt = [t + 0.07 * k for k in range(len(vals))]
        for j, (vv, ts) in enumerate(zip(vals, tt)):
            vid = c.uid('bv')
            s.add(f'<div id="{vid}" class="cvx-bval {"a" if acc else tone}" style="left:{x + OX:.0f}px;top:{base - h - 14 + OY:.0f}px;z-index:4">{esc(str(vv) + unit)}</div>')
            _show(c, f'#{vid}', ts, tt[j + 1] if j + 1 < len(tt) else None)


def donut(s, t, pct, x=None, y=None, r=None, tone='light', label=None, value=None, dur=0.9):
    """A ring that fills to `pct` in the accent while the number ticks up in the middle."""
    x = cv.W / 2 if x is None else x
    y = cv.H * 0.44 if y is None else y
    r = min(cv.W, cv.H) * 0.21 if r is None else r
    c = s.c
    did = c.uid('dn')
    L = 2 * math.pi * r
    base = 'var(--cv-axis)' if tone == 'light' else 'var(--cv-photo-shadow)'
    s.add(f'<svg id="{did}" class="cv-abs" style="left:{x - r - 40 + OX:.0f}px;top:{y - r - 40 + OY:.0f}px;z-index:3;overflow:visible" width="{2 * r + 80}" height="{2 * r + 80}">'
          f'<circle cx="{r + 40}" cy="{r + 40}" r="{r}" fill="none" stroke="{base}" stroke-width="42"/>'
          f'<circle id="{did}p" cx="{r + 40}" cy="{r + 40}" r="{r}" fill="none" stroke="var(--cv-accent)" stroke-width="42" stroke-linecap="round" '
          f'transform="rotate(-90 {r + 40} {r + 40})" stroke-dasharray="{L:.1f} {L + 2:.1f}" stroke-dashoffset="{L:.1f}" style="filter:drop-shadow(0 0 14px var(--cv-glow-soft))"/></svg>')
    _pop(c, f'#{did}', t - 0.2, 0.9, 8, 8)
    c.at(f'tl.fromTo("#{did}p",{{strokeDashoffset:{L:.1f}}},{{strokeDashoffset:{L * (1 - pct):.1f},duration:{dur:.4f},ease:"power2.out",immediateRender:false}},{fr(t):.4f});')
    steps = 8
    vals = [f'{round(pct * 100 * k / steps)}%' for k in range(1, steps + 1)] if value is None else [value]
    tt = ticks(t, t + dur * 0.9, len(vals))
    counter(s, tt, vals, x, y, size=140, tone=tone, label=label, label_dy=110)


def linechart(s, pts, t0, t1, x0=None, y0=None, x1=None, y1=None, tone='light', xl=None, yl=None, dots=()):
    """A smooth rising line with a soft area under it, drawing from t0 to t1; dots = [(t, index, label)] pop on the curve."""
    x0 = cv.W * 0.16 if x0 is None else x0
    x1 = cv.W * 0.85 if x1 is None else x1
    y0 = cv.H * (0.62 if PORTRAIT else 0.76) if y0 is None else y0
    y1 = cv.H * (0.3 if PORTRAIT else 0.2) if y1 is None else y1
    c = s.c
    lid = c.uid('lc')
    P = [(x0 + (x1 - x0) * u, y0 - (y0 - y1) * v) for u, v in pts]
    d = f'M {P[0][0]:.0f},{P[0][1]:.0f}'
    for (ax, ay), (bx, by) in zip(P, P[1:]):
        mx = (ax + bx) / 2
        d += f' C {mx:.0f},{ay:.0f} {mx:.0f},{by:.0f} {bx:.0f},{by:.0f}'
    area = d + f' L {P[-1][0]:.0f},{y0} L {P[0][0]:.0f},{y0} Z'
    ax = 'var(--cv-axis)' if tone == 'light' else 'var(--cv-ink)'
    s.add(f'<svg class="cv-abs" style="left:0;top:0;z-index:3" width="{cv.WW}" height="{cv.WH}" viewBox="{-OX} {-OY} {cv.WW} {cv.WH}">'
          f'<line x1="{x0}" y1="{y0}" x2="{x1 + 40}" y2="{y0}" stroke="{ax}" stroke-width="3" opacity=".6"/>'
          f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1 - 40}" stroke="{ax}" stroke-width="3" opacity=".6"/>'
          f'<path id="{lid}a" d="{area}" fill="var(--cv-glow-soft)" stroke="none"/>'
          f'<path id="{lid}" d="{d}" fill="none" stroke="var(--cv-accent)" stroke-width="9" stroke-linecap="round" style="filter:drop-shadow(0 0 10px var(--cv-glow))"/>'
          + (f'<text x="{(x0 + x1) / 2}" y="{y0 + 54}" text-anchor="middle" class="cvx-axt" fill="{ax}" style="font-family:var(--cv-sans);font-weight:600;font-size:22px;letter-spacing:.2em">{esc(xl)}</text>' if xl else '')
          + (f'<text x="{x0 - 30}" y="{(y0 + y1) / 2}" text-anchor="middle" transform="rotate(-90 {x0 - 30} {(y0 + y1) / 2})" fill="{ax}" style="font-family:var(--cv-sans);font-weight:600;font-size:22px;letter-spacing:.2em">{esc(yl)}</text>' if yl else '')
          + '</svg>')
    c.pre.append(f'(()=>{{const p=document.getElementById("{lid}");const L=p.getTotalLength();p.dataset.len=L;gsap.set(p,{{strokeDasharray:L+" "+(L+4),strokeDashoffset:L}});gsap.set("#{lid}a",{{opacity:0}});}})();')
    c.at(f'(()=>{{const p=document.getElementById("{lid}");tl.fromTo(p,{{strokeDashoffset:+p.dataset.len}},{{strokeDashoffset:0,duration:{t1 - t0:.4f},ease:"power1.inOut",immediateRender:false}},{fr(t0):.4f});}})();')
    c.at(f'tl.fromTo("#{lid}a",{{opacity:0}},{{opacity:1,duration:{(t1 - t0):.4f},ease:"power1.in",immediateRender:false}},{fr(t0):.4f});')
    for t, i, lab in dots:
        px, py = P[i]
        did = c.uid('ld')
        s.add(f'<div id="{did}" class="cv-ball" style="left:{OX}px;top:{OY}px;z-index:5"></div>')
        c.pre.append(f'gsap.set("#{did}",{{x:{px:.0f},y:{py:.0f},xPercent:-50,yPercent:-50,opacity:0,scale:.4}});')
        c.at(f'tl.fromTo("#{did}",{{opacity:0,scale:.4}},{{opacity:1,scale:1,duration:{F(6):.4f},ease:"back.out(2)",immediateRender:false}},{fr(t):.4f});')
        if lab:
            tid = c.uid('lt')
            s.add(f'<div id="{tid}" class="cvx-blab {tone}" style="left:{px + OX:.0f}px;top:{py - 80 + OY:.0f}px;z-index:5;font-size:34px;font-weight:700">{esc(lab)}</div>')
            _pop(c, f'#{tid}', t + 0.05, 1.0, 8, 5)


def checklist(s, items, x=None, y0=None, dy=None, tone='ink', done_before=None):
    """Install steps: a box per row, the row's words land, the box fills in the accent and a check draws on its word.
    items = [(text, t_show, t_check)]; done_before = rows shown already checked at the scene start."""
    x = cv.W * (0.07 if PORTRAIT else 0.25) if x is None else x
    y0 = cv.H * (0.3 if PORTRAIT else 0.28) if y0 is None else y0
    dy = dy or (130 if PORTRAIT else 120)
    c = s.c
    for i, (txt, ts, tc) in enumerate(items):
        rid, fid, kid = c.uid('ck'), c.uid('cf'), c.uid('ckk')
        s.add(f'<div id="{rid}" class="cvx-check {tone}" style="left:{x + OX}px;top:{y0 + i * dy + OY}px;z-index:4"><span class="n">{i + 1:02d}</span>'
              f'<span class="bx"><span id="{fid}" class="fill"></span><svg id="{kid}" style="position:absolute;left:6px;top:6px" width="44" height="44" viewBox="0 0 24 24" fill="none" '
              f'stroke="var(--cv-white)" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><span>{esc(txt)}</span></div>')
        _pop(c, f'#{rid}', ts, 1.0, 10, 6)
        c.pre.append(f'gsap.set("#{fid}",{{scale:0,opacity:0}});')
        c.at(f'tl.fromTo("#{fid}",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:{F(8):.4f},ease:"back.out(2.4)",immediateRender:false}},{fr(tc):.4f});')
        _draw_svg(c, f'#{kid}', tc + 0.08, 9)

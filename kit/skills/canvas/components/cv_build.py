"""cv_build.py — the Canvas build engine: words -> beats -> one HyperFrames composition per chapter.

A video's build.py only holds its config and its BEATS table; everything below is shared:

    import sys, json; K = json.load(open('kit.json')); sys.path.insert(0, K['skill'] + '/components')
    import cv_devices as cv; cv.set_format(K.get('format', '16x9'))     # BEFORE importing anything else from the kit
    from cv_build import *
    CHAPTERS = [('ch-01-intro', None), ('ch-02-how', 'so how does it')]  # chapter folder, the phrase that opens it
    BEATS = {0: [('this editing style', face), ('the paintings', paint('p_money.jpg'))], 1: [...]}
    main(CHAPTERS, BEATS)

Each beat = (the words that start it, a builder). A beat runs from that phrase's onset (2 frames early) to the next beat's
start. Builders get (comp, t0, t1) in chapter-local seconds. `face` is his camera with the captions on his chest; every
other builder is a scene (paper / dark / blue ground) holding one device from cv_devices / cvx.

Times come from work/words.json (the CUT voice). Captions are written by say(): groups of <= 5 words, the key word big
(a number, then a word from EMPH, then the longest content word), each group hard-replacing the last.
"""
import json, math, os, re, subprocess, sys
import cv_devices as cv
from cv_devices import Comp, Scene, cap, aroll, painting, photo, figure, line, graph, highlight, callout, quote_marks, sfx, F, fr
import cvx
from cvx import (Shot, roadmap, set_stops, counter, ticks, sharebar, typer, tile, chip, filecard, strike, band, blurstrip, waveform,
                 vidcard, receipt, icon, arrow, icons_flow, loop, versus, tiles, head, bars, donut, linechart, checklist, clamp)

FPS = 30
PORTRAIT = cv.H > cv.W
CAP_Y = 1330 if PORTRAIT else 820          # captions on the chest (measured off the reference, both shapes)
LEAD = 2 / 30                               # a picture lands 2 frames before the word that names it

GW, WORDS, SEG0, CAM = [], [], 0.0, 'assets/cam.mp4'
FIXSEQ, CAPS, LOG = [], {}, []


def norm(w):
    return w.strip('.,:?!"').lower()


# ------------------------------------------------------------------------------------------------ words + caption fixes
def load_words(path='work/words.json', fixseq=(), caps=None):
    """fixseq = [(['heard', 'tokens'], ['shown', 'tokens'])]: SAME length, so every shown word keeps its own onset ('' hides
    a word). caps = {'canvas': 'Canvas'}: spelling for single words."""
    global GW
    ws = json.load(open(path))
    out = [dict(w, d=w['w']) for w in ws]
    low = [w['w'].lower() for w in out]
    for src, dst in fixseq:
        n = len(src)
        for i in range(len(out) - n + 1):
            if low[i:i + n] == src:
                for k in range(n):
                    out[i + k]['d'] = dst[k]
                    low[i + k] = '\0'
    for w in out:
        if caps and w['d'] == w['w'] and w['w'].lower() in caps:
            w['d'] = caps[w['w'].lower()]
    GW = out
    return out


def TS_global(phrase, after=0.0):
    toks = [norm(t) for t in phrase.split()]
    n = len(toks)
    for i in range(len(GW) - n + 1):
        if GW[i]['s'] >= after - 1e-6 and [norm(GW[i + k]['w']) for k in range(n)] == toks:
            return GW[i]['s'], i
    raise KeyError(f'phrase not found: "{phrase}" after {after:.2f}s')


def TS(phrase, after=0.0):
    """Chapter-local onset of the first word of `phrase` (matched on the HEARD words, punctuation ignored) at or after `after`."""
    toks = [norm(t) for t in phrase.split()]
    n = len(toks)
    for i in range(len(WORDS) - n + 1):
        if WORDS[i]['s'] >= after - 1e-6 and [norm(WORDS[i + k]['w']) for k in range(n)] == toks:
            return WORDS[i]['s']
    raise KeyError(f'phrase not found in this chapter: "{phrase}" after {after:.2f}s')


def at(phrase, t0, d=0.0, fallback=0.4):
    """TS() that never fails: a device keyed to a word the speaker didn't say lands `fallback` s into the beat instead."""
    try:
        return TS(phrase, t0) + d
    except KeyError:
        return t0 + fallback


# ------------------------------------------------------------------------------------------------ the caption system
STOP = set("a an the and or but so to of in on at for with is it it's its i i'm i'll you you're your my me we our that that's this these those be "
           "was were are am do did does have has had will would can could just very really also then than there there's here here's what when "
           "how which who as by from up out into about not no if because all every gonna let let's go we'll they they're them".split())
EMPH = set()        # a video adds its own key words: EMPH.update({'canvas', 'free', ...})
NUM = re.compile(r'^[$]?\d')


def groups(ws):
    out, cur = [], []
    for w in ws:
        ends = w['w'][-1] in '.?!'          # a group may take a 6th word when it ends the sentence ("have to say.")
        if cur and ((len(cur) >= 5 and not (ends and len(cur) == 5)) or w['s'] - cur[-1]['e'] > 0.38):
            out.append(cur); cur = []
        cur.append(w)
        if w['w'][-1] in '.?!,' and len(cur) >= 2:
            out.append(cur); cur = []
    if cur:
        if len(cur) == 1 and out and len(out[-1]) < 5 and cur[0]['s'] - out[-1][-1]['e'] < 0.3:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def key_of(g):
    best, score = len(g) - 1, -1
    for i, w in enumerate(g):
        n = norm(w['w'])
        if not w['d']:
            continue
        sc = 100 if NUM.match(w['d']) else (50 + len(n) if n in EMPH else (10 + len(n) if n not in STOP else 0))
        if sc >= score:
            best, score = i, sc
    return best


def rows_of(g, tone):
    k = key_of(g)
    kw = g[k]
    d = kw['d']
    end = kw['w'][-1] in '.?!'
    st = 'n' if NUM.match(d) else ('i' if (end and k == len(g) - 1) else 'b')
    if tone == 'ink' and st == 'i':
        st = 'i/blue'
    before = [(w['d'], w['s'], 's') for w in g[:k] if w['d']]
    after = [(w['d'], w['s'], 's') for w in g[k + 1:] if w['d']]
    rows = []
    if before:
        rows.append(('l', before))
    rows.append(('c', [(d, kw['s'], st)]))
    if after:
        rows.append(('r', after))
    return rows


def say(c, scene, t0, t1, x=None, y=None, tone='light', maxw=None, scrim=False):
    """Caption every word with onset in [t0, t1): <= 5 words a group, one big key word, the small words in the gaps, each word
    blurring in on its onset; the next group hard-replaces the last. scene=None puts them over everything (face beats, pushes)."""
    x = cv.W / 2 if x is None else x
    y = CAP_Y if y is None else y
    ws = [w for w in WORDS if t0 - 0.03 <= w['s'] < t1 - 0.03]
    gs = [g for g in groups(ws) if any(w['d'] for w in g)]
    for i, g in enumerate(gs):
        nxt = gs[i + 1][0]['s'] if i + 1 < len(gs) else None
        rows = rows_of(g, tone)
        if scene is None:
            cap(c, None, nxt if nxt else t1, rows, x=x, y=y, tone=tone, maxw=maxw)
        else:
            hide = nxt if nxt is not None else (t1 if t1 < scene.t1 - 0.05 else None)   # a partial say() must not linger
            cap(c, scene, t1, rows, x=x, y=y, tone=tone, hide_at=hide, maxw=maxw, scrim=scrim)


# ------------------------------------------------------------------------------------------------ beat builders
def face(c, t0, t1):
    """His camera, raw, full frame, never zoomed; the captions on his chest. The cut back to the face is silent."""
    aroll(c, t0, t1, CAM, sound=None)
    say(c, None, t0, t1)


def paint(img, side='right', enter='slide', x=None, y=None, maxw=None, scrim=False):
    """A public-domain painting (cv_treat.py painting) sliding in; the words sit in its dark side.
    16:9: side right|left|full. 9:16: always treat with --side full --portrait and pass scrim=True."""
    def f(c, t0, t1):
        P = painting(c, t0, t1, f'assets/img/{img}', enter=enter)
        if PORTRAIT:
            xx, yy = (cv.W / 2 if x is None else x), (CAP_Y if y is None else y)
            sc = True
        else:
            xx = x if x is not None else (520 if side == 'right' else (1400 if side == 'left' else 960))
            yy, sc = (540 if y is None else y), (scrim or side == 'full')
        say(c, P, t0, t1, xx, yy, 'light', maxw=maxw or (cv.W * 0.8 if PORTRAIT else 740), scrim=sc)
        P.close()
    return f


def quote(c, t0, t1):
    """The punchline as a quote on the blue ground, with quotation marks."""
    Q = Scene(c, t0, t1, ground='blue_vig')
    Q.drift(s=1.035)
    sfx(c, t0, 'tick')
    ws = [w for w in WORDS if t0 - 0.03 <= w['s'] < t1 - 0.03 and w['d']]
    gs = groups(ws)
    for i, g in enumerate(gs):
        nxt = gs[i + 1][0]['s'] if i + 1 < len(gs) else None
        rows = rows_of(g, 'light')
        if i == 0:
            a, w0 = rows[0]
            rows[0] = (a, [('“', w0[0][1], 'q')] + w0)
        if i == len(gs) - 1:
            a, wl = rows[-1]
            rows[-1] = (a, wl + [('”', wl[-1][1] + 0.12, 'q')])
        cap(c, Q, t1, rows, x=cv.W / 2, y=cv.H / 2, tone='light', hide_at=nxt)
    Q.close()


def cutout(fig='figure.png', halo='figure_halo.png', nat=(945, 1311), fig_w=None, side_words=True):
    """The rough ultramarine cut-out of a PAINTED figure (scripts/figure.py), with its halo, words either side.
    Never a frame of the speaker's own take: a still of a talking face catches a blink or an open mouth."""
    def f(c, t0, t1):
        G = Scene(c, t0, t1, ground='paper')
        G.drift(s=1.012)
        fw = fig_w or (640 if PORTRAIT else 760)
        figure(G, f'assets/img/{fig}', f'assets/img/{halo}', t0, cx=cv.W / 2, fig_w=fw, nat=nat, halo_w=int(fw * 1.5))
        sfx(c, t0, 'pop')
        if PORTRAIT:
            say(c, G, t0, t1, cv.W / 2, cv.H * 0.2, 'ink', maxw=cv.W * 0.8)
        else:
            say(c, G, t0, t1, 400, 460, 'ink', maxw=560)
        G.close()
    return f


def MG(fn, ground='paper', cap=None, maxw=None, drift=1.03, captions=True):
    """A scene holding one explainer device. fn(scene, t0, t1, tone) draws it; the house captions sit under it."""
    def f(c, t0, t1):
        s = Scene(c, t0, t1, ground=ground)
        s.drift(s=drift)
        sfx(c, t0, 'tick')
        tone = 'ink' if ground == 'paper' else 'light'
        fn(s, t0, t1, tone)
        if captions:
            cx, cy = cap if cap else (cv.W / 2, cv.H * (0.8 if PORTRAIT else 0.86))
            say(c, s, t0, t1, cx, cy, tone, maxw=maxw or cv.W * 0.86)
        s.close()
    return f


def photos(items, ground='paper', cap=None, maxw=None, border=12):
    """Real photos / thumbnails dropping onto paper: items = [(img, phrase_or_seconds_after_start, x, y, w, rot)]."""
    def f(c, t0, t1):
        s = Scene(c, t0, t1, ground=ground)
        s.drift(x=0, y=-10, s=1.06)
        sfx(c, t0, 'tick')
        for img, when, x, y, w, rot in items:
            t = t0 + when if isinstance(when, (int, float)) else at(when, t0)
            photo(s, f'assets/img/{img}', max(t0, t - 0.03), x=x, y=y, w=w, rot=rot, sound=False, border=border)
        cx, cy = cap if cap else (cv.W / 2, cv.H * 0.85)
        say(c, s, t0, t1, cx, cy, 'ink' if ground == 'paper' else 'light', maxw=maxw)
        s.close()
    return f


def screen(key, ground='paper', x=None, y=None, w=None, rings=(), push=None, scroll=(), cap=None, h=None):
    """A real screen capture (assets/img/<key>.jpg + its boxes in assets/img/shots.json) in a window; rings=[(phrase, box)] draw
    on the word; push=(phrase, box, scale) moves the camera onto the box (the captions then ride above the scene)."""
    def f(c, t0, t1):
        s = Scene(c, t0, t1, ground=ground)
        s.drift(s=1.03)
        tone = 'ink' if ground == 'paper' else 'light'
        xx = cv.W / 2 if x is None else x
        yy = (cv.H * 0.4 if PORTRAIT else 400) if y is None else y
        ww = w or (cv.W - 120 if PORTRAIT else 1120)
        sh = Shot(s, key, t0, xx, yy, ww, h=h, rot=-1.0 if ground == 'paper' else 0.0, enter='drop' if ground == 'paper' else 'pop')
        for ph, dur, sy in scroll:
            sh.scroll(at(ph, t0, -0.05), dur, sy)
        for ph, box in rings:
            sh.ring(at(ph, t0), box)
        sh.close()
        if push:
            ph, box, scl = push
            px, py = sh.at(box)
            X, Y, S = clamp(*s.look(px, py + 170, scl))
            s.move(at(ph, t0, -0.1), 0.6, x=X, y=Y, s=S, ease='power3.inOut', smear=24)
        cx, cy = cap if cap else (cv.W / 2, cv.H * (0.82 if PORTRAIT else 0.85))
        say(c, None if push else s, t0, t1, cx, cy, tone)
        s.close()
    return f


def mark(img='logo.png', w=None):
    """A brand mark (white on black, screened onto the dark ground) blur-popping in, the words under it."""
    def f(c, t0, t1):
        K = Scene(c, t0, t1, ground='dark')
        K.drift(s=1.03)
        lid = c.uid('logo')
        ww = w or (480 if PORTRAIT else 520)
        K.add(f'<img id="{lid}" class="cv-abs" style="mix-blend-mode:screen;left:{cv.W / 2 - ww / 2 + cv.OX:.0f}px;top:{cv.H * 0.38 - ww / 2 + cv.OY:.0f}px;'
              f'width:{ww}px" src="assets/img/{img}" alt="">')
        cvx._pop(c, f'#{lid}', t0 + 0.05, 1.08, 22)
        sfx(c, t0, 'sub')
        say(c, K, t0, t1, cv.W / 2, cv.H * 0.74, 'light')
        K.close()
    return f


def blue_line(c, t0, t1):
    """The thick blue line the words interrupt (paper)."""
    L = Scene(c, t0, t1, ground='paper')
    sfx(c, t0, 'tick')
    L.drift(x=-40, y=-20, s=1.04)
    if PORTRAIT:
        line(L, 'M 300,-80 C 300,300 540,500 540,700', t0, t0 + 0.45)
        line(L, 'M 540,1180 C 540,1400 760,1600 780,2000', t0 + 0.5, t1)
        say(c, L, t0, t1, cv.W / 2, cv.H / 2, 'ink', maxw=cv.W * 0.8)
    else:
        line(L, 'M -80,300 C 240,300 420,540 640,540', t0, t0 + 0.45)
        line(L, 'M 1290,540 C 1520,540 1640,700 1780,860 S 2000,1150 2140,1180', t0 + 0.5, t1)
        say(c, L, t0, t1, 965, 540, 'ink', maxw=600)
    L.close()


def RM(active, phrase, captions=True):
    """The roadmap returning at a chapter: drawn, the camera pushes to this chapter's stop and lights it on `phrase`."""
    def f(c, t0, t1):
        roadmap(c, t0, t1, active=active, push=at(phrase, t0, fallback=0.5))
        if captions:
            say(c, None, t0, t1, cv.W / 2, cv.H * 0.16, 'ink')
    return f


def RM_first(c, t0, t1, light_on=()):
    """The roadmap's first appearance: the five stops pop in, then light one by one on the words that name them."""
    roadmap(c, t0, t1, draw=[t0 + 0.25 + 0.18 * i for i in range(5)], lights=[(i, at(p, t0)) for i, p in light_on])
    say(c, None, t0, t1, cv.W / 2, cv.H * 0.16, 'ink')


# ------------------------------------------------------------------------------------------------ chapters + the build
def boundary(phrase, after):
    t, i = TS_global(phrase, after)
    prev_e = GW[i - 1]['e'] if i else 0.0
    return round((prev_e + t) / 2 * FPS)


def chapters(CH, total_frames):
    fr_ = [0]
    after = 0.0
    for _, ph in CH[1:]:
        f = boundary(ph, after)
        fr_.append(f)
        after = f / FPS + 0.5
    fr_.append(total_frames)
    return [(CH[i][0], fr_[i], fr_[i + 1]) for i in range(len(CH))]


def build(k, SEGS, BEATS, title='Canvas'):
    global WORDS, SEG0
    name, f0, f1 = SEGS[k]
    SEG0 = f0 / FPS
    WORDS = [dict(w, s=round(w['s'] - SEG0, 3), e=round(w['e'] - SEG0, 3)) for w in GW if f0 / FPS - 0.02 <= w['s'] < f1 / FPS - 0.02]
    dur = (f1 - f0) / FPS
    c = Comp(dur)
    c.css.append(cvx.CSS)
    c.css.append(cvx.CSS2)
    beats = BEATS[k]
    starts, after = [], 0.0
    for ph, fn in beats:
        t = TS(ph, after)
        starts.append(max(0.0, fr(t - LEAD)) if starts else 0.0)
        after = t + 0.01
    for i, (ph, fn) in enumerate(beats):
        t0 = starts[i]
        t1 = starts[i + 1] if i + 1 < len(starts) else dur
        fn(c, t0, t1)
        LOG.append((name, round(SEG0 + t0, 2), round(t1 - t0, 2), ph, fn is face))
    os.makedirs(f'{name}/assets', exist_ok=True)
    for d in ('cv', 'img', 'clip', 'icons'):
        lk = f'{name}/assets/{d}'
        if not os.path.lexists(lk) and os.path.exists(f'assets/{d}'):
            os.symlink(f'../../assets/{d}', lk)
    cam = f'{name}/assets/cam.mp4'      # this chapter's piece of the cut camera (render.sh re-cuts it; snapshots need it too)
    if not os.path.exists(cam) or os.path.getmtime(cam) < os.path.getmtime('assets/cam.mp4'):
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{f0 / FPS:.4f}', '-i', 'assets/cam.mp4', '-frames:v', str(f1 - f0), '-an',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-g', '30', '-pix_fmt', 'yuv420p', cam], check=True)
    c.write(f'{name}/index.html', title=f'{title} · {name}')
    # the renderer CEILs duration*fps: write the root duration FLOORED to 4 decimals or a chapter renders one frame long
    h = open(f'{name}/index.html').read()
    h = h.replace(f'data-duration="{c.dur:.4f}"', f'data-duration="{math.floor((f1 - f0) / FPS * 1e4) / 1e4:.4f}"', 1)
    open(f'{name}/index.html', 'w').write(h)
    c.write_cues(f'{name}/sfx-cues.txt')
    print(f'{name}: {dur:.2f}s, {len(beats)} beats')


def main(CH, BEATS, title='Canvas', words='work/words.json', fixseq=(), caps=None):
    """Build every chapter (or the ones given as argv indices). Writes work/chapters.json and work/beats.txt (+ the holds)."""
    load_words(words, fixseq, caps)
    total = int(open('work/cut/frames.txt').read().split()[0])
    SEGS = chapters(CH, total)
    os.makedirs('work', exist_ok=True)
    json.dump([{'name': n, 'f0': a, 'f1': b} for n, a, b in SEGS], open('work/chapters.json', 'w'), indent=1)
    only = [int(a) for a in sys.argv[1:] if a.isdigit()] or range(len(SEGS))
    for k in only:
        build(k, SEGS, BEATS, title)
    with open('work/beats.txt', 'w') as f:
        for r in LOG:
            f.write(f'{r[0]:22s} {r[1]:8.2f} {r[2]:5.2f}  {r[3]}\n')
    faces = sum(r[2] for r in LOG if r[4])
    total_s = sum(r[2] for r in LOG) or 1
    print(f'beats {len(LOG)}, holds over 4.5 s: {[(r[1], r[2], r[3]) for r in LOG if r[2] > 4.5]}')
    print(f'face share {faces / total_s:.0%} (aim 30-35%), a new picture every {total_s / max(1, len(LOG)):.1f} s (aim ~2.4)')


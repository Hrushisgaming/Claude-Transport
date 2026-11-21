"""build.py — THIS video's Canvas edit: its chapters and its beats. Everything else lives in the skill (components/cv_build.py).

Run from the video folder:   "$CV_PY" build.py          (all chapters)     "$CV_PY" build.py 2     (just chapter 3)
Then:                        bash <skill>/scripts/render.sh .     and     bash <skill>/scripts/finish.sh .

Every time comes from work/words.json (the CUT voice, written by cut.py). A beat starts on the words that name it:
the face ANNOUNCES an idea, the screen SHOWS it. Aim: face 30-35%, a new picture every ~2.4 s, no hold over ~4.5 s,
paintings only where the words are about art or need a strong metaphor (~5 in 10 minutes), explainer graphics everywhere else.
"""
import json, sys
K = json.load(open('kit.json'))
sys.path.insert(0, K['skill'] + '/components')
import cv_devices as cv
cv.set_format(K['format'])               # '16x9' long format | '9x16' short format; must run before the next import
from cv_build import *

# 1. Caption spelling. Same-length rewrites keep each word on its own onset ('' hides a heard word).
FIXSEQ = [
    # (['clot', 'code'], ['Claude', 'Code']),
]
CAPS = {
    # 'canvas': 'Canvas',
}
EMPH.update({
    # words that should win the big key-word slot in their caption group
})

# 2. Chapters: (folder name, the words that open it). The first has no phrase. Long format: 40-130 s each; short: one chapter.
CHAPTERS = [
    ('ch-01-intro', None),
    # ('ch-02-how-it-works', 'so how does it work'),
]

# Optional: this video's five roadmap stops (the blue line that returns at every chapter).
# set_stops([('The', 'problem', 'b'), ('How it', 'works', 'i'), ('The', 'demo', 'b'), ('What it', 'costs', 'i'), ('How to', 'start', 'b')])


# 3. Explainer devices for this video (each one draws on the words it names; `at(phrase, t0)` = that word's time).
def g_example(s, t0, t1, tone):
    icons_flow(s, [('video', 'your recording', None, t0 + 0.05), ('scissors', 'the cut', None, at('cut', t0)),
                   ('sparkles', 'the edit', None, at('edit', t0))], tone=tone)


# 4. The beats: {chapter index: [(the words that start the beat, builder), ...]} in spoken order.
#    face                       his camera, raw, captions on the chest
#    paint('p_x.jpg', 'right')  a public-domain painting (cv_treat.py painting), words in its dark side
#    blue_line                  the thick blue line his words break
#    quote                      the punchline as a quote on blue
#    cutout()                   the blue cut-out of a painted figure (figure.py)
#    photos([...]), screen(...) real photos / thumbnails / a real page with a ring on the thing he names
#    mark('logo.png')           a brand mark on dark
#    RM_first / RM(i, phrase)   the roadmap: first drawing, then a return at each chapter
#    MG(fn, ground)             any explainer: icons_flow, versus, tiles, bars, donut, linechart, loop, checklist, counter,
#                               head, typer, receipt, waveform, filecard (cvx.py)
BEATS = {
    0: [
        # ('first words he says', face),
        # ('the words that describe', MG(g_example)),
    ],
}

main(CHAPTERS, BEATS, title=K.get('title', 'Canvas'), fixseq=FIXSEQ, caps=CAPS)

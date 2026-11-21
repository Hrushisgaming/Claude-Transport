"""build.py — example: the same 34-second Canvas edit in LONG format (16:9).

Same words as examples/short-9x16, re-composed for 16:9 (paintings fill one side, words in the dark half; photos side by side;
the graph climbs left to right). A long video is this, chapter after chapter, with the roadmap returning at each one.
"""
import json, sys
K = json.load(open('kit.json'))
sys.path.insert(0, K['skill'] + '/components')
import cv_devices as cv
cv.set_format(K['format'])
from cv_build import *

FIXSEQ = [(['final', 'phase.'], ['Final', 'Phase.']), (['everybody'], ['Everybody'])]
CAPS = {}
EMPH.update({'edit', 'painter', 'months', 'phone', 'hour', 'better', 'good', 'left', 'camera', 'edits', 'say'})
CHAPTERS = [('ch-01', None)]


def g_raw_edit(s, t0, t1, tone):
    photo(s, 'assets/img/raw.jpg', t0, x=640, y=560, w=760, rot=-3, sound=False)
    chip(s, t0 + 0.15, 'Raw', 640, 250, 'ink')
    s.move(at('edits', t0, 0.18), 0.40, x=-180, ease='power3.inOut', smear=40)
    photo(s, 'assets/img/ed_money.jpg', at('it', t0), x=1500, y=540, w=760, rot=3, sound=False)
    chip(s, at('it', t0, 0.1), 'Edited', 1500, 250, 'blue')


def g_better(s, t0, t1, tone):
    pts = [(300, 880), (520, 880), (520, 720), (740, 720), (740, 520), (960, 520), (960, 290), (1180, 290)]
    b1 = at('better', t0)
    b2 = at('better', b1 + 0.1)
    b3 = at('better', b2 + 0.1)
    graph(s, pts, [(t0 + 0.05, 0), (b1, 2), (b2, 4), (b3, 6), (b3 + 0.34, 7)], x_label='YEARS', y_label='EDITS', axis=(270, 900, 1700, 140))


def g_good(s, t0, t1, tone):
    for img, ph, x, r in (('ed_sorrow.jpg', 'so', 430, -4), ('ed_wall.jpg', 'every', 965, 2), ('ed_louvre.jpg', 'video', 1495, -2)):
        photo(s, f'assets/img/{img}', at(ph, t0) - 0.03, x=x, y=400, w=540, rot=r, sound=False, border=10)


BEATS = {0: [
    ('everybody thinks the edit', face),
    ('but 100 years ago', paint('p_sargent.jpg', 'left')),
    ('spend months', paint('p_vermeer.jpg', 'right', enter='whip')),
    ('today you film', face),
    ('and ai edits it', MG(g_raw_edit, cap=(960, 930))),
    ('and every year', MG(g_better, ground='dark', cap=(1380, 620), maxw=640)),
    ('so soon every video', MG(g_good, cap=(960, 850))),
    ('and when every video', face),
    ('nobody sees the edit', blue_line),
    ('so the only thing left', cutout('figure.png', 'figure_halo.png', nat=(945, 1311))),
    ("it's not the camera", face),
    ("it's what you have", quote),
    ("and that's what we", mark('fp_logo.jpg')),
]}

main(CHAPTERS, BEATS, title='Canvas short 16:9', fixseq=FIXSEQ, caps=CAPS)

"""build.py — example: a 34-second Canvas SHORT (9:16), "Everybody thinks the edit is what makes a video blow up".

One chapter. The face announces, the screen shows: two paintings (Sargent, Vermeer: public domain), the raw frame vs the edited
frame, the climbing graph (one step per "better"), three edited frames, the blue line, the painted blue cut-out (Rembrandt,
public domain), the punchline as a quote on blue, the brand mark. Every time comes from work/words.json.
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
    photo(s, 'assets/img/raw.jpg', t0, x=330, y=640, w=430, rot=-3, sound=False)
    chip(s, t0 + 0.15, 'Raw', 330, 230, 'ink')
    photo(s, 'assets/img/ed_money.jpg', at('edits', t0), x=600, y=1180, w=820, rot=3, sound=False)
    chip(s, at('edits', t0, 0.1), 'Edited', 600, 900, 'blue')


def g_better(s, t0, t1, tone):
    pts = [(160, 1500), (330, 1500), (330, 1250), (500, 1250), (500, 980), (670, 980), (670, 700), (860, 700)]
    b1 = at('better', t0)
    b2 = at('better', b1 + 0.1)
    b3 = at('better', b2 + 0.1)
    graph(s, pts, [(t0 + 0.05, 0), (b1, 2), (b2, 4), (b3, 6), (b3 + 0.34, 7)], x_label='YEARS', y_label='EDITS', axis=(140, 1520, 960, 420))


def g_good(s, t0, t1, tone):
    for img, ph, y, r in (('ed_sorrow.jpg', 'every', 420, -4), ('ed_wall.jpg', 'video', 780, 2), ('ed_louvre.jpg', 'looks', 1140, -2)):
        photo(s, f'assets/img/{img}', at(ph, t0) - 0.03, x=540, y=y, w=760, rot=r, sound=False, border=10)


BEATS = {0: [
    ('everybody thinks the edit', face),
    ('but 100 years ago', paint('p_sargent.jpg')),
    ('spend months', paint('p_vermeer.jpg', enter='whip')),
    ('today you film', face),
    ('and ai edits it', MG(g_raw_edit, cap=(540, 1560))),
    ('and every year', MG(g_better, ground='dark', cap=(540, 280))),
    ('so soon every video', MG(g_good, cap=(540, 1480))),
    ('and when every video', face),
    ('nobody sees the edit', blue_line),
    ('so the only thing left', cutout('figure.png', 'figure_halo.png', nat=(945, 1311))),
    ("it's not the camera", face),
    ("it's what you have", quote),
    ("and that's what we", mark('fp_logo.jpg')),
]}

main(CHAPTERS, BEATS, title='Canvas short', fixseq=FIXSEQ, caps=CAPS)

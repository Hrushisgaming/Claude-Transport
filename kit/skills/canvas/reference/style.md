# The Canvas style, measured

Measured frame by frame off a public 57-second 9:16 reel in the "premium minimal" look (a philosophical talking head), and
re-composed for 16:9. Numbers marked *measured* come from an automated measurement; *seen* = read off a frame at a timecode.

## The idea in one line

A philosophical talking head where the face only **announces** and the screen **shows**: classical paintings, a thick blue
line, a glowing graph, a rough ultramarine cut-out of a person, real photos on paper, all under one cinematic text system
(a big Inter Black or Playfair italic key word with small Inter words fitted into the gaps around it).

## Share of screen time (seen, the reel, 24 scenes in 57.5 s)

| What | Seconds | Share |
|---|---:|---:|
| A-roll with captions (three camera angles, hard cuts) | 20.4 | 35% |
| Paintings (slide-in / whip) | 7.0 | 12% |
| Paper scenes: figure, spiral, photos, line | 15.5 | 27% |
| Dark scenes: graph, thin line | 6.0 | 10% |
| Blue ground: orbit head, quote | 7.7 | 13% |
| B-roll with text | 3.9 | 7% |

A new picture every **2.4 s** on average (24 scenes / 57.5 s). Longest hold 4.1 s (*measured*). the reference's planning rule
(13:36-14:20): "whenever he announces a new type we stay on his face, whenever he describes it we show it."

## Home base

The A-roll: the speaker raw, full frame, never zooming (*measured*: scale 1.000 +-0.2%/s across 0.5-1.9 s, 8.3-10.3 s,
41.3-43.1 s). Variety comes from hard cuts between real camera angles (wide 6.1/7.0 s, close 32.0 s, side 47.2 s), never
from a push. Captions sit on the chest, centred (*measured* 49% from the top on 9:16).

## Look (measured)

Palette by screen time: #1e1817 32%, #eeedf1 22%, #685b55 20%, #bfb6b0 8%, #2047d9 8%, #979095 4%, #1d327f 4%, #c0c5e3 3%.
Mean brightness 109, contrast 51, saturation 0.25, near-B&W frames 30%, strong colour 14%.
Sampled from full-resolution frames (the reel):

| Token | Value | Where |
|---|---|---|
| paper | #eeecf0 (#edebef / #e6e6f0 / #f9f6fa) | cool off-white, cloudy mottling, faint dot grid every ~14 px |
| dark | #161818 (#191a1a / #141616) | grain + faint ruled lines; graph and thin-line scenes |
| blue ground | #2148e0 (#1f4beb..#2f5ef4) | rough grain; orbit scene |
| blue quote | #2e4fba centre -> #0a1643 corners | heavy vignette; quote scene |
| figure | #2045de | the cut-out, deep shadows to light highlights |
| line | #1466e0 (#0b67df) | thick rounded stroke on paper |
| ink | ~#121212 | type on paper |

Paintings : "a paint and rough paper texture", edges darkened, edges blurred, slightly muted.
B-roll : "a light paper texture", darkened and blurred edges, desaturated.

## Type

- **Key word**: Inter Black, tight tracking (~-0.045em), ~8% of the frame height on 9:16; white on footage/dark/blue, ink on
  paper, accent blue on paper for the word that matters most ("French horn", "PhD").
- **Accent word**: Playfair Display Black Italic at the same size ("psychologically", "San Diego.", "steady.", "brutal.", "life").
- **Small words**: Inter Medium, ~1.7% of the frame height on 9:16 (*measured* caption height 3.1%), white or ink.
- **Placement logic** (the reference): take a line of five words or fewer, pick the most important word, set it big in the
  centre, then fit the other words small into the gaps above or below it. Rows left-, centre- or right-aligned to the big
  word ("There's" above-left of "four", "career patterns," below-right). One group on screen at a time; the next group
  hard-replaces it.
- Each word appears **on its onset**. Small words: 3 frames, blur 5 px -> 0. Big words: **5 frames**, blur ~16 px -> 0,
  scale 1.10 -> 1, opacity 0 -> 1 (frames 17-23, the reel). A soft dark shadow under white type on footage.
- Captions on 92% of the runtime (*measured*), 2 words at a time on average, never in caps.

## Transitions, frame by frame

| Move | Frames | Seen |
|---|---|---|
| A-roll <-> anything | hard cut, the next scene's first word blurs in | 2.10, 6.10, 14.15, 24.05, 32.0, 35.2 s |
| Painting slide-in | 5: already almost in place, horizontal smear, settles (power2.out) | frames 343-348 |
| Painting -> painting whip | 13: 6 accelerating out with a growing horizontal smear, 7 decelerating in | frames 371-384 |
| Into an illustration | hard cut, the figure blur-pops: blur ~22 px -> 0, scale ~1.08 -> 1, 5 frames | frames 598-603, 1315-1319 |
| Photo drop | appears whole, settles ~25 px and ~2.5 deg over 5-6 frames | frames 1001-1006 |
| Highlighter box | accent blue, scaleX 0 -> 1 from the left, ~10 frames, white number on it | frames 553-563 |
| Callout arrow | thin white curve from the subject to the words, draws in 4 frames | frames 167-170, 17.2 s |
| Camera follow | the camera tracks the ball/line with directional motion blur, ~10 frames per leg | frames 147-156, 1580-1592 |

No flashes, no black frames, no dissolves inside the reel (*measured*).

## Motion

The ground of a scene is a world bigger than the frame and a camera moves over it:
- graph and line scenes: the camera keeps travelling, following the ball or the stroke (moving 55% of the reel, *measured*)
- object and quote scenes: a slow push, **+2.5-2.6%/s** (*measured*, 37.2-38.9 s and 49.3-50.9 s)
- figure scenes: barely, +0.3-0.75%/s (*measured* 20.4-23.4 s, 44.6-46.9 s); the spiral pulls out -3.1%/s
- paintings: static once landed; the face: never.

## Beat map (the reel, reel time)

0.1 face "There's four career patterns, psychologically" · 2.1 graph, the ball climbs one step per "up", camera follows ·
6.1 face · 11.15 painting slide-in "barista" · 12.15 whip to the next painting "San Diego." · 14.15 face · 15.15 thin line
on dark "expert, slow and steady." · 17.15 painting + callout + highlighter "My dad / Same job for / 42 years" ·
20.0 blue cut-out of that painting's figure on paper, words either side "secure / low stress," · 24.05 face · 25.25 spiral
draws on paper "spirals / 7 to 12 years." · 28.15 + 30.05 B-roll with text · 32.0 face (close) · 33.05 photos drop on paper
"French horn / scientist," · 35.2 face · 37.0 photo "PhD / what I was doing." · 39.25 + 41.15 face (close, then wide) ·
43.25 blue ground, his head as a blue engraving, an orbit circle with a dot visiting "circus clown / firefighter / something."
· 47.15 face (side angle) · 49.0 quote on blue "that's what it means to live an entrepreneurial life" · 51.05 thick blue line
on paper "your calling / agility / courage", the camera pans with it · 55.05 face to the end.

## Pacing (measured)

measure.py counts every word pop and every smeared camera frame as a cut on this reel (98 "cuts", median shot 0.10 s), so
its pacing rows are not the scene rate. By eye: 24 scenes, a new picture every 2.4 s, longest 4.1 s. Cuts land within
120 ms of a word start 86% of the time (*measured*). 246 words a minute.

## Sound (measured)

A soft cinematic bed
**19.2 dB under the voice**; the bed **drops out** at 52.2 s (0.4 s) and from 56.1 s to the end, under the last line.
Very few hard hits: 0.02 a second above 3 kHz, 3.1 sub hits a minute. The palette: "a cinematic
music track, clicks for text, highlighters for graphs, whooshes for transitions". The whooshes ride the slides and whips.

## Into the user's format (16:9)

The reel is 9:16; nothing is cropped, every scene is recomposed for 16:9:
- **A-roll**: his take full frame; the caption block centred on his chest (y ~820 of 1080), key word 124 px, small 32 px.
- **Paintings**: a portrait or square painting fills the frame HEIGHT on one side and feathers into the textured dark;
  the words sit in the dark half (the reel's words always sit in the painting's quiet area).
- **Object scenes**: two photos side by side on paper; the camera slides between them.
- **Figure scenes**: the figure stands in the lower middle and bleeds off the bottom; 16:9 gives words room on BOTH sides.
- **Line / graph**: horizontal travel suits 16:9; the camera tracks sideways instead of down.
- **Quote**: centred, small marks, one big word plus an italic word.



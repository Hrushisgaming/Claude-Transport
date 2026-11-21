---
name: canvas
description: "CANVAS (also 'canvas style', 'the minimal style', 'minimalistic', 'the paintings and the blue line'): a premium minimal edit of a talking-head recording, made in code on the user's own computer, in LONG format (16:9, YouTube) or SHORT format (9:16, TikTok / Reels / Shorts). The face only announces each idea and the screen shows it: public-domain paintings that slide in with a 5-frame smear, real photos and thumbnails dropping onto textured paper, one thick blue line the words interrupt, a dark graph whose glowing ball climbs a step per word, explainer motion graphics (icons that draw themselves with a flow arrow, versus cards whose winner lifts, tile grids, bar / donut / line charts, loops, checklists, a chapter roadmap), a painted figure turned into a rough blue cut-out, and the punchline as a quote on blue. One caption system on every beat: a big Inter Black or Playfair italic key word with small words in the gaps, each word blurring in on its onset. Cuts the silences and mistakes, renders with HyperFrames, $0. Use whenever the user says canvas, /canvas, the canvas style, minimal style, or asks to edit a video in this look; also for a 'raw vs final edit' opener."
---

# Canvas

A recording goes in; a finished, captioned, sound-designed MP4 comes out, built on this computer for $0.
**Always ask first: LONG format (16:9, YouTube) or SHORT format (9:16, TikTok, Reels, Shorts)?** The answer sets the
canvas size, every layout and the caption position. Write it at the top of PLAN.md.

Read `reference/style.md` (what the style is, measured) and `reference/devices.md` (every device and when to use it) before
the first build. `examples/` holds two real builds of the same 34-second edit, one per format.

## What makes it look like this (the rules)
1. **The face announces, the screen shows.** A new idea starts on the face; the moment it is described, the screen shows the
   thing. Face 30-35% of the runtime, a new picture every ~2.4 s, never a hold over ~4.5 s.
2. **One caption system on every beat**: <= 5 words a group, the most important word big in the middle (Inter Black, or
   Playfair Black Italic for the emotional / last word), the small words fitted into the gaps above-left and below-right,
   each word blurring in on its onset (5 frames). Ink on paper (the key word may go blue), white on footage, dark and blue.
3. **Explainer graphics carry the content; paintings are the seasoning.** Paintings only where the words are literally about
   art, a scene, a feeling or a person in a story (~5 in 10 minutes). Everything else gets a device from cvx.py, and the
   chart type changes: never the same graph twice in a row.
4. **Real material on every screen beat**: public-domain paintings (Wikimedia Commons, licence written in PLAN.md), the
   creator's own thumbnails, photos and screens, real pages with a ring on the thing named. No stock strangers, no emoji,
   no AI images.
5. **The blue cut-out is a PAINTED figure** (scripts/figure.py on a public-domain portrait), never a still of the speaker's
   own take: a frame of a talking face catches a half-blink or an open mouth and looks strange in blue.
6. **His face stays raw and still**: no grade, no zoom, no punch-in. Variety comes from the cuts, never from crops.
7. **Motion only where the reference moves**: graph and line scenes keep tracking, object and quote scenes push ~2.5%/s,
   paintings sit still once landed. Camera moves stay inside the world (cvx.clamp).
8. **Sound**: one quiet sound per scene change (the devices write the cue sheet), nothing per word. Music only if the creator
   gives a track, only where they want it (e.g. the first 90 s), ~19 dB under the voice, cut out under the punchline.
9. **Nothing is published or uploaded.** The skill renders, opens the file and stops.

## The workflow
Every command starts with `source ~/.claude/skills/canvas/scripts/env.sh` (puts node / ffmpeg on PATH, sets `$CV_PY`, pins
the renderer). `SK=~/.claude/skills/canvas`.

1. **New video**: `bash $SK/scripts/new-video.sh <recording> --long` (or `--short`; a horizontal take for a short is cropped
   to 9:16 around `--fx 0.5`: look at a frame and set fx to the speaker's face). Creates `~/canvas/videos/<name>/`.
2. **Transcribe**: `"$CV_PY" $SK/scripts/transcribe.py <video>` then `"$CV_PY" $SK/scripts/snap-onsets.py <video>`.
   Read `work/tx/transcript.txt` start to end. Fix misheard names later in build.py's FIXSEQ (never in the timings).
3. **Cut the mistakes**: write `work/cut/remove.json` = `[[start, end, "what"], ...]` in take seconds: every restart (remove
   the first tries, keep the last clean take), a sentence said twice, a misspoken name, a stutter, a claim that is wrong (say
   so to the creator). Then `"$CV_PY" $SK/scripts/cut.py <video>` (edges move to the nearest silence; pauses > 0.5 s become
   0.3 s; the camera is cut by frame index). Re-transcribe the cut voice
   (`transcribe.py <video> --src assets/media/vo_cut.wav`, it overwrites work/tx, so copy words.json first) and read every
   join listed in work/cut/joins.txt: a removed word must not leak in.
4. **Plan** in PLAN.md: chapters (long format: 40-130 s each, split mid-face; short: one chapter), then every beat:
   the words that start it -> the device -> the real asset and its licence. Show the creator the plan if they asked to see it.
5. **Assets** into `<video>/assets/img/`: paintings `"$CV_PY" $SK/scripts/cv_treat.py painting <src.jpg> assets/img/p_x.jpg --side right`
   (16:9: right|left|full; 9:16: `--side full --portrait --fx <subject x>`), photos `cv_treat.py photo`, the cut-out
   `figure.py <portrait.jpg> assets/img/figure.png`, screens as JPGs + their boxes in `assets/img/shots.json`.
6. **Build**: fill `build.py` (CHAPTERS, BEATS, FIXSEQ, CAPS, EMPH, your explainer functions) and run `"$CV_PY" build.py`.
   It prints the holds over 4.5 s, the face share and the picture rate. Fix the plan until they're in range.
7. **Look before rendering**: `npx -y hyperframes@$HF_VERSION snapshot <chapter> --at <times> --no-end -o work/snap_<chapter>`
   at ~70% of every beat. Look at every contact sheet: no empty scene, nothing clipped, captions readable, the right thing on
   the right word. Fix, rebuild, re-snapshot.
8. **Render**: `bash $SK/scripts/render.sh <video>` (every chapter, frame-checked, joined into out/render.mp4, the sound cues
   merged). Needs ~2 GB of free disk while it runs.
9. **Sound + finish**: with music, `"$CV_PY" $SK/scripts/bed-mix.py --voice assets/media/vo_cut.wav --song <their track>
   --song-at 0 --dur <seconds> --under 18.6 --ramp <a>,<b>,-70 ... --out work/premix.wav`; then
   `bash $SK/scripts/finish.sh <video>` (-14 LUFS, opens the file). Make a contact sheet of the final and look at it.
10. **Raw vs final edit opener** (optional, for a video about the edit itself): edit a short in 16:9 first, then
    `"$CV_PY" $SK/scripts/rawvsedit.py <short> <out>`: the raw cut and the finished edit side by side, in sync, with the
    edit's real timeline under them.

## Files
- `components/cv_devices.py` — the core devices with every measured frame count: Comp, Scene (a world with its own camera
  and motion blur), cap (the caption system), aroll, painting, photo, figure, line, graph, highlight, callout, quote_marks.
- `components/cvx.py` — the motion-graphics layer: roadmap, counter, sharebar, Shot (real screens + rings + scroll), typer,
  tiles, chip, filecard, strike, band, blurstrip, waveform, vidcard, receipt, and the explainers icon / icons_flow / arrow /
  loop / versus / tiles / head / bars / donut / linechart / checklist. Lucide line icons in assets/icons (ISC).
- `components/cv_build.py` — words -> chapters -> beats, the caption grouping, the beat helpers (face, paint, quote, cutout,
  MG, photos, screen, mark, blue_line, RM, RM_first).
- `scripts/` — env.sh, doctor.sh, new-video.sh, transcribe.py, snap-onsets.py, cut.py, cv_treat.py, figure.py, matte.py,
  render.sh, bed-mix.py, mix-sfx.py, synth-sfx.py, finish.sh, preview.py, rawvsedit.py.
- `template/` — build.py, PLAN.md, rawvsedit.html. `examples/` — the 34 s edit at 16:9 and at 9:16 (code only).
- `assets/` — tokens.css (every colour and size), canvas.css, Inter + Playfair Display (OFL), the grounds (drawn by
  doctor.sh), a public-domain painting and a ready painted cut-out for the preview.

## Notes become rules
When the creator gives a note on an edit ("too many paintings", "the music only for the first minute"), add it to the end of
this file as a rule with the date, and follow it from the next video on.

- (rule) More explainer motion graphics, fewer paintings; vary the chart type; the cut-out comes from a painted figure.
- (rule) Music is optional and only where the creator wants it; the cut back to the face is silent.

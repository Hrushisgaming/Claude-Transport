# Style family: lms-chase

Members (8): necrobloxians, vigilante, onebounce, eternityv2, eternity_forsakened, agravesoul, eternalhope, lmsy2k. Most typical member: **agravesoul**.

## What they ALL share (this is the style: copy it)
- Tempo clusters (feel BPM): 175.0 BPM x5 (range 164.0-180.0); 196.5 BPM x2 (range 193.0-200.0); 120.0 BPM x1 (range 120.0-120.0). Pick one cluster; do not average clusters.
- Key votes: {'A minor': 4, 'B minor': 3, 'F# minor': 1}.
- First drop at 9.8% of the track (range 4.6-16.2%); 8 of 8 have a clear drop; drops per track 1-6.
- Anatomy of a drop: impact on it in 59%, a cut right before in 0%, a riser before in 0% of drops.
- Layers that enter at drops (count of drops): {'+air': 7, '+sub': 5, '+bass': 4, '+lowmid': 4, '+mid': 4, '+highmid': 3}.
- Typical share of the track (median %, in how many tracks that section exists): build 16.4% (6/8), drop 76.9% (7/8), outro 5.8% (8/8), break 8.6% (6/8), intro 6.1% (1/8), verse 78.8% (1/8). Section labels are energy heuristics.
- Chord cycles seen (bars): [4, 4, 4, 4, 4, 8, 16].

## What VARIES (your room to be original)
| measure | min | median | max |
|---|---|---|---|
| mix.lufs | -15.0 | -12.05 | -7.6 |
| mix.crest_db | 10.8 | 14.24 | 16.99 |
| mix.side_to_mid_db | -12.93 | -8.4 | -5.61 |
| timbre.centroid_hz | 2193.8 | 2592.3 | 3030.9 |
| timbre.flatness | 0.482 | 0.601 | 0.702 |
| rhythm.onsets_per_beat | 1.73 | 2.37 | 4.31 |
| deep.hard_points.hits_per_min | 0.0 | 1.5 | 8.0 |
| deep.hard_points.stops_per_min | 0.0 | 0.0 | 0.0 |
| deep.lead_layer.share_of_bars | 0.1 | 0.23 | 0.38 |

Loop-ready members: 0 of 8 (finished rips rarely are; yours must be). Role guesses: {'chase / last-man-standing (fast, driving)': 7, 'tension / mid-intensity round music': 1}.

Compare your build with `af.py compare cand.wav <this folder>/dna.json`: a number INSIDE the member range is fine, you do not have to hit the median.

---

# Median measurements (same format as a single-track brief)
# Style brief: lms-chase

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **175.0 BPM**, 4/4, swing 0.007 |
| key / mode | **A minor** (relative D major) |
| loudness | -12.05 LUFS integrated, loudness range 4.1 LU, true peak -0.05 dB, crest 14.24 dB |
| brightness | spectral centroid 2592.3 Hz, 85% rolloff 1119.7 Hz, flatness 0.601, 3-8 kHz vs 0.2-3 kHz -7.3 dB |
| balance (dB re full scale) | sub -9.65, bass -3.1, low-mid -10.55, mid -8.25, high-mid -11.1, air -18.5 |
| stereo | side/mid -8.4 dB, L/R correlation 0.748; by band {'low': 0.85, 'mid': 0.665, 'high': 0.655} |
| rhythmic density | 6.545 attacks/s = 2.37 per beat; sustain (12 dB fall) 122 ms |

## 2. Arrangement shape
Sections: intro 9 bars (energy 0.17), drop 16 bars (energy 1.0), break 8 bars (energy 0.24), outro 17 bars (energy 0.0). Drops at [13.2] s. Energy per bar (dB below the loudest bar): `[-6.2, -2.4, -3.7, -3.2, -3.4, -2.1, -3.7, -3.4, -2.0, -0.6, -1.9, -1.8, -1.5, -0.8, -1.9, -2.0, -1.5, -1.2, -2.9, -2.7, -2.2, -0.6, -1.7, -1.4, -0.9, -1.8, -4.1, -4.3, -4.0, -1.7, -3.4, -3.1, -2.9, -0.7, -0.9, -0.3, -1.1, -1.5, -1.0, 0.0, -1.4, -1.3, -1.1, -0.5, -1.3, -1.1, -1.0, -4.3, -13.4, -31.6]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.9, 0.435, 0.765, 0.375, 0.885, 0.57, 0.805, 0.315, 0.815, 0.34, 0.825, 0.385, 0.94, 0.655, 0.73, 0.385]`  (grid confidence 0.76)
Drum hints (full mix, approximate): kick `Xoxxx.Xoxxxox.oo`, snare `X.xoX.X.xox.X.x.`, hat `X.x.x.X.xox.X.xo`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.83, chord changes per bar 0.635, most-used degrees ['V', 'I', 'bVII', 'bIII']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'I', 'V', 'V']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.5502, 3-8k vs 0.2-3k -8.9 dB)
- articulation: muted / staccato (median 12 dB fall 115.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick Xoxxx.Xoxxxox.oo, snare X.xoX.X.xox.X.x.; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 169.0, it behaves like **175.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B C C' C' D E** = build 8 bars (16.0%), drop 10 bars (20.0%), drop 8 bars (16.0%), break 4 bars (8.0%), build 3 bars (6.0%), drop 14 bars (28.0%), outro 3 bars (6.0%). Chord cycle: 4 bars.
- DROP at 16.0% (bar 9): bass +2.6 dB, brightness +655 Hz
- DROP at 66.0% (bar 34): bass +2.3 dB, brightness -27 Hz
- Hard hits 1.5/min (types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1, on beat 1 0.85.
Layers at section boundaries (what to add or take away there):
- bar 9 (drop): +sub 4dB, +air 7dB
- bar 19 (drop): no big change
- bar 27 (break): -lowmid 4dB, -highmid 4dB, -air 4dB
- bar 31 (build): no big change
- bar 34 (drop): +mid 4dB, +air 3dB
- bar 48 (outro): -sub 8dB, -bass 7dB, -lowmid 9dB, -mid 10dB, -highmid 8dB, -air 7dB
Loop-readiness of the reference file: NOT ready (ends with 3.3 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -60 dB vs first 0.25 s -19 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre lms_chase --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav lms-chase/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

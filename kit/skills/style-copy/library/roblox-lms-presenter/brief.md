# Style family: lms-presenter

Members (2): showtime, fired. Most typical member: **showtime**.

## What they ALL share (this is the style: copy it)
- Tempo clusters (feel BPM): 171.1 BPM x2 (range 165.2-177.0). Pick one cluster; do not average clusters.
- Key votes: {'G minor': 1, 'G# minor': 1}.
- First drop at 8.3% of the track (range 5.4-11.2%); 2 of 2 have a clear drop; drops per track 2-3.
- Anatomy of a drop: impact on it in 40%, a cut right before in 0%, a riser before in 20% of drops.
- Layers that enter at drops (count of drops): {'+highmid': 3, '+air': 3, '+sub': 1, '+bass': 1, '+lowmid': 1, '+mid': 1, '-lowmid': 1}.
- Typical share of the track (median %, in how many tracks that section exists): intro 7.4% (2/2), build 34.0% (2/2), drop 54.2% (2/2), outro 3.0% (2/2), break 3.0% (1/2). Section labels are energy heuristics.
- Chord cycles seen (bars): [8].

## What VARIES (your room to be original)
| measure | min | median | max |
|---|---|---|---|
| mix.lufs | -14.5 | -12.45 | -10.4 |
| mix.crest_db | 13.94 | 14.195 | 14.45 |
| mix.side_to_mid_db | -8.64 | -7.535 | -6.43 |
| timbre.centroid_hz | 2673.5 | 2777.35 | 2881.2 |
| timbre.flatness | 0.609 | 0.64 | 0.672 |
| rhythm.onsets_per_beat | 1.7 | 1.765 | 1.83 |
| deep.hard_points.hits_per_min | 0.6 | 1.6 | 2.6 |
| deep.hard_points.stops_per_min | 0.0 | 0.3 | 0.6 |
| deep.lead_layer.share_of_bars | 0.19 | 0.225 | 0.26 |

Loop-ready members: 0 of 2 (finished rips rarely are; yours must be). Role guesses: {'chase / last-man-standing (fast, driving)': 2}.

Compare your build with `af.py compare cand.wav <this folder>/dna.json`: a number INSIDE the member range is fine, you do not have to hit the median.

---

# Median measurements (same format as a single-track brief)
# Style brief: lms-presenter

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **171.1 BPM**, 4/4, swing 0.023 |
| key / mode | **G minor** (relative A# major) |
| loudness | -12.45 LUFS integrated, loudness range 5.65 LU, true peak -1.0 dB, crest 14.195 dB |
| brightness | spectral centroid 2777.35 Hz, 85% rolloff 1625.8 Hz, flatness 0.64, 3-8 kHz vs 0.2-3 kHz -8.65 dB |
| balance (dB re full scale) | sub -11.35, bass -3.65, low-mid -11.1, mid -5.95, high-mid -9.7, air -17.5 |
| stereo | side/mid -7.535 dB, L/R correlation 0.696; by band {'low': 0.95, 'mid': 0.58, 'high': 0.485} |
| rhythmic density | 5.045 attacks/s = 1.765 per beat; sustain (12 dB fall) 172 ms |

## 2. Arrangement shape
Sections: intro 3 bars (energy 0.0), break 4 bars (energy 0.3), drop 16 bars (energy 1.0), drop 17 bars (energy 0.91), drop 28 bars (energy 0.91). Drops at [23.138] s. Energy per bar (dB below the loudest bar): `[-12.6, -10.7, -11.4, -9.2, -9.6, -8.5, -8.4, -4.2, -3.1, -3.1, -2.5, -3.1, -3.0, -2.7, -2.1, -3.6, -2.4, -2.5, -2.0, -2.1, -2.3, -2.0, -1.8, -3.1, -4.8, -3.5, -4.0, -3.1, -3.9, -3.0, -3.2, -1.9, -4.1, -3.1, -3.5, -2.7, -4.0, -3.6, -3.4, -3.1, -1.7, -1.7, -1.3, -1.5, -1.6, -1.4, -1.0, -1.6, -1.1, -1.4, -0.7, -1.4, -1.6, -1.2, -1.0, -5.6, -10.9, -1.8, -0.6, -0.8, -0.5, -1.6, -1.3, -1.0, 0.0, -1.7, -12.8, -38.7]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.865, 0.235, 0.495, 0.28, 0.895, 0.235, 0.475, 0.195, 0.97, 0.365, 0.655, 0.3, 0.73, 0.14, 0.455, 0.375]`  (grid confidence 0.485)
Drum hints (full mix, approximate): kick `x...X..xo.x.x.o.`, snare `X.o.x.o.X.o.x.oo`, hat `X.o.X.x.X.x.X.xo`.

## 4. Harmony (reduced on purpose)
Power-chord share 0, third share 0.745, chord changes per bar 0.585, most-used degrees ['I', 'V', 'bII', 'VII']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'V', 'I', 'I']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.6719, 3-8k vs 0.2-3k -8.2 dB)
- articulation: mixed (median 12 dB fall 160.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick x...X..xo.x.x.o., snare X.o.x.o.X.o.x.oo; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 171.1, it behaves like **171.1 BPM** (medium confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B C B' D B' E** = intro 7 bars (10.3%), build 32 bars (47.1%), drop 9 bars (13.2%), drop 7 bars (10.3%), build 2 bars (2.9%), drop 8 bars (11.8%), outro 3 bars (4.4%). Chord cycle: none found bars.
- DROP at 11.2% (bar 8): riser +46 dB over 6.62 s -> full impact (+9.7 dB, one-shot 1.59 s) -> bass +5.5 dB, brightness +1331 Hz
- DROP at 57.4% (bar 40): full impact (+8.0 dB, one-shot 0.23 s) -> bass +2.2 dB, brightness -223 Hz
- DROP at 83.4% (bar 58): bass +5.8 dB, brightness -2133 Hz
- Hard hits 1.6/min (types {'full impact': 2, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.3/min, hits on the 16th grid 1, on beat 1 0.
- Riser at 4.7% for 6.62 s (+45.9 dB in the high bands)
- Hard stop at 23.0% for 0.1 s, then full impact
Layers at section boundaries (what to add or take away there):
- bar 8 (build): +sub 9dB, +bass 4dB, +mid 4dB, +highmid 3dB, +air 8dB
- bar 40 (drop): no big change
- bar 49 (drop): no big change
- bar 56 (build): -sub 11dB, -bass 5dB, -lowmid 15dB, -mid 13dB, -highmid 7dB
- bar 58 (drop): +sub 8dB, +bass 5dB, +lowmid 15dB, +mid 13dB, +highmid 8dB, +air 3dB
- bar 66 (outro): -sub 13dB, -bass 5dB, -lowmid 8dB, -mid 8dB, -highmid 5dB, -air 7dB
Loop-readiness of the reference file: NOT ready (ends with 2.8 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -65 dB vs first 0.25 s -20 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre lms_presenter --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav lms-presenter/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

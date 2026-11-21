# Style brief: showtime

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **176.98 BPM** (could also feel like 354.0, 88.5: ask which feels right), 4/4, swing 0.038 |
| key / mode | **G minor** (relative A# major) |
| loudness | -10.4 LUFS integrated, loudness range 6.9 LU, true peak 0.4 dB, crest 13.96 dB |
| brightness | spectral centroid 2888.1 Hz, 85% rolloff 1356.6 Hz, flatness 0.6734, 3-8 kHz vs 0.2-3 kHz -8.2 dB |
| balance (dB re full scale) | sub -7.8, bass -3.9, low-mid -9.9, mid -6.8, high-mid -10.6, air -16.4 |
| stereo | side/mid -8.64 dB, L/R correlation 0.762; by band {'low': 0.98, 'mid': 0.64, 'high': 0.6} |
| rhythmic density | 5.33 attacks/s = 1.81 per beat; sustain (12 dB fall) 165.0 ms |

## 2. Arrangement shape
Sections: intro 3 bars (energy 0.0), break 4 bars (energy 0.3), drop 16 bars (energy 1.0), drop 17 bars (energy 0.91), drop 28 bars (energy 0.91). Drops at [10.516] s. Energy per bar (dB below the loudest bar): `[-12.6, -10.7, -11.4, -9.2, -9.6, -8.5, -8.4, -4.2, -3.1, -3.1, -2.5, -3.1, -3.0, -2.7, -2.1, -3.6, -2.4, -2.5, -2.0, -2.1, -2.3, -2.0, -1.8, -3.1, -4.8, -3.5, -4.0, -3.1, -3.9, -3.0, -3.2, -1.9, -4.1, -3.1, -3.5, -2.7, -4.0, -3.6, -3.4, -3.1, -1.8, -1.7, -1.3, -1.5, -1.6, -1.4, -1.0, -1.6, -1.1, -1.4, -0.7, -1.4, -1.6, -1.2, -1.0, -5.6, -10.9, -1.8, -0.6, -0.8, -0.5, -1.6, -1.3, -1.0, 0.0, -1.7, -12.8, -38.7]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.87, 0.29, 0.29, 0.29, 0.79, 0.33, 0.29, 0.21, 1.0, 0.33, 0.42, 0.17, 0.75, 0.08, 0.37, 0.29]`  (grid confidence 0.33)
Drum hints (full mix, approximate): kick `x...X..xo.x.x.o.`, snare `X.o.x.o.X.o.x.oo`, hat `X.o.X.x.X.x.X.xo`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.82, chord changes per bar 0.41, most-used degrees ['I', 'V', 'bII', 'VII']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'V', 'I', 'I']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.6734, 3-8k vs 0.2-3k -8.2 dB)
- articulation: mixed (median 12 dB fall 165.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick x...X..xo.x.x.o., snare X.o.x.o.X.o.x.oo; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 177.0, it behaves like **177.0 BPM** (medium confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B C D B' E** = intro 7 bars (10.3%), drop 20 bars (29.4%), break 12 bars (17.6%), drop 9 bars (13.2%), drop 9 bars (13.2%), outro 11 bars (16.2%). Chord cycle: none found bars.
- DROP at 11.2% (bar 8): riser +46 dB over 6.62 s -> full impact (+9.7 dB, one-shot 1.59 s) -> bass +5.5 dB, brightness +1344 Hz
- DROP at 57.4% (bar 40): full impact (+8.0 dB, one-shot 0.23 s) -> bass +2.2 dB, brightness -226 Hz
- DROP at 83.4% (bar 58): bass +5.8 dB, brightness -2129 Hz
- Hard hits 2.6/min (types {'full impact': 4, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.6/min, hits on the 16th grid 1.0, on beat 1 0.0.
- Riser at 4.7% for 6.62 s (+45.9 dB in the high bands)
- Hard stop at 23.0% for 0.1 s, then full impact
Layers at section boundaries (what to add or take away there):
- bar 8 (drop): +sub 9dB, +bass 4dB, +mid 4dB, +highmid 3dB, +air 8dB
- bar 28 (break): no big change
- bar 40 (drop): no big change
- bar 49 (drop): no big change
- bar 58 (outro): +sub 8dB, +bass 5dB, +lowmid 15dB, +mid 13dB, +highmid 8dB, +air 3dB
Loop-readiness of the reference file: NOT ready (ends with 2.8 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -64 dB vs first 0.25 s -20 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre showtime --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav showtime/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

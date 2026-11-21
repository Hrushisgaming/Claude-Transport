# Style brief: eternity-v2

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **179.98 BPM** (could also feel like 360.0, 90.0: ask which feels right), 4/4, swing 0.026 |
| key / mode | **A minor** (relative C major) |
| loudness | -15.0 LUFS integrated, loudness range 7.7 LU, true peak -0.3 dB, crest 16.99 dB |
| brightness | spectral centroid 2210.1 Hz, 85% rolloff 753.7 Hz, flatness 0.5234, 3-8 kHz vs 0.2-3 kHz -13.5 dB |
| balance (dB re full scale) | sub -10.1, bass -3.7, low-mid -7.6, mid -5.9, high-mid -14.7, air -20.5 |
| stereo | side/mid -8.69 dB, L/R correlation 0.762; by band {'low': 0.89, 'mid': 0.69, 'high': 0.65} |
| rhythmic density | 5.2 attacks/s = 1.73 per beat; sustain (12 dB fall) 160.0 ms |

## 2. Arrangement shape
Sections: drop 7 bars (energy 0.94), drop 17 bars (energy 1.0), drop 16 bars (energy 0.87), drop 8 bars (energy 1.0), drop 4 bars (energy 0.81), drop 5 bars (energy 0.73), outro 2 bars (energy 0.0). Drops at [0.333] s. Energy per bar (dB below the loudest bar): `[-4.4, -4.3, -4.3, -4.7, -1.3, -3.2, -2.0, -2.3, -1.1, -1.9, -1.9, -2.3, -2.2, -2.4, -0.9, -0.2, -0.8, -2.1, -1.8, -2.0, -2.0, -2.2, -0.6, -0.3, -2.8, -10.5, -3.7, -7.5, -2.8, -10.6, -4.0, -5.3, -2.0, -9.0, -2.8, -7.0, -1.7, -8.0, -2.3, -4.5, -1.1, -2.0, -2.2, -2.1, -1.9, -2.3, -0.7, 0.0, -4.9, -7.3, -7.7, -8.7, -6.2, -8.7, -6.5, -10.0, -16.5, -27.3, -35.2]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.84, 0.37, 0.58, 0.21, 0.63, 0.95, 0.63, 0.11, 0.63, 0.21, 0.63, 0.0, 1.0, 0.89, 0.53, 0.16]`  (grid confidence 0.38)
Drum hints (full mix, approximate): kick `X.....X...o.x.x.`, snare `X...x.o.o.x.X.o.`, hat `X...X...o.x.X...`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.17, third share 0.39, chord changes per bar 0.54, most-used degrees ['I', 'V', 'VII', 'bVII']. Example loop (FLAVOUR ONLY, do not copy): ['I', 'I', 'I', 'V']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.5234, 3-8k vs 0.2-3k -13.5 dB)
- articulation: mixed (median 12 dB fall 160.0 ms)
- chords: mixed
- drums: probably yes (kick X.....X...o.x.x., snare X...x.o.o.x.X.o.; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 180.0, it behaves like **180.0 BPM** (medium confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A A' B C D B E** = build 4 bars (6.7%), drop 15 bars (25.0%), break 9 bars (15.0%), break 3 bars (5.0%), break 4 bars (6.7%), break 9 bars (15.0%), outro 16 bars (26.7%). Chord cycle: 16 bars.
- DROP at 7.1% (bar 5): bass +5.1 dB, brightness -296 Hz
- DROP at 51.9% (bar 32): bass +2.5 dB, brightness +150 Hz
- Hard hits 2.2/min (types {'full impact': 2, 'sub/kick impact': 1, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 0.33.
- Riser at 11.9% for 1.51 s (+13.1 dB in the high bands)
Layers at section boundaries (what to add or take away there):
- bar 5 (drop): +sub 7dB, +bass 4dB
- bar 20 (break): no big change
- bar 29 (break): no big change
- bar 32 (break): +bass 4dB, +lowmid 5dB, +highmid 4dB, +air 6dB
- bar 36 (break): no big change
- bar 45 (outro): no big change
Loop-readiness of the reference file: NOT ready (ends with 5.8 s of fade/silence: a looping Sound would play that gap every cycle; starts with 0.4 s of quiet before the music). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre eternity_v2 --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav eternity-v2/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

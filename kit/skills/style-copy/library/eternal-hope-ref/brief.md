# Style brief: hope-ref

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **173.97 BPM** (could also feel like 347.9, 87.0: ask which feels right), 4/4, swing 0.011 |
| key / mode | **A minor** (relative C major) |
| loudness | -14.6 LUFS integrated, loudness range 1.7 LU, true peak -0.3 dB, crest 16.79 dB |
| brightness | spectral centroid 3030.9 Hz, 85% rolloff 1184.3 Hz, flatness 0.7019, 3-8 kHz vs 0.2-3 kHz -5.5 dB |
| balance (dB re full scale) | sub -7.1, bass -2.8, low-mid -13.0, mid -9.0, high-mid -10.9, air -15.9 |
| stereo | side/mid -7.22 dB, L/R correlation 0.681; by band {'low': 0.72, 'mid': 0.58, 'high': 0.85} |
| rhythmic density | 5.5 attacks/s = 1.9 per beat; sustain (12 dB fall) 165.0 ms |

## 2. Arrangement shape
Sections: build 9 bars (energy 0.62), drop 7 bars (energy 0.82), drop 8 bars (energy 1.0), drop 24 bars (energy 0.74), outro 4 bars (energy 0.0). Drops at [13.251] s. Energy per bar (dB below the loudest bar): `[-1.0, -3.5, -1.5, -3.3, -2.0, -4.1, -2.7, -4.2, -1.3, -1.1, -1.4, -1.2, -1.6, -1.7, -1.8, -1.4, 0.0, -0.2, -0.8, -0.3, -0.7, -0.4, -0.8, -0.4, -1.1, -1.6, -1.9, -1.8, -2.1, -2.0, -2.3, -2.1, -2.2, -1.3, -1.8, -1.7, -2.0, -1.7, -2.3, -1.8, -1.6, -1.8, -2.3, -2.0, -2.3, -1.9, -2.3, -2.0, -2.4, -7.8, -9.4, -4.7]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.85, 0.02, 0.85, 0.02, 1.0, 0.02, 1.0, 0.0, 0.8, 0.22, 0.57, 0.0, 0.95, 0.02, 0.6, 0.35]`  (grid confidence 0.72)
Drum hints (full mix, approximate): kick `Xx..ooXo.xx.xo.o`, snare `X.X.X.x.XoX.X.xo`, hat `X.x.X.x.X.x.X.xo`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.92, chord changes per bar 0.37, most-used degrees ['I', 'II', 'V', 'VII']. Example loop (FLAVOUR ONLY, do not copy): ['I', 'IV', 'IV', 'II']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.7019, 3-8k vs 0.2-3k -5.5 dB)
- articulation: mixed (median 12 dB fall 165.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick Xx..ooXo.xx.xo.o, snare X.X.X.x.XoX.X.xo; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 174.0, it behaves like **174.0 BPM** (medium confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B C D D'** = drop 8 bars (15.1%), drop 25 bars (47.2%), drop 16 bars (30.2%), break 2 bars (3.8%), outro 2 bars (3.8%). Chord cycle: 4 bars.
- DROP at 16.2% (bar 9): full impact (+9.4 dB, one-shot 1.88 s) -> bass +2.1 dB, brightness +518 Hz
- Hard hits 4.1/min (types {'full impact': 2, 'sub/kick impact': 3, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 0.6.
Layers at section boundaries (what to add or take away there):
- bar 9 (drop): +air 4dB
- bar 34 (drop): no big change
- bar 50 (break): -bass 8dB, -lowmid 6dB, -mid 7dB, -highmid 9dB, -air 13dB
- bar 52 (outro): -sub 45dB, -bass 34dB, -lowmid 25dB, -mid 27dB, -highmid 32dB, -air 26dB
Loop-readiness of the reference file: NOT ready (ends with 1.5 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -90 dB vs first 0.25 s -28 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre hope_ref --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav hope-ref/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

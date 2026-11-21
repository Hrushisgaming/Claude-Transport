# Style brief: vigilante-shootdown

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **120.02 BPM** (could also feel like 240.0, 60.0: ask which feels right), 4/4, swing 0.0 |
| key / mode | **B minor** (relative D major) |
| loudness | -9.5 LUFS integrated, loudness range 3.8 LU, true peak 1.4 dB, crest 13.32 dB |
| brightness | spectral centroid 2961.9 Hz, 85% rolloff 2196.4 Hz, flatness 0.6791, 3-8 kHz vs 0.2-3 kHz -5.7 dB |
| balance (dB re full scale) | sub -11.8, bass -3.1, low-mid -8.6, mid -8.4, high-mid -8.8, air -15.3 |
| stereo | side/mid -8.81 dB, L/R correlation 0.768; by band {'low': 0.84, 'mid': 0.73, 'high': 0.69} |
| rhythmic density | 5.51 attacks/s = 2.76 per beat; sustain (12 dB fall) 130.0 ms |

## 2. Arrangement shape
Sections: intro 3 bars (energy 0.0), build 5 bars (energy 0.54), drop 8 bars (energy 0.91), drop 9 bars (energy 0.9), drop 4 bars (energy 1.0), drop 4 bars (energy 0.82), outro 5 bars (energy 0.04). Drops at [16.857] s. Energy per bar (dB below the loudest bar): `[-6.0, -6.7, -5.5, -4.0, -2.6, -2.8, -2.5, -2.2, -0.7, -0.6, -0.9, -0.8, -0.6, -0.6, -0.9, -0.6, -0.9, -0.8, -1.1, -0.6, -0.7, -0.5, -0.8, -0.9, -0.5, 0.0, -0.2, -0.5, -0.1, -0.9, -1.0, -1.1, -1.9, -4.3, -4.9, -4.4, -1.5, -13.9]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[1.0, 0.64, 0.7, 0.76, 0.88, 0.82, 0.58, 0.76, 1.0, 0.88, 0.85, 0.76, 0.94, 0.91, 0.48, 0.55]`  (grid confidence 0.95)
Drum hints (full mix, approximate): kick `..X...X...X...X.`, snare `XooxXxoxXooxxx.x`, hat `Xo.xXx.oXo.xxx.o`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.76, chord changes per bar 0.68, most-used degrees ['I', 'IV', 'bVII', 'bIII']. Example loop (FLAVOUR ONLY, do not copy): ['I', 'I', 'I', 'bVII']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.6791, 3-8k vs 0.2-3k -5.7 dB)
- articulation: muted / staccato (median 12 dB fall 130.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick ..X...X...X...X., snare XooxXxoxXooxxx.x; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 120.0, it behaves like **120.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): tension / mid-intensity round music.
Form: **A B** = build 3 bars (7.7%), drop 36 bars (92.3%). Chord cycle: 4 bars.
- DROP at 8.7% (bar 4): bass +3.3 dB, brightness +558 Hz
- Hard hits 0.0/min (types {'full impact': 0, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid None, on beat 1 None.
- Riser at 93.0% for 0.96 s (+12.5 dB in the high bands)
Layers at section boundaries (what to add or take away there):
- bar 4 (drop): +sub 18dB, +air 9dB
Loop-readiness of the reference file: NOT ready (ends with 3.4 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -90 dB vs first 0.25 s -24 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre vigilante_shootdown --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav vigilante-shootdown/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

# Style brief: a-grave-soul-now-run

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **164.0 BPM** (could also feel like 328.0, 82.0: ask which feels right), 4/4, swing 0.0 |
| key / mode | **B minor** (relative D major) |
| loudness | -12.6 LUFS integrated, loudness range 3.2 LU, true peak -2.0 dB, crest 12.5 dB |
| brightness | spectral centroid 2369.3 Hz, 85% rolloff 796.7 Hz, flatness 0.5502, 3-8 kHz vs 0.2-3 kHz -8.9 dB |
| balance (dB re full scale) | sub -10.5, bass -3.1, low-mid -7.5, mid -9.2, high-mid -11.4, air -20.2 |
| stereo | side/mid -7.09 dB, L/R correlation 0.669; by band {'low': 0.79, 'mid': 0.6, 'high': 0.45} |
| rhythmic density | 6.84 attacks/s = 2.5 per beat; sustain (12 dB fall) 115.0 ms |

## 2. Arrangement shape
Sections: intro 9 bars (energy 0.17), drop 16 bars (energy 1.0), break 8 bars (energy 0.24), outro 17 bars (energy 0.0). Drops at [13.2] s. Energy per bar (dB below the loudest bar): `[-6.2, -2.4, -3.7, -3.2, -3.4, -2.1, -3.7, -3.4, -2.0, -0.6, -1.9, -1.8, -1.5, -0.8, -1.9, -2.0, -1.5, -1.2, -2.9, -2.7, -2.2, -0.6, -1.7, -1.4, -0.9, -1.8, -4.1, -4.3, -4.0, -1.7, -3.4, -3.1, -2.9, -0.7, -0.9, -0.3, -1.1, -1.5, -1.0, 0.0, -1.4, -1.3, -1.1, -0.5, -1.3, -1.1, -1.0, -4.3, -13.4, -31.6]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[1.0, 0.1, 0.87, 0.62, 0.94, 0.17, 0.94, 0.25, 0.83, 0.35, 0.83, 0.12, 0.94, 0.12, 0.87, 0.42]`  (grid confidence 0.9)
Drum hints (full mix, approximate): kick `Xoxxx.Xoxxxox.oo`, snare `X.xoX.X.xox.X.x.`, hat `X.x.x.X.xox.X.xo`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.98, chord changes per bar 0.62, most-used degrees ['V', 'I', 'bVII', 'bIII']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'I', 'V', 'V']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.5502, 3-8k vs 0.2-3k -8.9 dB)
- articulation: muted / staccato (median 12 dB fall 115.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick Xoxxx.Xoxxxox.oo, snare X.xoX.X.xox.X.x.; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 164.0, it behaves like **164.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B C D** = build 8 bars (16.0%), drop 10 bars (20.0%), drop 15 bars (30.0%), outro 17 bars (34.0%). Chord cycle: 8 bars.
- DROP at 16.0% (bar 9): bass +2.6 dB, brightness +655 Hz
- DROP at 66.0% (bar 34): bass +2.3 dB, brightness -27 Hz
- Hard hits 0.8/min (types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 1.0.
Layers at section boundaries (what to add or take away there):
- bar 9 (drop): +sub 4dB, +air 7dB
- bar 19 (drop): no big change
- bar 34 (outro): +mid 4dB, +air 3dB
Loop-readiness of the reference file: NOT ready (ends with 3.3 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -60 dB vs first 0.25 s -19 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre a_grave_soul_now_run --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav a-grave-soul-now-run/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

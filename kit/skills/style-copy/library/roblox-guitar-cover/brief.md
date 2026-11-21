# Style brief: roblox-guitar-cover

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **165.23 BPM** (could also feel like 330.5, 82.6: ask which feels right), 4/4, swing 0.007 |
| key / mode | **G# minor** (relative B major) |
| loudness | -14.5 LUFS integrated, loudness range 4.4 LU, true peak -2.4 dB, crest 14.45 dB |
| brightness | spectral centroid 2673.5 Hz, 85% rolloff 1916.5 Hz, flatness 0.6085, 3-8 kHz vs 0.2-3 kHz -9.1 dB |
| balance (dB re full scale) | sub -14.9, bass -3.4, low-mid -12.3, mid -5.1, high-mid -8.8, air -18.6 |
| stereo | side/mid -6.43 dB, L/R correlation 0.629; by band {'low': 0.92, 'mid': 0.52, 'high': 0.37} |
| rhythmic density | 4.69 attacks/s = 1.7 per beat; sustain (12 dB fall) 185.0 ms |

## 2. Arrangement shape
Sections: intro 17 bars (energy 0.28), build 7 bars (energy 0.6), drop 25 bars (energy 0.93), drop 8 bars (energy 1.0), break 5 bars (energy 0.0), verse 4 bars (energy 0.69). Drops at [35.76] s. Energy per bar (dB below the loudest bar): `[-19.9, -10.4, -9.8, -7.3, -2.4, -5.1, -2.2, -1.5, -2.0, -1.8, -1.8, -1.4, -1.4, -1.0, -0.9, -1.5, -1.5, -2.7, -3.2, -2.5, -2.5, -2.9, -2.7, -1.9, -1.1, -0.6, -0.8, -0.6, -1.2, -1.2, -1.1, -1.0, -0.8, -0.8, -1.4, -1.1, -0.9, -1.2, -1.2, -0.8, -1.5, -0.8, -0.6, -0.6, -0.7, -0.9, -0.6, -0.4, -0.2, -0.2, -0.3, -0.8, -0.5, -0.9, -0.4, -0.5, -0.8, -6.7, -7.0, -6.6, -2.9, -5.5, 0.0, -1.3, -5.5, -2.0]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.86, 0.14, 0.74, 0.23, 1.0, 0.14, 0.66, 0.14, 0.94, 0.4, 0.89, 0.43, 0.71, 0.11, 0.54, 0.46]`  (grid confidence 0.64)
Drum hints (full mix, approximate): kick `xoxoxoXoooxox.xx`, snare `X.o.X.o.X.oox.oo`, hat `X.o.x.x.X.x.x.oo`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.67, chord changes per bar 0.76, most-used degrees ['I', 'bVII', 'bVI', 'bII']. Example loop (FLAVOUR ONLY, do not copy): ['IV', 'I', 'bII', 'bVII']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.6085, 3-8k vs 0.2-3k -9.1 dB)
- articulation: mixed (median 12 dB fall 185.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick xoxoxoXoooxox.xx, snare X.o.X.o.X.oox.oo; from a full mix, approximate)

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre roblox_guitar_cover --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav roblox-guitar-cover/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

# Style brief: necrobloxians

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **175.02 BPM** (could also feel like 350.0, 87.5: ask which feels right), 4/4, swing 0.017 |
| key / mode | **A minor** (relative C major) |
| loudness | -11.5 LUFS integrated, loudness range 2.4 LU, true peak 0.4 dB, crest 15.16 dB |
| brightness | spectral centroid 2995.5 Hz, 85% rolloff 2325.6 Hz, flatness 0.6905, 3-8 kHz vs 0.2-3 kHz -4.9 dB |
| balance (dB re full scale) | sub -9.2, bass -3.3, low-mid -11.5, mid -8.1, high-mid -8.2, air -16.0 |
| stereo | side/mid -8.11 dB, L/R correlation 0.733; by band {'low': 0.86, 'mid': 0.64, 'high': 0.57} |
| rhythmic density | 6.52 attacks/s = 2.24 per beat; sustain (12 dB fall) 95.0 ms |

## 2. Arrangement shape
Sections: intro 2 bars (energy 0.0), break 12 bars (energy 0.35), drop 16 bars (energy 1.0), drop 8 bars (energy 0.89), outro 17 bars (energy 0.24). Drops at [19.947] s. Energy per bar (dB below the loudest bar): `[-5.0, -4.7, -2.8, -2.8, -2.7, -3.4, -3.6, -2.2, -1.7, -1.7, -2.4, -2.8, -4.8, -8.7, -0.5, -0.4, -0.8, -0.4, -0.3, 0.0, -0.4, -0.8, -0.4, -0.5, -0.4, -0.1, -0.1, -0.2, -0.1, -0.8, -0.8, -1.3, -1.4, -1.6, -0.3, -0.7, -0.7, -0.6, -1.9, -2.4, -1.4, -1.5, -1.5, -3.4, -1.1, -1.2, -1.0, -1.5, -0.8, -0.6, -0.5, -0.8, -2.6, -10.8, -31.9]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.77, 0.5, 0.69, 0.38, 1.0, 0.35, 0.88, 0.38, 0.58, 0.23, 0.92, 0.62, 0.88, 0.58, 0.88, 0.31]`  (grid confidence 0.52)
Drum hints (full mix, approximate): kick `Xo.xx.Xxo.xxo.x.`, snare `X.ooX.Xox.x.X.x.`, hat `X.xxx.X.x.X.X.X.`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.02, third share 0.53, chord changes per bar 0.11, most-used degrees ['I', 'V', 'II', 'IV']. Example loop (FLAVOUR ONLY, do not copy): ['II', 'II', 'I', 'I']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.6905, 3-8k vs 0.2-3k -4.9 dB)
- articulation: muted / staccato (median 12 dB fall 95.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick Xo.xx.Xxo.xxo.x., snare X.ooX.Xox.x.X.x.; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 175.0, it behaves like **175.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B C D** = build 4 bars (7.3%), build 10 bars (18.2%), drop 30 bars (54.5%), outro 11 bars (20.0%). Chord cycle: none found bars.
- DROP at 4.6% (bar 3): bass +3.5 dB, brightness +558 Hz
- DROP at 26.2% (bar 15): full impact (+8.9 dB, one-shot 0.84 s) -> bass +6.2 dB, brightness -331 Hz
- DROP at 80.2% (bar 45): full impact (+12.5 dB, level stays up) -> bass +0.9 dB, brightness -119 Hz
- Hard hits 2.4/min (types {'full impact': 3, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 1.0.
Layers at section boundaries (what to add or take away there):
- bar 5 (build): no big change
- bar 15 (drop): +sub 14dB, +bass 6dB, +lowmid 10dB, +mid 6dB, +highmid 4dB, +air 4dB
- bar 45 (outro): +lowmid 4dB
Loop-readiness of the reference file: NOT ready (ends with 1.8 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -78 dB vs first 0.25 s -15 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre necrobloxians --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav necrobloxians/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

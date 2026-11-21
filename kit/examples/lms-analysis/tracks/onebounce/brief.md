# Style brief: onebounce

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **96.5 BPM** (could also feel like 193.0, 48.3: ask which feels right), 4/4, swing 0.006 |
| key / mode | **B minor** (relative D major) |
| loudness | -7.6 LUFS integrated, loudness range 4.5 LU, true peak 0.8 dB, crest 10.8 dB |
| brightness | spectral centroid 2703.3 Hz, 85% rolloff 1593.5 Hz, flatness 0.6233, 3-8 kHz vs 0.2-3 kHz -7.3 dB |
| balance (dB re full scale) | sub -9.2, bass -3.5, low-mid -10.2, mid -6.8, high-mid -10.0, air -16.9 |
| stereo | side/mid -12.76 dB, L/R correlation 0.899; by band {'low': 0.98, 'mid': 0.86, 'high': 0.71} |
| rhythmic density | 6.93 attacks/s = 4.31 per beat; sustain (12 dB fall) 150.0 ms |

## 2. Arrangement shape
Sections: intro 3 bars (energy 0.0), drop 13 bars (energy 0.97), drop 12 bars (energy 1.0), verse 2 bars (energy 0.68). Drops at [8.408] s. Energy per bar (dB below the loudest bar): `[-5.2, -5.1, -5.1, -3.1, -1.0, -1.0, -0.9, -2.0, -0.4, -0.5, -0.3, -0.3, -0.2, -0.6, -0.3, -0.8, -1.4, -1.2, -1.2, -1.0, -1.1, -0.9, -1.0, -0.2, 0.0, -0.0, -0.1, -0.5, -1.7, -2.5]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.86, 0.74, 0.83, 0.37, 0.89, 0.86, 0.8, 0.8, 0.86, 0.77, 1.0, 0.66, 0.94, 0.74, 0.86, 0.69]`  (grid confidence 0.83)
Drum hints (full mix, approximate): kick `Xox.x.xxxxx.XoX.`, snare `Xox.xxxxxoX.Xoxo`, hat `XxX.XxxxXoXoXoxx`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.9, chord changes per bar 0.77, most-used degrees ['V', '#IV', 'bVI', 'I']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'V', 'V', 'V']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.6233, 3-8k vs 0.2-3k -7.3 dB)
- articulation: mixed (median 12 dB fall 150.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick Xox.x.xxxxx.XoX., snare Xox.xxxxxoX.Xoxo; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 96.5, it behaves like **193.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B** = build 3 bars (9.7%), drop 28 bars (90.3%). Chord cycle: 4 bars.
- DROP at 10.9% (bar 4): bass +4.2 dB, brightness -131 Hz
- Hard hits 0.0/min (types {'full impact': 0, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid None, on beat 1 None.
Layers at section boundaries (what to add or take away there):
- bar 4 (drop): +bass 5dB
Loop-readiness of the reference file: NOT ready (ends with 1.3 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -63 dB vs first 0.25 s -15 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre onebounce --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav onebounce/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

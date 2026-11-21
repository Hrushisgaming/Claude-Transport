# Style brief: eternal-hope-old

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **139.98 BPM** (could also feel like 280.0, 70.0: ask which feels right), 4/4, swing 0.001 |
| key / mode | **B minor** (relative D major) |
| loudness | -15.5 LUFS integrated, loudness range 2.2 LU, true peak -3.7 dB, crest 12.61 dB |
| brightness | spectral centroid 2162.1 Hz, 85% rolloff 646.0 Hz, flatness 0.4967, 3-8 kHz vs 0.2-3 kHz -9.4 dB |
| balance (dB re full scale) | sub -10.6, bass -2.8, low-mid -7.6, mid -9.7, high-mid -12.1, air -22.4 |
| stereo | side/mid -7.1 dB, L/R correlation 0.669; by band {'low': 0.79, 'mid': 0.59, 'high': 0.37} |
| rhythmic density | 5.78 attacks/s = 2.48 per beat; sustain (12 dB fall) 115.0 ms |

## 2. Arrangement shape
Sections: intro 9 bars (energy 0.54), drop 8 bars (energy 1.0), drop 8 bars (energy 0.8), verse 7 bars (energy 0.46), outro 11 bars (energy 0.0). Drops at [15.501] s. Energy per bar (dB below the loudest bar): `[-5.6, -0.8, -2.6, -1.8, -1.8, -1.0, -2.6, -1.9, -1.2, 0.0, -1.4, -1.3, -1.1, -0.3, -1.3, -1.4, -1.4, -1.2, -2.7, -2.9, -2.5, -0.0, -0.9, -1.1, -0.7, -0.9, -3.7, -3.4, -3.2, -0.7, -2.4, -2.2, -2.6, -0.1, -1.1, -1.2, -1.1, -0.4, -1.2, -1.2, -0.9, -4.5, -24.2]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.98, 0.02, 0.93, 0.76, 0.95, 0.02, 1.0, 0.22, 0.95, 0.59, 0.93, 0.2, 0.95, 0.17, 0.98, 0.37]`  (grid confidence 0.96)
Drum hints (full mix, approximate): kick `XXxXooXxXxxxXxxx`, snare `X.oox.X.xoo.x.x.`, hat `X.o.x.X.ooo.x.x.`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.93, chord changes per bar 0.53, most-used degrees ['V', 'bVII', 'I', 'bIII']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'I', 'V', 'V']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: moderate (flatness 0.4967, 3-8k vs 0.2-3k -9.4 dB)
- articulation: muted / staccato (median 12 dB fall 115.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick XXxXooXxXxxxXxxx, snare X.oox.X.xoo.x.x.; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 140.0, it behaves like **140.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): tension / mid-intensity round music.
Form: **A B** = drop 21 bars (48.8%), drop 22 bars (51.2%). Chord cycle: 4 bars.
- DROP at 48.9% (bar 22): bass +2.3 dB, brightness -328 Hz
- Hard hits 0.8/min (types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 1.0.
Layers at section boundaries (what to add or take away there):
- bar 22 (drop): +sub 4dB, +lowmid 4dB
Loop-readiness of the reference file: NOT ready (ends with 2.2 s of fade/silence: a looping Sound would play that gap every cycle; level jump at the seam: last 0.25 s -79 dB vs first 0.25 s -22 dB). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre eternal_hope_old --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav eternal-hope-old/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

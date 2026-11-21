# Style brief: lmsy2k

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **100.0 BPM** (could also feel like 200.0, 50.0: ask which feels right), 4/4, swing 0.009 |
| key / mode | **F# minor** (relative A major) |
| loudness | -11.3 LUFS integrated, loudness range 4.4 LU, true peak -0.2 dB, crest 12.28 dB |
| brightness | spectral centroid 2480.9 Hz, 85% rolloff 409.1 Hz, flatness 0.5791, 3-8 kHz vs 0.2-3 kHz -7.3 dB |
| balance (dB re full scale) | sub -5.8, bass -2.8, low-mid -12.1, mid -11.1, high-mid -13.0, air -20.1 |
| stereo | side/mid -12.93 dB, L/R correlation 0.903; by band {'low': 1.0, 'mid': 0.73, 'high': 0.66} |
| rhythmic density | 6.77 attacks/s = 4.06 per beat; sustain (12 dB fall) 90.0 ms |

## 2. Arrangement shape
Sections: intro 2 bars (energy 0.0), drop 10 bars (energy 0.97), drop 8 bars (energy 1.0), drop 8 bars (energy 0.9), outro 4 bars (energy 0.53). Drops at [4.899] s. Energy per bar (dB below the loudest bar): `[-16.5, -17.6, 0.0, -0.4, -4.0, -4.1, -3.9, -4.1, -3.9, -4.0, -3.8, -4.0, -2.7, -2.6, -2.7, -2.7, -2.7, -2.7, -2.8, -3.4, -4.1, -4.1, -3.9, -4.1, -4.5, -4.4, -4.4, -4.4, -8.9, -10.8, -8.9, -9.3]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[0.94, 0.55, 0.97, 0.61, 0.85, 0.79, 0.79, 0.58, 1.0, 0.7, 0.82, 0.91, 0.82, 0.73, 0.94, 0.88]`  (grid confidence 0.8)
Drum hints (full mix, approximate): kick `XoXxXxXoXoxxxoxx`, snare `xoxooxxoxoxooxXo`, hat `xxoxxxoXoxxXxXxX`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.0, third share 0.94, chord changes per bar 0.75, most-used degrees ['I', 'bIII', 'bVI', 'bVII']. Example loop (FLAVOUR ONLY, do not copy): ['I', 'II', 'I', 'bVII']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: high (flatness 0.5791, 3-8k vs 0.2-3k -7.3 dB)
- articulation: muted / staccato (median 12 dB fall 90.0 ms)
- chords: full chords with thirds
- drums: probably yes (kick XoXxXxXoXoxxxoxx, snare xoxooxxoxoxooxXo; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 100.0, it behaves like **200.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A B** = intro 2 bars (6.1%), verse 31 bars (93.9%). Chord cycle: 4 bars.
- DROP at 6.2% (bar 3): full impact (+10.0 dB, level stays up) -> bass +29.8 dB, brightness -1544 Hz
- Hard hits 0.8/min (types {'full impact': 1, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 1.0.
Layers at section boundaries (what to add or take away there):
- bar 3 (verse): +sub 43dB, +bass 30dB, +lowmid 10dB, +mid 6dB, +highmid 8dB, +air 8dB
Loop-readiness of the reference file: NOT ready (ends with 1.8 s of fade/silence: a looping Sound would play that gap every cycle; starts with 4.9 s of quiet before the music). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre lmsy2k --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav lmsy2k/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

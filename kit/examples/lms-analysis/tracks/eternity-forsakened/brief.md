# Style brief: eternity-forsakened

Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.

## 1. Numbers to hit (check them with `af.py compare`)
| what | target |
|---|---|
| tempo | **179.98 BPM** (could also feel like 360.0, 90.0: ask which feels right), 4/4, swing 0.001 |
| key / mode | **A minor** (relative C major) |
| loudness | -12.9 LUFS integrated, loudness range 7.7 LU, true peak 0.1 dB, crest 16.31 dB |
| brightness | spectral centroid 2193.8 Hz, 85% rolloff 1055.1 Hz, flatness 0.4818, 3-8 kHz vs 0.2-3 kHz -9.0 dB |
| balance (dB re full scale) | sub -15.4, bass -1.9, low-mid -10.9, mid -7.9, high-mid -11.3, air -23.5 |
| stereo | side/mid -5.61 dB, L/R correlation 0.569; by band {'low': 0.78, 'mid': 0.41, 'high': 0.4} |
| rhythmic density | 5.93 attacks/s = 1.98 per beat; sustain (12 dB fall) 130.0 ms |

## 2. Arrangement shape
Sections: intro 7 bars (energy 0.32), build 8 bars (energy 0.69), drop 16 bars (energy 1.0), break 16 bars (energy 0.0), drop 8 bars (energy 0.84). Drops at [21.31, 63.981] s. Energy per bar (dB below the loudest bar): `[-7.2, -6.5, -4.9, -7.5, -5.5, -6.7, -5.7, -3.5, -2.6, -2.2, -4.0, -3.5, -3.3, -2.1, -5.4, -1.1, -0.9, -0.3, -1.9, -1.6, -0.8, -0.5, -1.6, -1.1, -0.3, 0.0, -1.1, -0.8, -0.4, -0.0, -1.1, -6.0, -13.1, -7.4, -15.0, -5.4, -13.4, -6.3, -14.3, -5.2, -9.5, -5.8, -9.5, -5.3, -9.8, -3.8, -11.5, -1.5, -1.2, -0.7, -2.4, -1.4, -1.0, -1.3, -7.9]`.
Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.

## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)
`[1.0, 0.16, 0.77, 0.16, 0.52, 0.39, 0.94, 0.23, 0.68, 0.58, 0.81, 0.1, 0.61, 0.35, 1.0, 0.06]`  (grid confidence 0.58)
Drum hints (full mix, approximate): kick `X.o.x.Xoo.X.xox.`, snare `X.o.o.x.x.x.x.x.`, hat `X.o.o.x.x.x.x.x.`.

## 4. Harmony (reduced on purpose)
Power-chord share 0.2, third share 0.42, chord changes per bar 0.64, most-used degrees ['V', 'I', 'bVI', 'IV']. Example loop (FLAVOUR ONLY, do not copy): ['V', 'bVI', 'V', 'I']. Write a NEW progression in the same mode.

## 5. Guesses about the sound (confirm if it matters)
- distortion: moderate (flatness 0.4818, 3-8k vs 0.2-3k -9.0 dB)
- articulation: muted / staccato (median 12 dB fall 130.0 ms)
- chords: mixed
- drums: probably yes (kick X.o.x.Xoo.X.xox., snare X.o.o.x.x.x.x.x.; from a full mix, approximate)

## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)
Tempo feel: analyzer says 180.0, it behaves like **180.0 BPM** (high confidence; ask which they tap). Role guess (heuristic): chase / last-man-standing (fast, driving).
Form: **A A' B C C' D D' D' C'** = build 2 bars (3.6%), build 5 bars (9.1%), build 6 bars (10.9%), drop 10 bars (18.2%), drop 8 bars (14.5%), break 4 bars (7.3%), break 4 bars (7.3%), build 8 bars (14.5%), drop 8 bars (14.5%). Chord cycle: 16 bars.
- DROP at 5.3% (bar 3): full impact (+8.2 dB, one-shot 0.14 s) -> bass +0.8 dB, brightness +595 Hz
- DROP at 14.2% (bar 8): bass +4.0 dB, brightness -613 Hz
- DROP at 28.4% (bar 16): full impact (+10.7 dB, level stays up) -> bass +1.8 dB, brightness +201 Hz
- DROP at 64.0% (bar 36): full impact (+11.4 dB, one-shot 0.46 s) -> bass +1.5 dB, brightness +218 Hz
- DROP at 71.1% (bar 40): full impact (+12.7 dB, one-shot 1.78 s) -> bass +1.1 dB, brightness +304 Hz
- DROP at 85.3% (bar 48): full impact (+15.9 dB, level stays up) -> bass +4.2 dB, brightness +463 Hz
- Hard hits 5.6/min (types {'full impact': 7, 'sub/kick impact': 0, 'crash/high burst': 0, 'accent': 0}), stops 0.0/min, hits on the 16th grid 1.0, on beat 1 1.0.
Layers at section boundaries (what to add or take away there):
- bar 3 (build): +sub 3dB
- bar 8 (build): +sub 7dB, +bass 4dB
- bar 14 (drop): +highmid 4dB
- bar 24 (drop): no big change
- bar 32 (break): -sub 8dB, -bass 10dB, -lowmid 5dB, -mid 9dB, -highmid 9dB, -air 3dB
- bar 36 (break): +mid 4dB, +highmid 3dB
- bar 40 (build): +bass 3dB, +mid 5dB, +highmid 5dB, +air 5dB
- bar 48 (drop): +sub 13dB, +bass 6dB, +lowmid 4dB, +mid 7dB, +highmid 8dB, +air 8dB
Loop-readiness of the reference file: NOT ready (level jump at the seam: last 0.25 s -45 dB vs first 0.25 s -19 dB; length is 55.27 bars from the first downbeat (+364 ms from a whole bar): a loop would drift off the grid). YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.
Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.

## 6. How to build it with audio-forge
1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.
2. `af.py compose --genre eternity_forsakened --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).
3. `af.py compare cand.wav eternity-forsakened/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.
4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.

## 7. Do not
- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.
- Do not claim it 'sounds the same'. Say which measured numbers match.

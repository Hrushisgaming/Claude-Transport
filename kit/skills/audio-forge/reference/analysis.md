# Reference analysis

`python3 af.py analyze ref.mp3 --out ref.profile.json` writes `audio-forge/profile@1`. Needs only numpy, scipy, ffmpeg.

| field | meaning / trust |
|---|---|
| `tempo.bpm`, `grid_fit`, `steady` | grid-fitted to ~0.02 BPM on steady music. `steady=false` -> live/drifting: beats come from a tracker. |
| `tempo.ambiguous`, `alt_octaves` | half/double-time candidates are both plausible. **Ask the user**, re-run with `--bpm-range LO HI`. `octave_adjusted` says if the tool already doubled. |
| `meter` | 4/4 vs 3/4 and the downbeat phase, from accent contrast (medium confidence). |
| `key.best`, `key.relative`, `alternatives` | Krumhansl key finding on harmonic content. Relative major/minor and modes (dorian, phrygian) collapse onto a parent key. |
| `chords_per_bar` | triad/power-chord labels per bar with a match score; progression is derived from the confident bars. |
| `pattern.kick/snare/hat` | 16-step grooves (`X x o .`). From the full mix = approximate; from demucs stems = good. |
| `swing` | 0 straight, ~0.33 triplet feel. |
| `loudness`, `dynamics`, `stereo`, `bands_db`, `spectral` | LUFS/LRA/true peak (ffmpeg ebur128), crest factor, side/mid, six band balance, centroid/rolloff/flatness. |
| `sections`, `drops`, `energy_per_beat` | novelty-based structure with energy 0-1 and labels (intro/build/drop/break/verse/outro); drops = energy jumps. |
| `genre_guess` | heuristic ranking from tempo, mode, groove similarity, density, spectrum. Present as "sounds closest to ...", confirm. |

## Optional extra tools (ask first)
- **demucs** (~1 GB): `python3 af.py separate ref.mp3 --out stems/` then `analyze ref.mp3 --stems stems/` -> drum pattern from the isolated drum stem. You can also inspect `bass.wav` / `other.wav` / `vocals.wav` separately.
- **librosa** (~250 MB): `librosa_tempo` cross-check appears in the profile.

## Remaking
`remake.py` maps the profile to: genre, bpm, key, major/minor scale, bars (from length), swing, intensity (from onset density), kick/snare/hat patterns, chord progression as scale degrees, section plan. Then `compose.py --profile` renders it. The melody is newly generated, never copied. To push further: `--genre X` to override the guess, `--override` for instruments, `--seed` for variations, `--intensity`, `--dynamics`.

## Validation the tool ran on itself
Round trip on 13 generated tracks (known tempo/key/genre, fresh seeds): tempo within 1 BPM on 12/13 (the miss: a half-time reading of 174 BPM dnb, flagged `ambiguous`), key = true / relative / mode-parent on 9/13 (weak on power-chord rock/metal, modal tunes), genre top-1 on 8/13 (family right on most others). These are clean synthetic mixes: real recordings are harder, expect lower accuracy on live, rubato, or dense music.

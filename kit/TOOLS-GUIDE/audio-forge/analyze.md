# audio-forge — `analyze`

Listen to a reference track and write a style profile (JSON). Everything is measured with numpy + scipy + ffmpeg; nothing is copied. If `librosa` is installed it is used to cross-check tempo/beats. If `--stems` points at a demucs output (`drums.wav bass.wav other.wav vocals.wav`), the drum pattern, bass notes and melody range are measured from the isolated stems — much more accurate than the full mix.

## Exact command

```
python3 af.py analyze AUDIO [--out PROFILE.json] [--max-seconds N] [--start S]
    [--engine auto|builtin|librosa] [--stems STEMS_DIR]
    [--bpm-range LO HI] [--brief]
```

### Flags

| Flag | Meaning |
|---|---|
| `AUDIO` | the reference file (mp3/wav/ogg/flac/m4a/…; ffmpeg decodes it). |
| `--out PROFILE.json` | write the full profile here. |
| `--max-seconds N` | only analyze the first N seconds (speeds up long files). |
| `--start S` | start analyzing at S seconds. |
| `--engine` | tempo/beat engine: `auto` (default), `builtin`, `librosa`. |
| `--stems` | demucs output dir for stem-based measurement. |
| `--bpm-range LO HI` | force the tempo octave, e.g. `150 190` (useful when the analyzer is ambiguous between half and double time). |
| `--brief` | print only the one-line summary (tempo, key, meter, loudness, sections, drops). |

## Outputs

`profile.json` holds:
- tempo (+candidates, steadiness)
- beats / downbeats / meter
- key + mode (+runner-ups)
- per-bar chords
- 16-step kick/snare/hat patterns
- swing, loudness (LUFS), dynamics, stereo width
- band energy balance, brightness, percussive/harmonic split
- structure (sections with energy), drop candidates
- per-beat energy curve
- genre guess (heuristic, labelled as such)

## Step-by-step tutorial

1. Analyze the reference:
   ```
   af.py analyze ref.mp3 --out ref.profile.json
   ```
2. Read the summary line (`--brief` or the top of the JSON). Confirm the tempo/key/genre guess with the person — key detection gave the true key, its relative, or the mode's parent key on most synthetic tests but is weakest on power-chord rock/metal and modal tunes, so treat it as a hint.
3. If `tempo.ambiguous` is true, ask which feels right ("87 or 174 BPM?") and re-run with `--bpm-range LO HI`.
4. Use the profile for `remake` (turn it into compose parameters) or for `compose --profile` (derive genre/bpm/key/scale/intensity).
5. Re-analyze your remake and report how close tempo/key/groove/energy arc are. Change ONE knob per round (`--override`, `--intensity`, `--genre`).

## Honesty

Tempo was within 1 BPM on 12 of 13 synthetic test tracks (the miss was a half-time reading of a 174 BPM drum-and-bass track, which the tool flags as ambiguous). Full-mix groove detection is approximate; stems from demucs are much better. The genre guess is a heuristic — right family most of the time, not always the exact genre. Nobody has listened to the reference or the profile's implications.

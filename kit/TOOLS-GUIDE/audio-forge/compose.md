# audio-forge — `compose`

Generate an original piece of music from code. No samples, no downloads, nothing uploaded. Every genre is a data spec (rhythm strings, instruments, mix, sections) rendered by the V2 synth engine (`forge/dsp.py` + `forge/instruments.py` + `forge/song.py`) using only numpy and scipy.

## Exact command

```
python3 af.py compose --genre GENRE [--bars BARS | --duration SECONDS] \
    [--bpm BPM] [--key KEY] [--scale SCALE] [--seed SEED] \
    [--intensity 0-1] [--swing SWING] [--dynamics 0-1.5] \
    [--profile PROFILE.json] [--override 'JSON' | override.json] \
    [--plan '[["intro",0.2],["drop",0.8]]'] \
    [--stems STEMS_DIR] [--midi] [--no-master] [--out OUT.wav] [--list]
```

### Flags

| Flag | Meaning |
|---|---|
| `--genre GENRE` | any genre from `--list` (aliases work: `forsaken`, `8bit`, `lo-fi`). Required unless `--list` or `--profile`. |
| `--bars BARS` | number of 16-step bars. Defaults to a genre-sensible length. |
| `--duration SECONDS` | target length in seconds (overrides --bars; needs bpm known or random). |
| `--bpm BPM` | tempo. Picked from the genre's BPM window if omitted. |
| `--key KEY` | C C# D … B. Random from the genre's scale list if omitted. |
| `--scale SCALE` | major minor dorian phrygian lydian mixolydian harmonic_minor pent_minor pent_major blues locrian |
| `--seed SEED` | variation seed — change it for a different take of the same genre/key/tempo. |
| `--intensity 0-1` | sparser vs denser (default 0.75). |
| `--dynamics 0-1.5` | loudness arc: 0 flat, 1 natural (quiet intro → full drop), 1.5 dramatic. |
| `--profile PROFILE.json` | derive genre/bpm/key/scale/intensity from an `analyze.py` profile. |
| `--override OVERRIDE` | JSON string **or file** deep-merged into the genre spec (change instruments, rhythms, drive, mix gains, …). |
| `--plan PLAN` | JSON list of `[section, fraction]` e.g. `'[["intro",0.2],["drop",0.8]]'` — section proportions always sum to the bar count. |
| `--stems STEMS_DIR` | also write one WAV per instrument track into this folder. |
| `--midi` | also write `<out>.mid` (open in any DAW). |
| `--no-master` | skip the light master chain (keeps crest for further processing). |
| `--out OUT.wav` | output path (16-bit stereo 44.1 kHz WAV). |
| `--list` | print every genre + alias and exit. |

## Outputs

- `<out>.wav` — 16-bit stereo 44.1 kHz, peak-limited, mastered to keep crest (light `compress(-16,1.55)` + ceiling/normalize −1.5 dBFS).
- `<out>.beatmap.json` — `audio-forge/beatmap@1`: `{schema, bpm, beats_per_bar, beats[], downbeats[], sections[{name,start,end}], drops[], energy_per_beat[], duration}`. Ready for the editor bridge (`af.py bridge …`).
- `<out>.mid` (only with `--midi`).
- `<stems>/<track>.wav` (only with `--stems`).

## Step-by-step tutorial

1. Pick a genre: `af.py compose --list`. For a game chase bed try `horror_chase` (aliases `forsaken`, `chase`, `roblox`, `horror`); for a vlog bed try `warm_piano`; for a trailer try `epic_trailer`.
2. Compose a first take:
   ```
   af.py compose --genre horror_chase --bars 24 --bpm 176 --key A --scale minor --seed 1 --out mybed.wav
   ```
3. Check what you made (always):
   ```
   af.py analyze mybed.wav --brief
   ```
   Report tempo/key/length in plain words. Do **not** claim it "sounds good" — you haven't heard it. Hand the file to the person and let them listen.
4. Want a different take? Change only `--seed`. Want it sparser or denser? Change `--intensity`. Want a different section shape? Use `--plan`.
5. Want to match a reference's style? Run `af.py analyze ref.mp3 --out profile.json`, then `af.py compose --profile profile.json --out remake.wav` (this copies tempo/key/groove/structure, never the melody).
6. For a Roblox set, all tracks should share one key and one BPM so they crossfade on bar lines — see `roblox-ost/build.md`.

## Honesty

`compose` synthesises from code. It makes convincing genre-appropriate demos, game loops, beds and jingles; it will not pass for a recorded band or human singer. Genre presets are starting points chosen by reasoning, not tuned on real edits. Nobody has listened to the output.

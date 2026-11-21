# audio-forge — `audition`

Hear the instrument library: a timestamped showcase WAV plus a mini-mix, so you can compare the V2 voices and decide which to keep. Nobody has listened to these sounds yet — play the showcase and tick the names that are wrong.

## Exact command

```
af.py audition [--out DIR] [--inst KEYS] [--all]
    [--genre GENRE] [--bpm BPM] [--bars BARS] [--seed SEED] [--no-mix]
```

### Flags

| Flag | Meaning |
|---|---|
| `--out DIR` | output folder (default `audition/`). |
| `--inst KEYS` | comma-separated instrument keys (default: the standard voice set). |
| `--all` | every instrument in the library. |
| `--genre GENRE` | genre for the mini-mix (default `horror_chase`). |
| `--bpm BPM` | mini-mix tempo (default 175). |
| `--bars BARS` | mini-mix length (default 8). |
| `--seed SEED` | mini-mix variation seed (default 0). |
| `--no-mix` | showcase only, no mini-mix. |

## Outputs (in `--out`)

| File | What it is |
|---|---|
| `showcase.wav` | every requested instrument, one after another, same peak volume, for comparison |
| `showcase.md` | timestamp guide: what starts when and which notes (MIDI) each voice played |
| `showcase.json` | the same guide as JSON (schema `audio-forge/audition@1`) |
| `minimix.wav` | a short arrangement in one genre at one tempo (V2 voices in context) |
| `minimix.json` | mini-mix beatmap / section summary |

## Default voice set

`piano_m1`, `piano`, `organ`, `organ_rock`, `organ_pipe`, `ep`, `bell`, `bell_tubular`, `clock_bell`, `guitar`, `guitar_mute`, `guitar_elec`, `guitar_pluck`, `acid_303`, `saw_bass`, `sine_sub`, `y2k_bass`, `pulsing_bass`, `chip_lead`, `lead_saw`, `stab`, `strings`, `pad`, `choir`, `brass`, `marimba`, `showtime_sax`, `rave_stab`, `orch_hit`, `clock_tick`, `heartbeat` — plus all legacy keys (`sine_sub`, `saw_bass`, `reese`, `pluck`, `lead_saw`, …).

## Step-by-step tutorial

1. Run the default showcase:
   ```
   af.py audition --out audition/
   ```
2. Open `audition/showcase.md` — it lists start/end seconds and the MIDI notes for each voice. Play `showcase.wav` and note which voices are wrong or weak.
3. Check specific voices:
   ```
   af.py audition --inst piano_m1,organ_rock,bell_tubular,acid_303,guitar --out audition2/
   ```
4. Or every voice at once:
   ```
   af.py audition --all --out allvoices/
   ```
5. Hear the V2 voices in a genre context:
   ```
   af.py audition --genre horror_chase --bpm 175 --bars 8 --out audition3/
   ```
   This writes `minimix.wav` + `minimix.json` so you hear the instruments in an actual arrangement.

## Honesty

Every voice is normalised to the same peak so you can compare them — that is not a mix. `audition` renders; it does not judge. Report what each voice does (pitch, attack, decay), not whether it "sounds good".

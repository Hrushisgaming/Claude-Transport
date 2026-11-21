# roblox-ost — `af.py ost build`

Build one Roblox game soundtrack set with **one key and one BPM** for every state, so states crossfade on bar lines and stems layer cleanly. Every loop is made seam-safe: the render's decay tail is folded back onto the start, the loop is cut to a whole number of bars, then loudness-matched (linear gain + peak limit, no fades).

States: **lobby** (loop) → **tension** (loop) → **chase** (loop, with stems) → **lms_intro** (plays once) + **lms** (loop) → **win** (stinger) → **lose** (stinger).

## Exact command

```
af.py ost build --out OST_DIR [--key A] [--scale minor] [--bpm 178]
    [--family STYLES/LMS-FAMILY] [--lms-bars 48] [--format ogg|wav|mp3|flac]
    [--target-lufs -14] [--quick] [--seed 1] [--strict]
```

### Flags

| Flag | Meaning |
|---|---|
| `--out OST_DIR` | where the set is written (default `ost/`). |
| `--key` / `--scale` / `--bpm` | one key/tempo for the whole set (derived from `--family` if given; defaults A minor / 178 BPM). |
| `--family` | a style family folder (with `dna.json`) to shape the lms plan, tempo and key. |
| `--lms-bars` | length of the lms loop in bars (default 48, snapped to a multiple of 4 with `--quick`). |
| `--format` | output codec (default `ogg`; use `wav` for lossless / loop checking). |
| `--target-lufs` | loudness target (default −14 LUFS; music bed, leaves headroom for SFX — not a Roblox rule). |
| `--quick` | shorter bars (half) for fast iteration. |
| `--seed` | variation seed. |
| `--strict` | exit non-zero if any loop fails the seam/headroom/mono-sub checks. |

## Outputs (in `--out`)

- `lobby.wav`, `tension.wav`, `chase.wav`, `lms_intro.wav`, `lms.wav`, `win.wav`, `lose.wav` (one key, one BPM, whole-bar loops)
- `chase_stems/` — one WAV per stem, same length, start together (play as synchronized Sounds and fade layers with danger level)
- `roblox_manifest.md` — what plays when, loop yes/no, bars, LUFS, per-file check results
- `MusicDirector.luau` — the in-game script (copied from `templates/`; **not run in Roblox Studio here**)

## Roblox upload limits used by `ost check`

mp3/ogg/wav/flac, single track, < 20 MB, ≤ 7 minutes, ≤ 48 kHz. Re-check on the Creator Hub audio page before relying on them. mp3 adds encoder padding (a tiny gap at the loop point); for looping Sounds prefer ogg/flac/wav (verify in Studio).

## Step-by-step tutorial

1. Build a fast V2 set:
   ```
   af.py ost build --out myost/ --format wav --strict --quick --bpm 178 --key A --scale minor --seed 1
   ```
2. Every loop should print `OK` in the manifest table. With `--strict`, the build exits non-zero if any loop fails.
3. Read `myost/roblox_manifest.md` — it states the checks per file and reminds you: **nobody has listened; audition every file.**
4. Upload each file at create.roblox.com (Creator Hub > Assets > Audio). New uploads are private until you grant them to your experience. Put the returned asset IDs into the `TRACKS` table in `MusicDirector.luau`.
5. Use `chase_stems/` for adaptive danger-layering: all stems are the same length and start together; play them as synchronized Sounds and fade layers with danger level.

## Honesty

These are original compositions in a genre feel; they are not copies of any game's tracks. Loop checks are objective (seam, whole bars, mono sub, headroom, DC, clipping) — they do not prove the loop is musically good. You have not run this in Roblox Studio; verify in Studio before shipping.

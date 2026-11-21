# audio-forge — `stem_mix`

Mix a folder of WAV stems into one finished mix. Per stem: role detection, EQ carve (mud carve on guitars/pads, presence on leads), mono bass below 140 Hz, kick sidechain, stereo width on guitars/pads. Master: DC removal, glue compression, soft saturation, look-ahead limiter, then loudness matching to `--target-lufs` (measured with ffmpeg ebur128, default −14 LUFS for a game bed).

## Exact command

```
af.py stem_mix STEMS_DIR [--out MIX.wav]
    [--target-lufs -14] [--width 0.012]
    [--sidechain auto|on|off]
    [--reference DNA.json] [--processed-out DIR] [--json]
```

### Flags

| Flag | Meaning |
|---|---|
| `STEMS_DIR` | folder with the stem WAVs (all must share the sample rate). |
| `--out MIX.wav` | finished mix path. |
| `--target-lufs` | loudness target in LUFS (default −14). |
| `--width` | stereo width for guitars/pads (default 0.012). |
| `--sidechain` | `auto` (default), `on`, or `off`. Ducks bass/pads under the kick's onsets. |
| `--reference DNA.json` | use the DNA's loudness/width as the target instead of `--target-lufs`. |
| `--processed-out DIR` | also write the per-stem processed (safety-limited, −1.5 dBFS) stems here. |
| `--json` | print a JSON report to stdout. |

## Processing order (per stem, then master)

1. Role detection from the file name **and** the audio itself: bass / drums / guitar / pad / lead / other.
2. DC removal first (a DC step would ring through the filters).
3. EQ carve: high-pass every melodic stem; 250–450 Hz cut on guitars and pads; bass HP 25 Hz + LP 3.2 kHz; drums HP 28 Hz; lead HP 100 Hz.
4. Mono bass: everything below 160 Hz folded to mono (`song.mono_bass_hz=160.0`).
5. Sidechain: kick onsets (from a kick stem, else the drum stem's low-band onsets) duck bass/pads/guitar/lead per role.
6. Width: guitars/pads widened; low end stays mono.
7. Per-stem safety limiter at −1 dBFS.
8. Master: glue compression (`compress(-16,1.5)`), soft saturation, look-ahead limiter, normalize to ceiling, then loudness match.

## Outputs

- `<out>` — the finished mix WAV.
- `--processed-out/<stem>.wav` — processed stems (if requested).
- Stdout: a per-stem table (role, gain dB, peak dBFS, EQ, sidechain %) plus "target X LUFS, measured Y LUFS".

## Step-by-step tutorial

1. Gather stems in one folder (all same sample rate):
   ```
   ls stems/          # kick.wav snare.wav bass.wav guitar.wav pad.wav lead.wav
   ```
2. Mix to −14 LUFS (game-bed target):
   ```
   af.py stem_mix stems/ --out mix.wav --target-lufs -14 --sidechain auto
   ```
3. To match a style family's loudness/width instead:
   ```
   af.py stem_mix stems/ --out mix.wav --reference styles/lms-family/dna.json
   ```
4. To also keep the processed stems (useful for re-mixing later):
   ```
   af.py stem_mix stems/ --out mix.wav --processed-out stems_processed/ --json
   ```
5. Read the measured LUFS line, then **audition `mix.wav`** — nobody has listened to it, and whether it sounds good is the person's call.

## Honesty

`stem_mix` measures and processes; it does not judge. EQ carve points and sidechain depths are starting points. Always audition the mix before shipping.

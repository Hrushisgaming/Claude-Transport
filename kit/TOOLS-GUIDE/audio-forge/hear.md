# audio-forge — `hear`

Detailed feedback on a track: an **offline** measurement pass (`--local`, nothing leaves the machine, no API key) plus optionally an audio-capable model's opinion (API mode, uploads short clips — asks first).

## Exact command

```
# OFFLINE — recommended, no key, no upload
af.py hear AUDIO --local [--out FEEDBACK_DIR] [--json] [--start S] [--dur D]

# API mode — sends short mono 16 kHz clips (max 60 s each) to NVIDIA;
# asks for confirmation first; pass --yes only after the person agreed
af.py hear AUDIO --question "Is the speech clear over the music?" [--full] [--yes]
af.py hear AUDIO --dry-run                          # show what would be uploaded, send nothing
```

### Flags

| Flag | Meaning |
|---|---|
| `AUDIO` | the track to inspect. |
| `--local` | offline only: rich JSON + Markdown telemetry, no API key, no upload. |
| `--out` | folder for `hear-local.json` / `hear-local.md` (default `hear/<name>/`). |
| `--json` | print the local JSON report to stdout. |
| `--question` | also ask the NVIDIA model (API mode; confirm first). |
| `--full` | API mode: auto-slice a >60 s track into section-aligned windows and merge with local telemetry. |
| `--start` / `--dur` | inspect a window of the track. |
| `--model` / `--base-url` | model and endpoint for API mode. |
| `--max-tokens` | model token budget. |
| `--yes` | confirm the person already agreed to uploading (required in non-interactive API runs). |
| `--dry-run` | show what would be uploaded, send nothing. |

## What `--local` measures (all numpy/scipy/ffmpeg)

Per section and overall:
- frequency balance per band (sub / bass / low-mid / mid / high-mid / air), calibrated so band levels sum to measured RMS
- mud / clash score (200–500 Hz buildup)
- harshness / fizz index (3–8 kHz spikes)
- sub weight
- per-beat punch / crest
- stereo band correlation and phase-cancellation risk
- clipping / DC checks
- timbral archetype guesses: guitar / bell / 303 / chip / piano / breakbeat
- exact `af.py compose --override` suggestions

## Outputs

- `hear-local.json` — schema `audio-forge/hear-local@1`: `{schema, overall_bands_db, sections[{punch_crest_db, stereo, ...}], issues[], archetypes[], override_suggestions[]}`
- `hear-local.md` — the same as a readable report.

## API mode (optional, ask first)

- Slices tracks longer than 60 s using `deep.py` section windows, merges local + API results.
- Needs the person's own NVIDIA key (`~/.config/audio-forge/nvidia.key`, chmod 600, or `NVIDIA_API_KEY` env); never print or echo the key.
- Many hosts (opencode included) do not pass audio files to the model, so this is how an agent gets any audio description at all.
- Report the model's answer as **opinion**, not a measurement: timing and loudness come from `analyze`, and whether music sounds good is the person's call.

## Step-by-step tutorial

1. Run the offline pass on your track:
   ```
   af.py hear mybed.wav --local --out feedback/
   ```
2. Read `feedback/hear-local.md`. Look at `issues` (mud, harshness, clipping, DC, sub correlation) and `archetypes` (what the track most resembles).
3. Apply the exact `compose --override` suggestions (e.g. a lower guitar drive, a different mix gain) and re-render, then re-run `hear --local` to confirm the numbers moved.
4. Only if you want a model's opinion: `af.py hear mybed.wav --question "…"` and wait for the person to confirm before uploading anything. Use `--dry-run` first to see what would be sent.

## Honesty

`--local` numbers are measurements, but whether music **sounds good** is the person's call — never claim it. The model's description (API mode) is an opinion, not a measurement. API mode uploads audio: ask the person first, every project, never silently.

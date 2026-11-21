# audio-forge — `doctor`

Check the machine, install the tiny core (numpy + scipy into a private venv, ~60 MB), and install optional parts **only when asked**. Everything is free and local; no accounts, no API keys.

## Exact command

```
python3 af.py doctor                          # status of every part (installs nothing)
python3 af.py doctor --install core           # numpy + scipy into a private venv. Required. Safe without asking.
python3 af.py doctor --list-optional --json   # optional parts: size, description, exact question to ask
python3 af.py doctor --install kokoro         # one optional part (ids: kokoro piper espeak librosa demucs whisper)
python3 af.py doctor --install whisper --whisper-model base
python3 af.py doctor --capabilities           # JSON a host skill reads to detect audio-forge + what is installed
python3 af.py doctor --selftest               # synthesis + analysis + tts + bridge smoke tests
```

### Flags

| Flag | Meaning |
|---|---|
| `--install ID` | install one part (`core`, `kokoro`, `piper`, `espeak`, `librosa`, `demucs`, `whisper`). `--install core` is required and safe to run without asking; everything else needs the user's yes. |
| `--list-optional` / `--json` | list optional parts with size and the exact question wording. |
| `--capabilities` | machine-readable JSON: what audio-forge provides and which tools are installed — a host skill (e.g. cinematic-edit) reads this to detect audio-forge. |
| `--selftest` | run `af.py selftest`. |
| `--whisper-model` | model size for the whisper install. |

## Rules

- The agent MUST ask the user before installing any optional part (the parts list carries the exact "Do you want [PART]? …" wording).
- Never type or request a password: if `doctor` prints a `sudo` command, show it to the user.
- Files go to `~/.cache/audio-forge` (override with `AUDIO_FORGE_HOME`).
- `af.py` uses the `AUDIO_FORGE_HOME` venv if present, else `sys.executable`; always invoke tests with `<your python>`.

## Outputs

- Status lines (doctor with no flags).
- Optional-parts JSON (`--list-optional --json`).
- Capabilities JSON (`--capabilities`) — tools list and `provides` (music, tts, subtitle_dub, sfx, audio_edit, reference_analysis, beat_sync, midi, stems_export, video_score, voice_cleanup, offline_feedback, adaptive_composition, instrument_audition, stem_mixing, loop_repair).
- Pass/fail (`--selftest`).

## Honesty

Doctor reports what is installed; it does not judge audio. The core venv is required for `af.py` to run (system `python3` lacks numpy).

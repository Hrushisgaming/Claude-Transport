# style-copy — `copy.py`

One entry point for style copying (audio genre, video editing style, animation style). Works with **any model**: it only needs a shell. Copies production style only — never notes, melody, lyrics, footage, characters or text.

```
python3 copy.py <cmd> [args] [--name N] [--kind edit|animation] [--words W] [--text T]
    [--deep DEEP] [--bars 64] [--bpm BPM]
```

## Commands

| Command | What it does | Delegates to |
|---|---|---|
| `doctor` | which skills are installed and ready | (native) |
| `list` | prebuilt styles and your own installed styles | (native) |
| `show NAME` | print a style's brief | (native) |
| `study REF [REF2 …] [--name N]` | measure one reference into `dna.json` + brief; several references blend into a family | `af.py study` / `af.py blend` |
| `install` | install the kit into opencode/Claude Code | (native) |
| `compare CANDIDATE REF_DNA` | score a candidate against a reference DNA or audio file | `af.py compare` |
| `deep REF` | hard points, cuts, risers, drops + anatomy, sections, layers, loop-readiness, bar map, Audacity labels | `af.py deep` |
| `lyrics REF [--words W\|--text T]` | lyric statistics against bars/drops (Whisper optional, asked first) | `af.py lyrics` |
| `plan NAME` | turn a style into a bar-by-bar plan | (native) |
| `adapt REF --out CANDIDATE` | compose → compare → adjust (up to 5 rounds) towards a reference | `af.py adapt` |
| `audition [--out DIR]` | timestamped instrument showcase + mini-mix | `af.py audition` |
| `stem-mix STEMS_DIR --out WAV` | mix a folder of stems into a finished mix | `af.py stem_mix` |
| `loop-doctor FILE [--repair OUT]` | diagnose and repair a music loop | `af.py loop_doctor` |

## How copy.py locates audio-forge

`copy.py` finds `af.py` next to the audio-forge skill folder and runs its commands with the kit's Python. If audio-forge isn't installed, the delegating commands (`adapt`, `audition`, `stem-mix`, `loop-doctor`, `deep`, `blend`, `lyrics`, `plan`) exit with a message to install the kit (`python3 install.py`).

## Reference handling

- One audio file → `./styles/N/` (one reference teaches one sound).
- Several audio files → each studied, then blended into a family in `./styles/N/` (shared habits + ranges; several teach a style).
- Only measurements of STYLE are stored. Never the reference's notes, melody, lyrics, footage, characters, text or logos. The reference never leaves your computer.

## Step-by-step tutorial

1. Study a reference:
   ```
   copy.py study ref.mp3 --name my-style
   ```
2. Show the brief: `copy.py show my-style`.
3. Build a candidate in that style (audio-forge compose with the draft genre, or `af.py compose --genre my-style`).
4. Score it: `copy.py compare cand.wav styles/my-style/dna.json`.
5. Change ONE knob per round, max 5 rounds, re-compare each time.

## Honesty

`compare` scores production style only, never whether it "sounds the same". The person's ears decide.

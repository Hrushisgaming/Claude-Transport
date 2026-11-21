# audio-forge — `lyrics`

Analyse the **lyrics** of a track: where the words sit against the bars, drops and sections; how dense, how repetitive, how rhymed. Statistics only by default — the words themselves are **not** stored unless you pass `--keep-text`.

## Exact command

```
# transcribe with Whisper (~500 MB, optional, asked first; never downloads silently)
python3 af.py lyrics AUDIO [--deep DEEP.json] [--model MODEL] [--language en] [--separate] [--keep-text] [--out OUT] [--name NAME]

# words from `af.py listen --words` — no Whisper needed here
python3 af.py lyrics AUDIO --words WORDS.json [--deep DEEP.json]

# lyrics you typed yourself — text statistics only, no timing
python3 af.py lyrics --text LYRICS.txt [--deep DEEP.json]
```

### Flags

| Flag | Meaning |
|---|---|
| `AUDIO` | the track (omitted when `--text` is used). |
| `--words WORDS.json` | word timestamps from `af.py listen --words`. |
| `--text LYRICS.txt` | lyrics you typed/pasted. |
| `--deep DEEP.json` | align words against bars, drops and sections. |
| `--model` / `--language` | Whisper model size and language. |
| `--separate` | use a Demucs vocal stem (~1 GB, ask first) — much better on music. |
| `--keep-text` | also write `lyrics.local.json` (private working copy: do not publish or commit it). |
| `--out` / `--name` | output folder and name (default `./lyrics/<name>/`). |

## Outputs

- `lyrics/<name>/lyrics.json` — `audio-forge/lyrics@1`: statistics only (counts, rates, positions, repetition and rhyme shares, theme-word counts).
- `lyrics.local.json` (only with `--keep-text`) — the words themselves; private, do not publish/commit.

## Honest limits

Whisper on music is noisy (instruments, effects, chopped samples, stylised vocals) — treat counts as approximate. No Whisper and no text = the tool says so and exits 3 so the agent can ask the person (it never downloads silently).

## Step-by-step tutorial

1. Get word timestamps: `af.py listen track.mp4 --words words.json` (ask-first for Whisper).
2. Produce the analyzer's section/drop map: `af.py deep track.mp4 --out deep/track/`.
3. Compute lyric statistics: `af.py lyrics track.mp4 --words words.json --deep deep/track/deep.json`.
4. Read `lyrics/track/lyrics.json` — where the words sit against bars/drops/sections, density, repetition, rhyme.

## Honesty

Statistics only. Whisper on music is approximate; `--separate` helps a lot. The words are not stored unless you ask (`--keep-text`), and that private copy must not be published or committed.

# audio-forge — `listen`

Transcribe speech to words + timestamps. Whisper is optional (~500 MB, asked first); it never downloads silently.

## Exact command

```
python3 af.py listen MEDIA [--srt OUT.srt] [--words OUT.json]
    [--model MODEL] [--language LANGUAGE]
```

### Flags

| Flag | Meaning |
|---|---|
| `MEDIA` | video or audio file. |
| `--srt` | write subtitles here. |
| `--words` | write word timestamps here (`[{"w","s","e"}, …]`). |
| `--model` | Whisper model size. |
| `--language` | language code (e.g. `en`). |

## Outputs

- `--srt` — subtitle file.
- `--words` — word-level timestamps JSON, usable by `af.py lyrics --words words.json` (no Whisper needed there).

## Step-by-step tutorial

1. Ask-first: offer Whisper (~500 MB) only if the user wants transcription; never download silently.
2. Transcribe: `af.py listen video.mp4 --srt out.srt --words words.json`.
3. Feed the words to lyric statistics without re-transcribing: `af.py lyrics track.mp3 --words words.json --deep deep.json`.

## Honesty

Whisper on music is noisy (instruments, effects, chopped samples, stylised vocals) — treat word counts and timings as approximate. `--separate` (Demucs vocal stem, ~1 GB, ask first) makes it much better. No Whisper and no text = the tool says so and exits 3 so the agent can ask the person.

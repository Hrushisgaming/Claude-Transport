# audio-forge — `tts`

Text-to-speech with automatic engine choice and a guaranteed offline fallback. All engines are free/local; no paid API, no sign-up.

## Exact command

```
python3 af.py tts --list
python3 af.py tts --text "Hello there" --out hello.wav
python3 af.py tts --file script.txt --engine kokoro --voice af_heart --speed 1.05 --out vo.wav
python3 af.py tts --text "Run." --voice-fx robot --out robot.wav
```

### Flags

| Flag | Meaning |
|---|---|
| `--text TEXT` | the text to speak. |
| `--file FILE` | read text from a file. |
| `--engine` | `auto` (default), `kokoro`, `piper`, `say`, `espeak`, `formant`. |
| `--voice` | voice id (engine-dependent). |
| `--speed` | speaking speed multiplier. |
| `--lang` | language code. |
| `--voice-fx` | `robot`, `radio`, `cave`, `deep`, `chipmunk`, `whisper`, `telephone`, `demon`. |
| `--out OUT` | output WAV path. |
| `--list` | which engines are installed + voices. |

### Engines (best first with `--engine auto`)

| Engine | Notes |
|---|---|
| `kokoro` | natural, 54 voices (en-US/UK, es, fr, hi, it, ja, pt, zh), ~350 MB optional model (`pip kokoro-onnx`) |
| `piper` | good, fast, ~60 MB per voice, many languages (optional download) |
| `say` | macOS built-in voices (free, nothing to install) |
| `espeak` | robotic but tiny (apt/brew install espeak-ng), 100+ languages |
| `formant` | built-in last-resort placeholder (pure numpy). Timing tests only — **NOT for final audio** |

With no voice pack installed only `formant`/system voices exist: tell the user, and ask-first offer the natural voice pack.

## Outputs

`<out>.wav` — synthesised speech.

## Step-by-step tutorial

1. See what's installed: `af.py tts --list`.
2. Speak some text:
   ```
   af.py tts --text "Welcome to the game." --out welcome.wav
   ```
3. If only `formant` is available, tell the user it's a timing placeholder and ask-first offer to install a natural voice pack (`kokoro` or `piper`) via `af.py doctor --install kokoro` (never install without asking).
4. Apply voice FX for character: `af.py tts --text "Run!" --voice-fx robot --out robot.wav`.

## Honesty

The `formant` voice is a timing placeholder, not speech to ship. Say which engine produced a voice. The synth engine makes convincing demos, not studio-realistic vocals. Non-English voices were not exercised in testing; English voices were.

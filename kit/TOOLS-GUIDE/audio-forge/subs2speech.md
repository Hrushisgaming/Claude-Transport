# audio-forge — `subs2speech`

Speak an `.srt` / `.vtt` / `.ass` subtitle file as a timed voice track (dub or voice-over). **Confirm intent with the user before running** — ask: replace the original speech (dub), keep it quietly underneath (voice-over), or just the voice track as a separate file? Which voice/language?

## Exact command

```
python3 af.py subs2speech SUBS.srt --out VOICE.wav [--duration 94.2]
python3 af.py subs2speech SUBS.srt --engine kokoro --voice af_heart --max-tempo 1.3 --out voice.wav
python3 af.py subs2speech SUBS.srt --video IN.mp4 --mode replace --out dubbed.mp4    # dub
python3 af.py subs2speech SUBS.srt --video IN.mp4 --mode mix --orig-db -16 --out vo.mp4   # voice-over
python3 af.py subs2speech SUBS.srt --voice-map '{"ALICE":"af_heart","BOB":"am_adam"}'
```

### Flags

| Flag | Meaning |
|---|---|
| `SUBS` | subtitle file (.srt .vtt .ass). |
| `--out OUT` | voice track / output video path. |
| `--duration DURATION` | total duration to fit cues into. |
| `--engine` / `--voice` / `--lang` | TTS engine, voice, language. |
| `--voice-fx` | robot / radio / cave / deep / chipmunk / whisper / telephone / demon. |
| `--speed` | speaking speed. |
| `--max-tempo` | cues longer than their slot are sped up (max ×1.35, pitch kept). |
| `--borrow-gap` | a cue may run into the silence before the next cue. |
| `--align {start,center}` | where to place the cue within its slot. |
| `--keep-sfx` | also speak `[bracketed]` sound descriptions. |
| `--voice-map VOICE_MAP` | JSON `{"SPEAKER":"voice"}` for "SPEAKER: text" lines. |
| `--video VIDEO` | input video to mux the voice onto. |
| `--mode {replace,mix}` | replace = dub, mix = keep original underneath at `--orig-db`. |
| `--orig-db` | original audio level when mixing (default −16). |

## Outputs

- voice track WAV (or dubbed/mixed video with `--video`).
- `<out>.fit.json` — cues that still don't fit after speed-up, so the text can be shortened. Read the report to the user and offer to shorten those lines, then re-run.

## Step-by-step tutorial

1. Confirm with the user: dub, voice-over, or voice track only? Which voice/language?
2. Run:
   ```
   af.py subs2speech subs.srt --engine kokoro --voice af_heart --out voice.wav
   ```
3. Check `<out>.fit.json` for cues that don't fit; shorten those lines and re-run.
4. To dub onto video:
   ```
   af.py subs2speech subs.srt --video in.mp4 --mode replace --out dubbed.mp4
   ```
   To voice-over (original kept quietly underneath): `--mode mix --orig-db -16`.

## Honesty

Never auto-dub because a subtitle file exists — confirm first. Whisper is not used here unless you route through `listen`. Cues that don't fit are listed, not silently stretched beyond the limit. Nobody has listened to the spoken result.

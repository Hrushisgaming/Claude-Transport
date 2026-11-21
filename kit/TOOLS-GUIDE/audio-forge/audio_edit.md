# audio-forge — `audio_edit`

Everyday audio editing on top of ffmpeg (nothing else to install). Each sub-command takes `IN OUT` plus its own flags.

## Exact command

```
python3 af.py audio_edit CMD IN OUT [flags]
```

### Commands

| Command | What it does | Key flags |
|---|---|---|
| `info FILE` | duration, codec, channels, sample rate, loudness | |
| `extract VIDEO OUT.wav` | pull audio out of a video | |
| `trim IN OUT` | cut a region | `--start`, `--end` |
| `fade IN OUT` | fade in / out | `--in`, `--out` |
| `norm IN OUT` | two-pass loudness normalisation | `--lufs` (streaming −14, speech −16, broadcast −23), `--tp` (true peak) |
| `convert IN OUT` | any format to any format | `--bitrate` |
| `concat A B C...` | join files | `--out`, `--xfade` |
| `mix A:gain:delay B:...` | layer files with per-file gain and start offset | `--out`, `--dur` |
| `duck MUSIC VOICE OUT` | music dips under the voice (sidechain) | `--amount`, `--delay` |
| `stretch IN OUT` | speed up/slow down without changing pitch (0.5–4×) | `--factor` |
| `pitch IN OUT` | pitch shift | `--semitones`, `--keep-tempo` |
| `eq IN OUT` | high-pass / low-pass | `--hp`, `--lp` |
| `loop IN OUT` | loop a bed to a length with crossfaded seams | `--dur`, `--xfade` |
| `silence IN OUT` | trim leading/trailing silence | `--thresh` |
| `mux VIDEO AUDIO OUT` | put audio on a video (never re-encodes video) | `--mode replace\|mix`, `--orig-db` |
| `beatcut IN OUT` | re-cut audio on beat boundaries | `--beatmap`, `--every`, `--bars` |

## Outputs

The edited/converted audio file at `OUT` (or alongside the video for `mux`).

## Step-by-step tutorial

- Normalise a music bed to streaming loudness: `audio_edit norm bed.wav bed_norm.wav --lufs -14 --tp -1.5`
- Duck music under voice: `audio_edit duck music.wav voice.wav ducked.wav --amount 0.35`
- Loop a bed to 90 s with crossfaded seams: `audio_edit loop bed.wav bed90.wav --dur 90 --xfade 1.0`
- Pull audio from video: `audio_edit extract clip.mp3 clip.wav`
- Mux a finished bed onto video without re-encoding the video: `audio_edit mux edit.mp4 bed.wav final.mp4 --mode replace`

## Honesty

`audio_edit` is a thin ffmpeg wrapper — it is deterministic and predictable. Loudness targets are conventions (streaming −14, speech −16, broadcast −23 LUFS), not rules. Nobody has listened to the result.

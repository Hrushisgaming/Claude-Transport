# Audio editing cookbook (`af.py audio_edit`)

| goal | command |
|---|---|
| inspect | `info file` (codec, duration, LUFS, true peak) |
| pull audio from video | `extract in.mp4 out.wav` |
| cut a region | `trim in.wav out.wav --start 3.5 --end 12` |
| fades | `fade in.wav out.wav --in 0.5 --out-fade 2` |
| loudness | `norm in.wav out.wav --lufs -14` (music/streaming) `-16` speech `-23` broadcast; two-pass, true peak -1.5 |
| format | `convert in.wav out.mp3 --bitrate 192k` (wav mp3 flac ogg m4a opus) |
| join | `concat a.wav b.wav --out c.wav --xfade 0.5` |
| layer | `mix music.wav:-6 voice.wav:0:2.5 sfx.wav:-3:10 --out mix.wav --dur 60` (file:gain_db:start_s) |
| music dips under voice | `duck music.wav voice.wav out.wav --amount 0.35` |
| tempo without pitch change | `stretch in.wav out.wav --factor 1.25` |
| pitch | `pitch in.wav out.wav --semitones -3 [--keep-tempo]` (uses rubberband when ffmpeg has it) |
| filter | `eq in.wav out.wav --hp 80 --lp 12000` |
| loop a bed | `loop bed.wav out.wav --dur 120 --xfade 1.0` |
| trim silence | `silence in.wav out.wav --thresh -45` |
| audio onto video | `mux video.mp4 audio.wav out.mp4 --mode replace` or `--mode mix --orig-db -18` (video stream copied) |
| re-cut on beats | `beatcut in.wav out.wav --beatmap map.json --every 1` |

Always write to a new file. Mix order for video: voice, then music (duck or bed-mix), then SFX, then `norm`.

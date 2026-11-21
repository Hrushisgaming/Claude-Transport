# Text to speech and subtitle voices

## Engines
| engine | quality | size | notes |
|---|---|---|---|
| kokoro | natural | ~400 MB (`doctor --install kokoro`) | 54 voices, ONNX, CPU. Verified in testing (English). Speed (measured on a modest 2-core cloud CPU): about 0.8x realtime once loaded (a 5 s line took ~7 s) plus ~40 s on the first call to load the model; faster on a modern laptop, but a few minutes of subtitles can take minutes. Each cue is synthesised once and cached. |
| piper | good | ~100 MB (`doctor --install piper`) | many languages; voice downloaded from the rhasspy/piper-voices repo. Not exercised in testing. |
| say | decent | built into macOS | `--voice Samantha` etc. |
| espeak | robotic | ~5 MB, system package | 100+ languages, `--voice fr` |
| formant | placeholder | built in | timing tests only, unintelligible by design |

`tts.py --list` shows what is ready. `--engine auto` prefers kokoro > piper > say > espeak > formant. If an engine fails it falls back and prints why.

## Kokoro voices
American f: af_alloy af_aoede af_bella af_heart af_jessica af_kore af_nicole af_nova af_river af_sarah af_sky; m: am_adam am_echo am_eric am_fenrir am_liam am_michael am_onyx am_puck am_santa
British f: bf_alice bf_emma bf_isabella bf_lily; m: bm_daniel bm_fable bm_george bm_lewis
Other: ef_dora em_alex em_santa (es) ff_siwis (fr) hf_alpha hf_beta hm_omega hm_psi (hi) if_sara im_nicola (it) jf_* jm_kumo (ja) pf_dora pm_alex pm_santa (pt) zf_* zm_* (zh).
The first letter picks the language automatically. Non-English voices were not tested here and may need extra phonemiser packages.

## Style
`--speed 0.8-1.3`, `--voice-fx robot|radio|telephone|cave|deep|demon|chipmunk|whisper`. Paragraph breaks (blank line) become 0.35 s pauses.

## Subtitles -> speech
1. **Confirm intent** (SKILL.md 3.5): speak the subtitles? replace / keep-under / separate track? which voice?
2. `subs2speech.py subs.srt ...` supports .srt .vtt .ass. Tags and `{\an8}` are stripped; `[door slams]` style cues are skipped unless `--keep-sfx`.
3. Fit: each cue is synthesised then sped up (never slowed) up to `--max-tempo` (1.35) with pitch preserved. `--borrow-gap` lets a cue use the silence before the next one.
4. `<out>.fit.json` lists every cue: slot, natural length, tempo, status `ok | overflows-slot | runs-into-next-cue`. Report problem cues to the user and offer to shorten the text, then re-run.
5. Multiple speakers: lines like `ALICE: text` plus `--voice-map '{"ALICE":"af_bella","BOB":"am_adam"}'`.
6. `--video in.mp4 --mode replace|mix` muxes with ffmpeg without re-encoding the video. `mix` keeps the original at `--orig-db` (default -16 dB) under the voice.
7. No subtitles: `listen.py video.mp4 --srt out.srt` (faster-whisper, ~500 MB, ask first), review the text with the user, then dub.

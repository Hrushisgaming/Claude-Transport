# Cinematic edit: style guide

## The tension arc (3-minute round, 1 killer vs 8 survivors)
| act | share | look | drone | heartbeat | what happens on screen |
|---|---|---|---|---|---|
| calm | 0-14% | cold | 0.10 | 55 | the setup. Title card. Slow, wide, quiet. |
| the hunt | 14-42% | teal | 0.30 | 70 | first contact. Counter "8 ALIVE". Small punches, ticks. |
| escalation | 42-72% | teal | 0.55 | 90 | downs and chases. Booms. Counter drops. First riser+impact. |
| finale | 72-92% | bleach | 0.85 | 115 | last survivors. Heaviest hits, freeze on the key moment, glitch. |
| payoff | 92-100% | warm | 0.25 | 60 | release: warm grade, slow, outcome title, bed swells. |
Shift act times to the real footage (`t` in source seconds); the percentages are only a start.

## Looks
`teal` (shadow teal / highlight orange: the cinema default), `cold` (calm, dread), `bleach` (desaturated high contrast: war, climax),
`warm` (relief, payoff), `noir` (B&W), `horror` (sick green shadows, red highlights), `natural`. Act changes crossfade over 1.2 s.

## Sound palette (all synthesised, free)
impact (sub drop + crack + tail) · boom · tick · riser · whoosh/swish · sweepdown (slow-mo) · heartbeat · drone (seamless loop) · glitch · reverse.
Rule of thumb: sub-heavy impact on the top 10% of moments, boom on the next 30%, tick on the rest.
Replace any sound with your own licensed one by editing `synth.KIT` or pre-mixing it into the music.

## Platform specs
9:16 1080x1920 (TikTok, Reels, Shorts: keep key action inside the centre 80%, avoid the bottom 15% and top 10% where UI sits; Shorts max 3 min,
Reels 3 min, TikTok up to 10 min) · 16:9 1920x1080 · 1:1 1080x1080 · 4:5 1080x1350. Loudness -14 LUFS, true peak -1 dB. H.264 + AAC.

## Pacing
Hook in the first 1.5 s (a hit, or the title with a riser). Cut/hit about every 1.5-3 s in the body, every 0.6-1.2 s in the finale.
One quiet beat (0.5-1 s of near silence) before the final hit makes it land.

## 16:9 gameplay to 9:16
`reframe.mode: "fit"` keeps the whole HUD over a blurred background (safe, good for reading kills). `"cover"` with `x` set to where the action is
fills the frame (more cinematic, loses the sides). For long chases, split into two plans or key `x` by hand per act.

## Known limits
Moments are found from loudness and motion, not understanding: always review. Frame-by-frame Python rendering: a full 3-minute 1080x1920 render takes
roughly 10-15 min on a laptop; use `--preview` while editing. No face/object tracking (reframe.follow tracks motion only), no AI upscaling. Captions need a transcript (transcribe.py).
For styles other than the action arc above see `video-styles.md`; `styles.py show <id>` prints a preset.

## Documentary devices: when to use which
- `tile_reveal`: open a chapter / swap the world. `strobe`: land one abstract word with 4-8 shape-matched images at 2-3 frames each
  (all circles, all banknotes): random crops are NOT a strobe. `pop_collage`: the line lists things (one card per word).
  `wall3d`: "everyone / everywhere". `cutout_world`: the hero line naming a list of variants; keep the huge word to 1 short word.
- Pace: a new picture every 0.6-1.5 s in the open and the chapter starts; let the body breathe to 1.2-2 s with internal motion.
- Face: the speaker is one picture in the stream, not the default. (Known difference from editor-v1: the act grade is applied to the face too;
  keep `look` subtle on face-heavy videos or keep faces in a `natural` act.)
- Captions: small white words, one at a time; italic serif for a stressed phrase; 2.3x for the one key word.
- Every word on screen was said. Titles are the thing named (a real name, a real number), never a slogan.

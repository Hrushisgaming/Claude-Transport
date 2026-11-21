---
name: cinematic-edit
description: >-
  Edit ANY kind of video locally and free, in any aspect ratio (9:16, 16:9, 1:1, 4:5), with 18 style presets: gaming/sport
  highlights, horror chases, trailers, vlogs, travel, talking-head/podcast, tutorials, product ads, music videos, found-footage
  documentaries, comedy/memes, aesthetic lofi, anime edits, weddings, news explainers, real estate, cyber/tech. It finds the
  moments from audio and motion (no speech needed), then adds speed ramps, punch-ins, shake, flashes, glitch, act-by-act colour
  grading, risers and impacts, titles/counters/lower thirds, word-by-word captions, audio-reactive visualizers, documentary
  devices (tile reveals, strobes, 3D wall, cut-out speaker), silence removal (jump cuts), shot detection, beat-cut montage,
  auto-follow reframing, platform exports. Pairs with the audio-forge skill (offered, never assumed): it composes a music bed whose
  drop lands on your biggest moment, speaks subtitles, adds sound effects. Use for: "edit this video", "make this cinematic",
  "cut to the beat", "TikTok / Reels / Shorts edit", trailers, highlight reels, vlogs, tutorials, podcasts, ads, "remove the silences",
  "add music and sound effects". Replaces editor-v1.
---

---

# CINEMATIC EDIT

You are the editor. The scripts measure the footage, the **plan** (`plan.json`) is the edit, the renderer
executes it. Your job is judgement: which moments deserve a hit, what the story arc is, what looks cheap.
Everything runs locally and free (ffmpeg + Python: numpy, opencv, pillow). **Nothing is uploaded or posted.**

Every bash step starts with `source <skill>/scripts/env.sh` (`<skill>` = this folder; sets `$CE_PY`).
First time: `bash <skill>/scripts/doctor.sh` until it prints "All set".

## Pick the style, then the mode

**Style first.** Ask which kind of video it is (or infer it from the request and say so). `python3 scripts/styles.py list` prints the 18
presets; `reference/video-styles.md` is the guide (what each does, pacing, workflow). Pass it as `analyze.py ... --style <id>`: it sets the
format, the colour arc, how hard and how often it hits, captions, loudness and the audio mode (`voice` / `music` / `hybrid`).
Unsure? Gameplay or sport -> `hype-highlight`/`sport`; horror -> `horror-chase`; a person talking -> `vlog`/`talking-head`/`tutorial`;
clips + a song -> `music-video`/`anime-amv`/`travel`; product -> `product-ad`; found footage + voice -> `documentary`.

| input | do |
|---|---|
| One video: gameplay, sport, action, b-roll, screen recording | **A. Moments edit** |
| Several clips + a track | **B. Beat montage**, then A on the result |
| A person talking (vlog, podcast, tutorial, comedy) | **D. Talking edit** (silence_cut first), then A with a speech style |
| Voice-over wanting the found-footage look | **C. Documentary mode** (captions + devices + sourcing) |

Footage facts first: `python3 scripts/scenes.py video.mp4` reports how fast it is already cut (average shot length, cuts/min) and writes `work/shots.json`.

Ask for anything essential that is missing (the video; target format; optional music) in ONE short question,
otherwise decide and state your assumptions at the top of your reply.

## A. Moments edit (the core loop)

1. **Analyze.** `$CE_PY <skill>/scripts/analyze.py <video> --out work --plan plan.json --style <id> [--format 9:16] [--music track.mp3] [--n 24]`
   Prints every moment (time, strength, audio/motion) and writes a DRAFT plan. Tune `--n` (how many hits),
   `--gap` (min seconds between them). A 3-minute round wants ~15-30 moments, not 100.
1b. **Find the moments that matter from the game's HUD** (better than loudness): ask for 2-3 screenshots of the banner/kill-feed, pick the ROI (fractions of
   the frame) and crop the icon as a template, then `$CE_PY <skill>/scripts/hud_events.py video.mp4 --roi x,y,w,h --template icon.png --label "survivor down" --merge plan.json --sfx impact`
   (`--change 0.1` instead watches the region for any change: new kill-feed line, a counter ticking). Rising edges only, ~1.2 s apart. No OCR needed.
1c. **16:9 gameplay to 9:16:** set `reframe.follow: true` (tracks the centre of motion, smoothed, dead-zoned, speed-limited; `$CE_PY <skill>/scripts/follow.py video` previews the track).
   It follows motion, not meaning: if the game camera tracks your character it stays near centre, so set `reframe.x` by hand per section instead.
2. **Look at the footage** before trusting the numbers: grab frames at each moment
   (`ffmpeg -ss T -i video -frames:v 1 -vf scale=360:-2 f.png`, or render stills, see 5). Machines find
   LOUD, not MEANINGFUL: re-rank by the story. In a chase: the first down, the hook, the last-survivor
   moment, the escape. Delete weak/duplicate events, change `strength`, add events by hand at moments the
   detector missed (an event is just `{t, strength, fx, sfx}`, `t` = SOURCE seconds).
3. **Write the arc** (`acts`, see `reference/styles.md`): calm -> the hunt -> escalation -> finale -> payoff.
   Each act sets the colour grade, the drone level and the heartbeat BPM. The finale should be the loudest,
   fastest, most desaturated act; the payoff releases it.
4. **Add storytelling overlays**: `overlays` titles at the start, a `counter` each time a survivor goes
   down ("5 LEFT" ... "LAST ONE"), a `lower_third` naming a player/character. Only text that is true to
   the footage. Never invent names or facts.
5. **Preview.** `$CE_PY <skill>/scripts/render.py plan.json out --preview` (half-size, about real-time).
   Check stills: `render.py plan.json out --preview --range 40,46 --png` writes a frame every 0.25 s.
   Look at them (Read the PNGs). Check: nothing important covered by the visualizer or captions, hits land
   on the picture, text legible, no black frames.
6. **Final.** `$CE_PY <skill>/scripts/render.py plan.json out` -> `out/final.mp4` (loudness -14 LUFS).
   Full size is ~4x slower than preview; tell the person to expect minutes, not seconds.
7. **Export.** `$CE_PY <skill>/scripts/export.py out/final.mp4 --preset tiktok|reels|shorts|youtube|x|all --plan plan.json --words work/tx/words.json --out exports`
   re-encodes per platform (crf + bitrate cap, loudness), warns on aspect/length, writes `.srt` (times follow speed ramps) and a thumbnail from the best frame near your hits.
   Limits are defaults: check the platform's current rules.
8. **Verify and hand over.** `ffprobe` the file (duration, size, audio present), watch the contact sheet,
   state what you did and what you'd change next. Publish nothing.

## B. Beat montage (uploaded clips + music)

`$CE_PY <skill>/scripts/montage.py clipA.mp4 clipsdir/ --music track.mp3 --out assembled.mp4 --format 9:16 --dur 30 --every 2`
Cuts a new shot every `--every` beats (1 frantic, 2 default, 4 slow). Then run A on `assembled.mp4`
(the music is its audio, so hits come from the track). Use the characters' footage as the hero shots:
put the strongest clip on the downbeats of the drop.

## C. Documentary mode (editor-v1's moves, built in)

For a spoken take: a new real picture every 0.6-1.5 s, each re-coloured, sound on every change.
1. `$CE_PY <skill>/scripts/transcribe.py take.mp4 --out work/tx/words.json` (faster-whisper or `npx hyperframes`; install with `doctor.sh --install-whisper`).
   Fix misheard names by hand, keep the timings. Cut restarts/long pauses first, then transcribe the cut file.
2. **Source real material for every line** (the thing named, not a stock cliche; a metaphor/pun where the line allows):
   - moving footage: `$CE_PY <skill>/scripts/sourcing/find_footage.py "<idea>" work/find --src archive,nasa,commons,mixkit` -> numbered thumbnail
     sheet; choose by LOOKING; cut with `fetch_clip.py <media-url> clips/x.mp4 --ss 3 --dur 1.2 --format 9:16 --look teal`.
   - company pages/posts: `node <skill>/scripts/sourcing/capture.mjs jobs.json assets/captures` (needs Node 22+ and Chrome). LOOK at every capture:
     consent walls, bot checks and scroll-reveals return plausible blank pages; drop those.
   - verify every number/claim on the real page, quoted exactly and dated. No random people unless they are the subject of the line.
3. **Record every source** in `plan.sources` (`id, path, url, licence, flag, approved, note`) and run `plancheck.py plan.json --md PLAN.md`.
   **Show the person PLAN.md (every line, its picture, its source, licence, FLAGs) and wait for a go.** FLAG anything unclear: a company's own film,
   a news photo, someone else's clip, game footage. The final render is blocked until nothing is undeclared and every FLAG is `approved: true`.
4. Add `captions` and `devices` to the plan (below), grade acts, preview, finish as in A.
5. `$CE_PY <skill>/scripts/verify.py out/final.mp4 work/tx/words.json` re-transcribes the final and lists words a hit or the bed masked.
   Never put an impact ON a name. Fix, re-render, re-verify.
Optional cut-out: `bash <skill>/scripts/doctor.sh --install-matte`, then `matte.py --plate take.mp4 --start S --dur D --out matte.mp4 --size 1080x1920 --trust-repo`
(runs Robust Video Matting from GitHub via torch.hub: that is why `--trust-repo` is required; pin with `CE_RVM_REF`).

## D. Talking edit (vlog, podcast, tutorial, comedy, news explainer)

1. `$CE_PY <skill>/scripts/silence_cut.py take.mp4 --out work/cut.mp4` removes dead air (tune `--thresh -40` for noisy rooms, `--min-silence` for more breathing). Report how much was removed. Your original is untouched.
2. `transcribe.py work/cut.mp4 --out work/tx/words.json` (transcribe the CUT file), fix misheard names, then `analyze.py work/cut.mp4 --style vlog|talking-head|tutorial|comedy-meme ...`.
3. Speech styles keep effects light (`events.mode` emphasis/none): captions carry the edit. Add `lower_third` for real names, a `counter` per tutorial step, `terminal`/`code_scroll` devices for commands.
4. Voice first: `audio.mode: "voice"` ducks the bed and lowers effects. Noisy voice? `audioforge.py clean-voice in.wav out.wav` (rumble cut, denoise, even out).
5. Preview, check stills, final, export as in A.

## Audio: music, voice, sound effects (optional: the audio-forge skill)

audio-forge is a separate free, local skill. **Never assume it exists and never use it without the person's yes.**

1. **Detect** (silent): `$CE_PY <skill>/scripts/audioforge.py detect` -> JSON, exit 0 = ready; 1 = not installed (say once: "audio-forge is not installed; it is free and local, want to continue without it?"); 2 = installed, not ready (show `fix`).
2. **Ask once per project** (skip if `work/audio-forge.json` exists, the person said "no music"/"use audio-forge", or supplied their own track and said to use it; if you cannot ask, do not use it). Use your question tool, else chat:
   "Do you want me to use audio-forge for this video's sound? It runs on your computer: a music bed that fits your cuts with the drop on your biggest moment, subtitles read aloud, extra sound effects. Nothing is uploaded." Options: Yes, use it for what fits / Only some (bed, sfx, voice) / No, I'll bring my own audio / Not now.
   Save: `audioforge.py state --set yes|partial|no|later --parts bed,sfx,voice`.
3. **Plan first.** `audioforge.py score plan.json [--seed 1] [--genre G] [--sfx]` builds a *brief* from the plan (acts, hit times after speed ramps, cut times from `work/shots.json`), asks audio-forge to compose, and writes a patched copy `plan.scored.json` (your plan is unchanged until you pass `--apply`). It prints the genre, BPM, and where the drop lands versus your hero moment. Show that with the rest of the plan and wait for the go.
4. **Audition honestly.** You have not listened to the bed. Offer `--seed 2/3` or `--genre` for other takes; change `audio.music_db` if it fights the footage.
5. Extras: `audioforge.py sfx record_scratch camera_shutter ...` then `audioforge.py cue plan.json --at 3.2 --sfx record_scratch` adds one effect at a time; `audioforge.py voice plan.json --subs lines.srt --yes-confirmed ...` turns subtitles into a voice track **only after the person confirms** (replace the original / keep it underneath / separate file, which voice). Optional downloads (natural voices ~400 MB, etc.): ask with the question strings from `af.py doctor --list-optional --json`.
6. Rights: an audio-forge bed is recorded in the plan as `audio_forge` with `synthesised: true`, so `plancheck.py` marks it "original, no third-party rights". Your own music still needs a source row.
7. If the person's own track is used (`--music`), offer once to detect its beat so cuts land on it (`montage.py` does this; `analyze.py --music` reports the BPM).

Plan fields this adds: `music_start` (song second that plays at video 0), `voice` + `voice_at`, `sfx_cues` (cue sheet `<video s> <wav> <gain>`), `audio.voice_db`, `audio.voice_duck_db` (default -12), `audio.mode`, `audio_forge{...}`. The bed still drops out ~0.28 s before an `impact`; set the music to start its own drop on the hero moment (that is what `score` does) and the two reinforce each other.

## Plan reference (plan.json)

- `format` 9:16 | 16:9 | 1:1 | 4:5. `fps` 30. `start`/`dur` = source window in seconds.
- `reframe`: `{mode: cover|fit, x: 0..1, bg: blur}`. `cover` crops to fill (`x` = horizontal focus); `fit` keeps the
  whole frame over a blurred copy: use it for 16:9 game footage going to 9:16 when the HUD matters.
- `look`: `grain, vignette, bloom, letterbox (0.0-0.12 bar height), beat_zoom` (bass-driven pulse).
- `acts[]`: `{name, t, look: natural|cold|teal|warm|bleach|noir|horror, drone: 0-1, heart_bpm}`; `t` in source s.
- `events[]`: `{t, strength 0-1, fx: [punch, shake, flash, chroma, glitch], sfx: impact|boom|tick|glitch|whoosh|subdrop,
  riser: seconds (a riser ends exactly on the hit), pre: "reverse", ramp: {speed, dur, lead}}`
  `ramp.speed` 0.3 = slow-mo, <=0.1 = freeze/hold (source audio mutes, sweep-down plays).
- `captions`: `{words: path|list, pos: lower|center|top, size: 62, max_words: 5, keywords: [..] (big, 2.3x), stress: ["phrase"] (italic serif), color, key_color}`.
  Words appear one at a time at their onset. Only words that were said.
- `devices[]`: `{type, t (source s), dur (out s), images: [path | {path, treat}], treat}` with types
  `tile_reveal` (3x3 panes flash white then the picture, 1/frame, a click each; `grid`, `push`),
  `strobe` (`per` frames each, shape-matched images, a click each), `wall3d` (`cols`, `rows`; silent),
  `pop_collage` (`every` s, `card` width fraction), `cutout_world` (`matte`, `matte_start`, `mega` word, `mega_color`, `every`, worlds in `images`, `raw_speaker: true` pastes the speaker back UNGRADED),
  `typewriter` (`text`, `cps`, `bg`, `color`: a quoted line typed with a caret), `terminal` (`lines`: `$ cmd` lines are typed, others print),
  `code_scroll` (`code`, `mark`: line numbers swept by a highlighter once scrolling stops; keep marked lines inside the final visible window). Use only REAL text.
  `treat`: a look name, `halftone`, `led`, `negative`, `hue=140`, `duo=#ff2a55` (duotone), combined with `+` like `teal+halftone`. Devices write their own click cues.
- `acts[].halftone` 0-1 adds the dot screen to an act. `acts[].raw: true` skips the whole grade/vignette for that act (talking-head beats stay natural, as in editor-v1). `sources[]`: see Documentary mode.
- `overlays[]`: `{type: title|counter|lower_third|caption, t, dur, text, pos, color, scale}`.
- `visualizer`: `{style: bars|ring|line, pos: top|center|bottom, color: "#hex", opacity, mirror}` or omit to turn off.
- `audio`: `game_db, music_db, duck_db, sfx_db, voice_db, voice_duck_db, lufs, mode (voice|music|hybrid)`. `music`: path or null; `music_start`; `voice`; `sfx_cues`; `style`.
- Looks (`acts[].look`): natural cold teal warm bleach noir mono horror amber, and new: vivid clean film pastel golden sport cyber sepia matte.

## How to make it hit harder (checklist)

- **Contrast of silence and size.** The bed drops out ~0.28 s before every `impact` automatically; use `impact` on
  only the top few moments, `boom` on mid ones, `tick` on small ones. If everything hits, nothing does.
- **Anticipation.** Risers (1-1.5 s) + the 3-frame push-in before the hit sell it. Add a `ramp` on the single best moment.
- **Escalate.** Cut density, heartbeat BPM, grade contrast and visualizer opacity all rise act by act.
- **One hero moment.** A freeze (`ramp.speed` 0.05, dur 0.8) + title card is the shot people remember. Use it once.
- **Never mask the voice.** If the footage has commentary/speech, keep `sfx_db` <= -6 and avoid `impact` over words.
- **Restraint with the visualizer.** Bottom, 0.6-0.8 opacity, one style per video.

## Rules

1. Look at real frames before delivering. Never claim a result you have not inspected.
2. Do not invent events: every overlay must be true to what the footage shows.
3. Rights: music, found footage and game IP belong to someone. Every external asset goes in `plan.sources` with a licence; unclear = FLAG; the person approves.
   The final render refuses to run until the gate passes (`--force-rights` only if the person decided). No music ships with this skill: bring your own, or (only with the person's yes) let audio-forge synthesise an original bed.
4. Nothing is uploaded, posted or published. Work only inside the video's folder, `~/.cache/cinematic-edit`, and the user's output folder.
5. Keep sources untouched; write to `out/`. Do not delete the person's files.
6. audio-forge (music, voice, effects) only with the person's yes; subtitles-to-speech only after they confirm what happens to the original audio; ask before any optional download; never pretend to have listened to generated audio.
7. Anything REAL that you draw, model, recreate or write on screen (a character, game, controller, product, person, place, number, date) goes through the `reference-check` skill first: search, look at real reference images, write your own checklist, compare and fix, log verified facts. Never from memory. `plancheck.py` lists the checked facts and blocks the final render while a fact shown on screen is unverified.
8. Show the plan (arc, hits, audio plan, sources) and wait for the go before the final render. Styles are starting points: say which style you chose and why.

## Files

`scripts/`: `styles.py` (18 presets) · `scenes.py` (shot detection, shots.json) · `silence_cut.py` (jump cuts) · `audioforge.py` (bridge to audio-forge) · `analyze.py` (moments, beats, draft plan) · `montage.py` (beat cuts) · `mixdown.py` (soundtrack) · `render.py` (picture + final mux) ·
`follow.py` · `hud_events.py` · `export.py` · `devices.py` · `captions.py` · `looks.py` · `plancheck.py` (PLAN.md + rights gate) · `transcribe.py` · `verify.py` · `matte.py` · `fetch_clip.py` ·
`sourcing/find_footage.py`, `sourcing/capture.mjs` · `reference/editor-v1-notes/` (measured numbers, read-only) · `synth.py` (sound kit, in code) · `ce_common.py` · `doctor.sh` · `env.sh` · `ce.sh`
`reference/styles.md` (arcs, looks, platform specs) · `reference/video-styles.md` (the 18 styles) · `templates/plan.example.json`

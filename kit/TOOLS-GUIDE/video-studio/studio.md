# video-studio — `studio.py`

One front door for making any video with the cinematic-edit and audio-forge skills working together. Use it when the user wants a finished video with **picture and sound handled in one flow**: highlight reel, vlog, trailer, tutorial, podcast clip, ad, travel film, wedding film, meme… It picks the style, runs the edit, offers audio-forge for music/voice/effects, and keeps both on one plan.

## Exact command

```
python3 studio.py doctor                            # JSON: where cinematic-edit and audio-forge are, whether each is ready
python3 studio.py new NAME --style STYLE [--source VIDEO.mp4]
                                                    # create NAME/ with work/ and work/studio.json
```

## What `studio.py doctor` reports

JSON with:
- `cinematic_edit`: dir, ready (ffmpeg + numpy + cv2 + PIL present), fix command
- `audio_forge`: dir, ready (capabilities JSON), fix command — **optional**, only used with the person's yes
- `others`: style-copy, reference-check, canvas, editor-v3, 2d-animation-long-form-aivxer locations
- exit 0 = cinematic-edit ready; exit 1 = not ready

## The flow (from SKILL.md)

1. **Intake** (one short question at most; otherwise decide and state assumptions): footage, kind of video, target format, own music or voice? Pick a style (`python3 <cinematic-edit>/scripts/styles.py list`).
   - gameplay/kill montage → `hype-highlight`; trailer → `trailer`; talking → `vlog`/`talking-head`/`tutorial`/`comedy-meme`; product → `product-ad`; clips + song → `music-video`/`anime-amv`; travel → `travel`; found footage + narration → `documentary`; "make it like THIS" → **style-copy** skill.
2. **Start the project:** `studio.py new myvideo --style vlog --source take.mp4` → `myvideo/`, `myvideo/work/studio.json` (records style/source/answers so nothing is asked twice).
3. **Prepare picture:** silence_cut, transcribe, montage, scenes → `work/shots.json`.
4. **Draft the edit:** `analyze.py <video> --out work --plan plan.json --style <id>`; look at frames; re-rank by story.
5. **Ask about audio (once):** genre, BPM, where the drop lands, level. Skip if they brought their own track.
6. **Plan the sound:** `af.py score --brief brief.json --out work/bed.wav` (speech styles get a quiet bed −22 to −26 dB under voice).
7. **Show the plan and wait for the go:** arc, hits, audio plan, sources and rights (`plancheck.py plan.json --md PLAN.md`).
8. **Preview, inspect, adjust:** `render.py plan.json out --preview` and stills. Offer another bed take (`--seed 2`) rather than describing sound you cannot hear.
9. **Final and export:** `render.py` then `export.py --preset tiktok|reels|shorts|youtube|x|all`.

## The other skills in this kit

`canvas` (minimal talking-head explainer), `editor-v3` (long cinematic silhouette edit — spends the person's Higgsfield credits, show the cost first), `2d-animation-long-form-aivxer` (animated explainer from a script). Each has its own SKILL.md and setup; load and follow them, do not rewrite their rules.

## How audio-forge plugs in (ask first)

- Original bed with no rights worries: `af.py score --duration D --style documentary|talking-head --hero T --exact --out bed.wav`
- Canvas: `bed-mix.py --song bed.wav --song-at 0 --dur D --under 18.6`
- Editor-v3: `EDITOR_SONG=bed.wav`, `DROP_IN_SONG` = bed's `drop_start_s`, `DROP_AT` = hero time

## Honesty

video-studio orchestrates; cinematic-edit and audio-forge each own their own rules and limits. Nobody has watched or listened to any generated output. The kit song in editor-v3 has an unconfirmed licence — use an audio-forge bed or your own track for monetised videos.

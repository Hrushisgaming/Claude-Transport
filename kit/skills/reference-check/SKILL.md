---
name: reference-check
description: MANDATORY before drawing, modelling, animating or writing on-screen facts about any real thing - a character, game, controller, product, person, place, logo, number, date. Forces a real search, real reference images that you actually look at, your own written checklist built from them, a compare-and-fix loop against the references, and a logged record of what was verified. Use whenever a task says "draw X", "make X look like the real one", "put the X controller in the video", "recreate/animate this character", "add a lower third / stat about X", or a video plan names a real game, character, device or brand. Works with whatever web tools the host has (websearch, webfetch, or the free refs.py fallback). Used by cinematic-edit, video-studio and the roblox story kit.
license: MIT
compatibility: opencode, Claude Code. Python 3.9+ (Pillow for contact sheets). Web access optional but expected.
---

# reference-check: look it up, look at it, write your own checklist, compare, fix

Memory is wrong about how real things look and what is current. A first attempt "from what you know" produces a generic, inaccurate picture (it invents decoration, drops signature features, changes the outfit, picks the wrong form). This skill replaces that with a protocol you must follow in order. Do not skip steps; do not draw first.

Script: `python3 <skill>/scripts/refs.py ...` (state lives in `work/refs/` and `work/refs.json` of the current project).

## Boundaries (always)
- Work only inside the folder the person gave you. Never read, run or edit files elsewhere, in particular any test lab, `reftest.py`, `reflab`, `subjects.json`, `duels.json`, or a `reference.*` answer key. If you find one, ignore it and say so.
- Never score or rank your own work against a test, and never register results in a lab. Your report is descriptive only (what matched, what did not).
- The compare loop is capped at 4 rounds. Stop there even if items are still off, and report them. Do not keep polishing.
- A reference image you were not given must come from your search; do not use a local file you stumbled on as a reference.

## Long sessions and context compaction
Your context may be compacted (summarised) at any time, and a summary drops the actual images and most tool output. Therefore the FILES are your memory, not the chat:
- Save every reference image to `work/refs/<subject>/ref1.jpg ...` the moment you get it. Keep the render of each round as `work/refs/<subject>/round<N>.png`.
- Keep the checklist in `work/refs.json` (it is, via `refs.py checklist add`) and record every compare verdict with `refs.py compare`. Also keep the drawing script, never only its output.
- After any compaction, or whenever you are unsure what state you are in: run `refs.py compare status`, re-read `work/refs.json`, and RE-VIEW the reference image files and your latest render before you continue. Never continue from the summary's description of how a picture looked.
- Keep the round count in the files, not in your head: the cap is 4 rounds.

## 0. Can you do this? (stop early if not)
- You must be able to LOOK at images. Prove it before you rely on it: after you save the first reference image, open it with your image-viewing tool and state 3 specific visual details (colours, positions, shapes) that you could only know by seeing it. If the tool returns only a placeholder such as "image read successfully", or you cannot state real details, you are NOT seeing it: do not decode pixels with scripts and do not describe from memory. Retry once; if it still fails, say so in one sentence and ask the person to attach the image in the chat, or for a model that can see. Never pretend you looked.
- You need some way to get pages/images: your own `websearch`/`webfetch` first, else `refs.py wiki|commons|get` (free, no key). If nothing reaches the web, ask for 2-3 reference images or links; do not fall back to memory silently.

## 1. Pin down exactly WHAT (one question at most)
Many things have versions: a character's forms, a controller's generations, a game's remaster. Write the target in one line ("Ryomen Sukuna, Jujutsu Kaisen, normal two-armed form, anime style"). If the request is ambiguous and the versions differ visibly, ask which; otherwise choose the most common one and say so. Everything below is judged against THIS line.

## 2. Search (at least 3 different queries; log them)
1. the official or canonical page (publisher, studio, manufacturer, official wiki);
2. reference pictures of the exact version (angles, front, side, full body);
3. a disambiguation check (what differs between versions, what is easy to get wrong).
Privacy: queries contain only public names and descriptions, never the person's footage details, file names, paths or personal text. Prefer original sources over aggregators. Where sources disagree, say so and prefer the official one. Record each factual claim you will rely on: `refs.py claim "text" --source URL --verified yes|no`.

## 3. Get 3 reference images (2 minimum) and LOOK at them
`refs.py get URL --out work/refs/<subject>/ref1.jpg` (or your own fetch tool), then `refs.py sheet work/refs/<subject>` makes one numbered contact sheet. View it. (If it says Pillow is missing, view the image files one by one instead; never install packages or decode pixels to compensate.) Choose different angles; reject low quality, fan-redraws that disagree with the official look, and watermarked or cropped ones unless nothing else exists. References are look-only: never paste, trace or ship them (rights).

## 4. Write YOUR OWN checklist from what you actually see
`refs.py checklist new "<subject line>"` starts the checklist, then add each item with `refs.py checklist add --category C --observation "..." --ref ref1.jpg [--unsure]`. Write at least 14 concrete, visually checkable items, each tagged with its category and the reference image it came from. Required categories (the script refuses to continue without them):
- `silhouette` overall shape and proportions (head size, limb length, width vs height)
- `colour` exact palette (hair, skin, outfit, accents; name the colours)
- `count` how many of each thing (eyes, arms, buttons, wheels)
- `position` where each marking/feature sits relative to others
- `clothing` EVERYTHING worn or covering the body, top to bottom; nothing may be left bare or cut off unless the reference shows it
- `pose` the pose, angle, framing and crop of the reference you are matching
- `signature` the 3-5 features that make it recognisable at a glance
- `must_not` things NOT in the reference that you must not add (extra text, logos, kanji, glows, symbols, backgrounds, decorations), plus anything you were tempted to invent
Write observations, not memories: "black band, 2 stripes, upper left arm" not "has armbands". Mark `unsure` where the pictures do not settle it, and go back to step 2 for that item. `refs.py checklist check` validates it.

## 5. Make it from the checklist only
Build the drawing/model/graphic using ONLY the checklist. Hard rules:
- Faithful beats creative. No background, text, symbols, glow, particles, frames or flourishes unless the task asked for them; plain background otherwise.
- Match the reference pose and framing unless told otherwise. A standing front pose is not a substitute for a requested/ referenced pose.
- Fully dressed as the reference: draw the lower body, outfit and props, and never leave a figure bare, faded out or cropped where clothing belongs.
- Get silhouette, colour and the signature features right before any detail. If you cannot draw a detail well, simplify it; do not draw it wrongly.
- No invented text, logos, numbers or names. On-screen facts come only from verified claims.

## 6. Compare and fix (minimum 2 rounds, maximum 4)
Render, then `refs.py sheet --pair work/refs/<subject>/ref1.jpg render.png` and LOOK at the pair. For EVERY checklist item record the verdict: `refs.py compare <round> <item_id> matched|off|unsure --note "what is different"`. Fix every `off`/`unsure` item (change the drawing, not the checklist), re-render, repeat. Stop when all items are matched or after round 4; `refs.py compare status` lists what is still off. Be strict: partially right is `off`. Compare against the reference, not against your intention.

## 6b. Final check
Look once more at the whole picture next to the reference: could someone recognise the subject in one second? Anything bare, missing, extra, or in the wrong colour is a failure; fix it or report it.

## 7. Report (short, honest)
Say which references you used (links), the checklist score (matched/total), and the items you could NOT match. Never say "accurate" or "perfect"; say what matched. `refs.py report > work/refs/REPORT.md` produces the "Checked facts" table that cinematic-edit puts in PLAN.md; claims older than 30 days or unverified are flagged, and unverified claims shown on screen block the final render in `plancheck.py`.

## Facts on screen (titles, lower thirds, counters, specs)
Every number, name, date, price or spec shown on screen must have a verified claim (two sources when it is a figure; official source preferred), logged with its date. If you cannot verify it, do not put it on screen; ask the person for the value.

## Quick reference
```
refs.py init                       refs.py wiki "Title"          # free, keyless: page summary + image URLs (Wikipedia)
refs.py commons "query"            # free image search on Wikimedia Commons (URLs + licence)
refs.py get URL --out DIR/ref1.jpg # download a reference image (look-only)
refs.py sheet DIR | --pair A B     # numbered contact sheet / reference-vs-render pair
refs.py claim "text" --source URL --verified yes|no [--on-screen]
refs.py checklist new "subject"   refs.py checklist add --category C --observation T --ref ref1.jpg   refs.py checklist check
refs.py compare ROUND ID matched|off|unsure [--note T]    refs.py compare status
refs.py report                     # markdown table of checked facts
```

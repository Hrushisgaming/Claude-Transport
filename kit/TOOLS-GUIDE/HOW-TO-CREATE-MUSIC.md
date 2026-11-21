# How the AI should create music with this kit

Read this before composing. Nobody who builds with this kit can hear the result: everything below exists to reduce guessing.

## 0. Rules that never change
1. **Say plainly that nobody has listened** to what you made. Report measurements, not impressions.
2. **Variation is the default.** Do not pass `--seed` or fixed values unless the user asked for them. Every choice the user did NOT specify must be allowed to differ from the last run (key, tempo, chord cycles, drums, palette, structure, ending, SFX, motifs). Lock only what the user said (`--lock key=D,bpm=176`).
3. **Original music only.** References give structure, tempo, density, instrument roles and mood. Never copy melodies or chord-for-chord progressions.
4. **One knob per round** when fixing something. Re-render with the same seed (`--seed`/`--same-as`) so only that knob moves.
5. **Listener numbers are not facts.** A listening AI's mood verdict is useful; its BPM, timestamps and durations are not. Check with `af.py deep`.

## 1. Understand the brief (ask at most one question)
Write down: target feeling (hunted, heroic, eerie, presenting), priority list of references (highest first), things to exclude (e.g. Fired and Showtime are a different style), and anything the user locked (key, tempo, length, instruments).

## 2. Look up the mood before writing a note
`forge/recipe.py` MOODS holds what feedback taught us. For "hunted": minor only (i, bII, VI, iv, leading-tone V; never C or G major), cold piano, dark choir, tubular bells on key beats, distorted guitars front and centre, chopped Amen breakbeats, creeping stereo SFX, a vocal shout before the drop, a clock section for "time left", a glitch interruption, tape-stop / static-crash / hard-cut ending. No brass, organ, glockenspiel, major-key lift, warm pads, hero melody, peaceful fade. Details: `skills/roblox-ost/references/hunted-vs-heroic.md`.

## 3. Study the references (numbers, not vibes)
`af.py survey <folder>` then `af.py deep <file>` for structure (drops, breakdowns, risers, impacts, fill dips, harmonic shifts, tail), `style-copy` for a family DNA. Keep fast-chase themes and the presenting style (Showtime, Fired) in separate families.

## 4. Create with a recipe
`af.py huntfight --out piece.wav [--lock ...]` picks a recipe (everything not locked is random, and avoids the last few recipes), writes `piece.wav.recipe.json`, and prints the choices. Build new composers the same way: put every creative choice in the recipe, lock only user-specified values, save the recipe next to the audio.

## 5. Verify with the analyzer, not your ears
`af.py deep piece.wav`: sections and breakdowns where designed, riser before drops, key correct, end shape (hard cut / tail), no clipping, intro quieter than the first drop. State what passed and what did not.

## 6. Get listening feedback
Use the exact prompt in `TOOLS-GUIDE/HYDROGEN-PROMPT.md`, attach the audio, paste the reply into a file, run `af.py feedback reply.txt`, then re-render with `--apply overrides.json` and the same `--seed`.

### Applying feedback to the SAME piece
`af.py feedback reply.txt --out overrides.json` -> `huntfight.py --same-as piece.wav.recipe.json --apply overrides.json`. The recipe keeps key, tempo and structure; only the fields the listener complained about change (`overrides.recipe`). If the composer code itself must change (a new voice, a new riff), change it once, note it in the changelog, and say which complaint it answers. Do not apply `mix_db` from prose-mode feedback on top of code changes that already moved the same tracks.

## 7. Deliver
Give the audio, the recipe json, what you changed, what you measured, what you could NOT verify. Offer the next single change. Package a full zip each round.

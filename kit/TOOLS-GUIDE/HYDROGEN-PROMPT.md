# Prompt for the listening AI (Hydrogen)

Use it every time. Attach the audio file (and, if the AI allows, one or two reference themes). Fill in TARGET. The JSON block at the end is what `af.py feedback` reads.

---
You are a listening assistant for a game-music producer. Listen to the attached track: an original Roblox "Last Man Standing"-style theme. I cannot hear it, so answer only from what you actually hear. Say "unsure" instead of guessing. Do not identify songs and do not search the web. Your tempo estimates are by ear and can be wrong, so give them with a confidence.

TARGET FEEL: hunted to death, last one standing. (Replace this line if the goal is different.)

PART 1 (put this FIRST so it cannot be cut off): exactly one JSON block, valid JSON with no comments, shaped like the example in PART 2.

PART 2: then a plain-language report, at most 300 words, in this order:
1. Overall mood in two sentences. Give timestamps (m:ss) for every moment that sounds happy, heroic, cozy or triumphant, and for every moment that sounds scary, desperate or hunted.
2. Key and harmony: does it feel minor and dark? Name the specific chords, melodies, key changes or pads that brighten it.
3. Instrument by instrument: drums, bass, guitars, piano, bells (and glockenspiel), strings/choir, organ, brass, synth lead, sound effects. For each: does it sound real or fake, does it fit the target, and what exactly should change.
4. Rhythm and pacing: relentless chase, or bouncy and danceable? Your BPM estimate and how sure you are.
5. The ending: does it feel like death, defeat, a win, or nothing?
6. Variation: which sections sound the same as each other, and what repeats too much.
7. If I attached reference themes: what do the references have that this track lacks? Name three things.

JSON shape (use only the allowed words where options are shown):

```json
{
  "target_feel": "hunted to death, last one standing",
  "heard_as": "hunted | desperate | tense | dark | neutral | calm | happy | heroic | triumphant",
  "mood_match_0_to_10": 0,
  "happy_or_heroic_moments": [{"time": "m:ss", "what": "..."}],
  "bright_causes": ["major chords | warm pad | bright bells | brass | rising melody | key lift | bouncy groove | peaceful ending | other: ..."],
  "tempo_estimate_bpm": 0,
  "tempo_confidence": "low | medium | high",
  "groove_feel": "relentless | driving | bouncy | laid-back | half-time",
  "ending_feels": "death | defeat | neutral | win | peaceful",
  "variation_complaints": ["..."],
  "instrument_verdicts": {
    "drums": {"sounds": "real | fake | mixed | unsure", "fits_target": true, "change": "..."},
    "bass": {}, "guitars": {}, "piano": {}, "bells": {}, "choir_strings": {}, "synth_lead": {}, "sfx": {}, "organ": {}, "brass": {}
  },
  "top_changes": [{"priority": 1, "instrument": "...", "when": "m:ss-m:ss", "change": "..."}],
  "comparison_to_references": [{"reference": "name", "has_that_this_lacks": "..."}],
  "unsure": ["..."]
}
```
Give exactly five items in top_changes, most important first, each concrete (which instrument, when, what to do).

PART 3: show me what you mean as data for your top 3 changes. Plain JSON or Python literals only, no imports or libraries, at most 25 lines each, a "confidence": "low|medium|high" on each, "guess" on anything you are guessing. Drums as 16-step grids ("x" hit, "." rest, "g" ghost), chords as names per bar, melody as [step_0_to_15, length_in_steps, note_name] for one bar, mix as {"guitars": "+3 dB"}, timeline as [{"bar": 9, "event": "drop"}]. For reference tracks use scale degrees and rhythm, never note-for-note melodies.
---

## After you get the answer
1. Save the reply to a text file (the whole reply, report and JSON).
2. `python3 skills/audio-forge/scripts/af.py feedback reply.txt --out overrides.json`
3. Read what it printed. Anything under NOT MAPPED, you apply by hand (or tell the agent).
4. `python3 skills/audio-forge/scripts/af.py huntfight --out v2.wav --seed <same seed> --apply overrides.json` repeats the same piece with only the asked changes. Leave `--seed` off to get a different piece with the same fixes.
5. Check facts yourself: a listener's mood is useful, its numbers (BPM, timestamps, durations) are not reliable. Verify with `af.py deep`.

## Notes from round 2
- The last reply was cut off in the middle of the JSON, so the JSON now comes FIRST and the report is shorter. If a reply is cut, ask for "the rest of the JSON from priority 5 onward".
- `af.py feedback` also reads the prose; it maps phrases like "heroic key lift", "stiff DnB", "arcade square", "warm choir", "bright chimes", "block guitars", "buried bass" to recipe changes (`overrides.json` -> `recipe`). Re-render with `--same-as piece.wav.recipe.json --apply overrides.json` so only those things move.

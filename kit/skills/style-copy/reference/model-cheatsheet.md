# style-copy cheat sheet (for any model, including ones that cannot hear or watch)

1. Copy the STYLE. Never the melody, lyrics, footage, characters, logos or text of the reference.
2. You cannot hear or watch. Use numbers. Never say "sounds like" or "looks like". Say what matched and what is OFF.
3. Commands, in order:
   - `copy.py list` (library first)  ->  `copy.py study REF --name N`  ->  read `styles/N/brief.md` fully
   - build: audio `af.py compose --genre G --bpm B --key K --scale S --bars N --out cand.wav` / video `analyze.py --style N` / animation: set the 2D skill's style from dna.json
   - check: `copy.py compare CAND styles/N/dna.json`
4. Each round: change ONE knob (the compare output names it). Max 5 rounds. Keep a log in styles/N/log.md.
5. Ambiguous tempo (two answers)? Ask the person which feels right.
6. Write a NEW chord progression / NEW scenes / NEW characters. Only the style carries over.
7. Anything that uploads (hear, API) or downloads: ask first.
8. Final message: numbers table, what is OFF, file paths, "I have not listened/watched: please check".

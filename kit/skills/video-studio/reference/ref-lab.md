# Ref lab: finding the best instructions for "look it up, then recreate it"

Goal: measure, not guess, which instruction makes the agent recreate a real thing (a character, a controller, a product) most accurately.

## Run it
```
python3 scripts/reftest.py init                       # makes ./reflab (subjects.json = the yes/no checks, edit them)
python3 scripts/reftest.py prompt v4-loop "Ryomen Sukuna (Jujutsu Kaisen)" --model my-model    # exact text to give the agent
#   give that text to the agent in opencode, let it finish, open its render
python3 scripts/reftest.py sheet reference.png render.png --out sheet.png   # reference and render side by side
python3 scripts/reftest.py score character v4-loop --run 1 --model my-model     # answer y/n per check (or --hits 1,0,1,...)
python3 scripts/reftest.py report                      # averages, spread, most-missed checks
```
Use a SPECIFIC subject name (full title, model number, franchise) so the search finds the right thing.

## Faster: blind A/B duels (recommended)
```
python3 reftest.py duel add v1_run1.png v1_run2.png --variant v1-baseline --model glm-5.3-flash
python3 reftest.py duel add v4_run1.png v4_run2.png --variant v4-loop --model glm-5.3-flash     # and so on
python3 reftest.py duel run --ref reference.jpeg      # shows REFERENCE | A | B, you press a, b, t (tie) or q (quit)
python3 reftest.py duel report                         # win rate per variant + head-to-head table
```
Variant names are hidden and A/B sides are random each time. Only drawings from different variants are paired. You can stop and resume any time (`duel run` continues where you left off). Judge on "which looks more like the reference", nothing else. 2 drawings per variant is enough for a first ranking; under 8 duels per variant is only a hint.

## Rules for a fair test (checks method)
- Same subject, same model, one variant per run; run each variant 3 times (results vary).
- Change one thing at a time: the variant OR the model, never both. Compare models only with the same variant.
- Score every run against the same checks, from the side-by-side sheet, before reading the next run's output.
- If the top two averages are within the spread, there is no winner yet: add runs.
- Edit `subjects.json` so the checks match the real reference for your subject (the shipped checks are generic starting points).

## Variants (`reftest.py variants`)
v1 baseline (control) - v2 look then draw - v3 written checklist, draw from it - v4 checklist + compare-and-fix loop (up to 3 rounds)
- v5 simplify on purpose (silhouette, palette, 3 signature features) - v6 part by part, checked each time - v7 three references + loop - v8 the enforced `reference-check` skill (needs it installed; the real test of the new instructions).
Other things to test with the best variant: different models (the model must accept images), output method (SVG vs Python script vs Blender), 1 vs 3 references.

## Use the result
The winning variant's text goes into the skill's "check the real thing" step. The most-missed checks tell you what to add to the checklist for that kind of subject.

# Examples: one 34-second edit, both formats

`short-9x16/build.py` and `long-16x9/build.py` are the real builds of the same 34-second take ("Everybody thinks the edit is
what makes a video blow up"), one per format. Only the code is here, not the recording. They show:
- a beat table (the words that start each beat -> its device), FIXSEQ / EMPH for the captions
- the same idea re-composed per format: photos side by side (16:9) vs stacked (9:16), paintings on one side with the words in
  the dark half (16:9) vs full frame with a soft scrim under the words (9:16)
- small explainer functions (`g_raw_edit`, `g_better`, `g_good`) built from cv_devices / cvx calls

Assets they used (in the video's assets/img/): two public-domain paintings treated with cv_treat.py (John Singer Sargent,
"Claude Monet Painting by the Edge of a Wood", 1885; Johannes Vermeer, "The Art of Painting", c. 1666-68), a frame of the raw
take, four frames of earlier edits, the painted cut-out (Rembrandt, "Self-Portrait", 1659, public domain; ready-made in
assets/examples/) and a logo. Times come from that video's work/words.json, so the phrases match only that recording.

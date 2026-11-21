# Video styles -> music recipes

Same style ids as the cinematic-edit skill. `$AF score --list-styles` prints this table. Edit `scripts/forge/styles.py` to change a recipe.

| style | genre (fallbacks) | tempo | intensity / dynamics | speech-forward | effects | bed level | for |
|---|---|---|---|---|---|---|---|
| `aesthetic-lofi` | lofi (warm_piano, synthwave) | 70-88 | 0.5 / 0.6 | no | light | -10 dB | calm aesthetic loops, study/chill, slow-mo cityscapes |
| `anime-amv` | edm (dnb, rock) | 130-174 | 0.85 / 1.2 | no | medium | -10 dB | fan edits / AMVs: fast cuts on the beat, big drops |
| `comedy-meme` | chiptune (lofi, edm) | 110-140 | 0.7 / 0.8 | yes | dense | -20 dB | comedy shorts, memes, reaction edits: fast pops, record scratches, stings |
| `cyber-tech` | synthwave (techno, edm) | 100-128 | 0.8 / 1.0 | no | medium | -12 dB | tech reveals, gadgets, AI, neon and sci-fi looks |
| `documentary` | soft_ambient (cinematic, dark_ambient) | 60-90 | 0.4 / 0.8 | yes | medium | -22 dB | found-footage documentary, essay videos, narrated explainers |
| `horror-chase` | horror_chase (metal, dark_ambient) | 150-176 | 0.85 / 1.35 | no | dense | -12 dB | Forsaken-style survival/horror chases, tension that never lets go |
| `hype-highlight` | dubstep (trap, edm, metal) | 140-150 | 0.9 / 1.25 | no | dense | -11 dB | gaming / sport kill-montages, edits that hit on every moment |
| `music-video` | - | your song | 0.8 / 1.0 | no | none | -6 dB | you bring the song, the video is cut to it (beat montage, lyric edits) |
| `news-explainer` | corporate (soft_ambient, house) | 96-118 | 0.55 / 0.7 | yes | light | -24 dB | news-style explainers, data stories, business updates |
| `product-ad` | corporate (house, synthwave) | 100-124 | 0.7 / 1.0 | no | medium | -13 dB | product films, ads, brand spots, app promos |
| `real-estate` | corporate (warm_piano, soft_ambient) | 90-110 | 0.5 / 0.8 | no | none | -14 dB | property walkthroughs, hotel and venue tours |
| `sport` | edm (rock, trap) | 126-146 | 0.85 / 1.1 | no | medium | -12 dB | sport and fitness reels |
| `talking-head` | soft_ambient (lofi, corporate) | 60-80 | 0.35 / 0.5 | yes | light | -26 dB | podcasts, interviews, explainers: voice first, bed barely there |
| `trailer` | epic_trailer (cinematic, metal) | 80-110 | 0.85 / 1.4 | no | medium | -12 dB | trailers, teasers, launch films, anything with a big reveal |
| `travel` | warm_piano (synthwave, cinematic) | 80-110 | 0.65 / 1.0 | no | light | -14 dB | travel, nature, drone and b-roll montages |
| `tutorial` | corporate (lofi, soft_ambient) | 96-116 | 0.5 / 0.6 | yes | light | -24 dB | screen recordings, how-tos, courses |
| `vlog` | warm_piano (lofi, corporate) | 70-96 | 0.6 / 0.8 | yes | light | -22 dB | daily vlogs, creator videos with talking |
| `wedding-memory` | warm_piano (soft_ambient, cinematic) | 64-84 | 0.45 / 0.9 | no | none | -10 dB | weddings, family films, tributes, slow emotional montages |

## Rules of thumb
- Speech-forward styles: bed 20-26 dB under the voice, no drums that compete with consonants (`soft_ambient`, `corporate`, `warm_piano` are built for it).
- Hype/horror/trailer: the bed's drop lands on the hero hit; the host's own risers and impacts sit on top, so keep `--sfx` off unless you want extra beat accents.
- `music-video`: no generated bed: bring the song, `bridge beatmap song.mp3`, then `bridge snap` the cuts to it.
- Same `--key`/`--bpm` across several beds of one project makes them crossfade cleanly.
- Not happy with a take? `--seed 2`, `--genre <fallback>`, `--intensity 0.6`, or `compose --override` for surgery.

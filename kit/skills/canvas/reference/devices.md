# Canvas devices: which one for which line

Every beat is ONE device. Pick it from what the line does, then from what real material exists. All of them sit in the same
type system (cv_build.say) and the same tokens (assets/tokens.css). Coordinates are frame pixels; defaults adapt to 16:9 / 9:16.

## The core look (cv_devices.py, cv_build.py helpers)
| Device | Use it when the line... | Builder |
|---|---|---|
| Face | announces an idea, turns, gives an opinion, asks, thanks | `face` |
| Painting | describes a scene, a feeling, a person in a story, or is literally about art (~5 per 10 min, no more) | `paint('p_x.jpg', 'right')` |
| Photos on paper | names a real object: a thumbnail, a photo, a frame of their video | `photos([...])` |
| The blue line | carries one thought into the next ("nobody sees / that value") | `blue_line` |
| The climbing graph | says the same rising word several times ("better and better and better"), the ball steps on each | `MG(lambda s,a,b,t: graph(...), 'dark')` |
| Painted cut-out | is about a person as the subject ("the only thing left is you") | `cutout('figure.png', ...)` |
| Quote on blue | is the punchline, a quote, a line said to themselves | `quote` |
| Real screen | names a page, an app, a price, a setting: the page with a ring drawn on the thing | `screen('key', rings=[(word, box)])` |
| Brand mark | names the creator's own brand or product | `mark('logo.png')` |
| Roadmap | lists what the video covers (first time), then opens every chapter (lights that stop) | `RM_first`, `RM(i, word)` |

## The explainers (cvx.py) — the motion graphics
| Device | Use it when the line... | Call (inside `MG(fn)`) |
|---|---|---|
| Icon flow | is a process or a sequence: "you download X, you screenshot Y, you feed it to Z" | `icons_flow(s, [(icon, label, sub, t), ...])` |
| Versus card | contrasts two things: "not your money, your attention", "$97 vs free", "by hand vs an hour". The winner lifts with an accent underline, the other dims | `versus(s, left, right, t_win, win)` |
| Tile grid | lists 2-6 parallel things: audiences, features, what it measures | `tiles(s, [(icon, label, sub, t), ...])` |
| Loop | describes a cycle: "your notes become rules, every video comes out better" | `loop(s, [(icon, label, t), ...])` |
| Bar chart | compares numbers they said (scores, prices, counts); the last or best bar in the accent | `bars(s, [(label, value, t, accent), ...])` |
| Donut | says a share or a fraction ("a third of the time", "46 of 60 minutes") | `donut(s, t, pct, label=...)` |
| Line chart | says something grows or shrinks over time ("the technology keeps getting better") | `linechart(s, pts, t0, t1, dots=...)` |
| Counter | says a number that should land with weight; ticks up on 2s | `counter(s, ticks(t0, t1, n), values, x, y)` |
| Checklist | gives steps to follow (install, setup); each box fills and checks on its word | `checklist(s, [(text, t_show, t_check), ...])` |
| Typed prompt | quotes something they typed (a prompt, a command); phrases highlight on the spoken words | `typer(s, x, y, w, h, words, marks)` |
| Receipt | lists costs line by line, with a total | `receipt(s, x, y, w, rows, total)` |
| Waveform | is about cutting the audio (silences, mistakes): their own take's waveform, the cuts collapse | `waveform(s, t, peaks, ...)` |
| File card / chip / strike / band | names a file, labels a thing, crosses something out, marks a zone | `filecard`, `chip`, `strike`, `band` |
| Video card | shows a clip playing (their own demo, a result) | `vidcard(s, src, t0, t1, media_start, ...)` |
| Head | gives a heading over any explainer (small line + italic key word) | `head(s, t, small, key)` |

Icons: any Lucide name in `assets/icons/` (video, scissors, sparkles, wallet, eye, user, monitor, gift, link, clock, check, x,
pencil, list-checks, briefcase, timer, download, image, layers, bot, terminal, credit-card, users, ...).

## Rules of thumb
- One device per beat; a new picture every ~2.4 s; no hold over ~4.5 s (a long explainer is fine if something lands every
  second: icons popping, bars growing, checks ticking).
- Never the same chart type twice in a row. Rotate grounds: paper, dark, blue, the face.
- Only the speaker's words and real numbers on screen. A device keyed to a word they didn't say (`at()` falls back to
  0.4 s into the beat) is a sign the beat is on the wrong line.
- 9:16: keep everything inside x 60-1020 and above y ~1560 (the TikTok / Reels buttons and caption sit below and on the right).

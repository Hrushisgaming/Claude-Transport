# Canvas — a free Claude Code skill

A premium minimal edit of your talking-head recordings, made in code on your own computer, in **long format (16:9, YouTube)**
or **short format (9:16, TikTok, Reels, Shorts)**. Your face announces each idea and the screen shows it: public-domain
paintings that slide in, your real photos and thumbnails dropping onto textured paper, one thick blue line your words break,
a dark graph whose glowing ball climbs a step per word, explainer motion graphics (icons that draw themselves, versus cards,
charts, checklists, a chapter roadmap), a painted figure turned into a rough blue cut-out, and your punchline as a quote on
blue. Every word blurs in exactly when you say it. It also cuts your silences and mistakes.

**Cost: $0.** No AI video, no credits, no API keys. It renders on your computer with free tools (HyperFrames, free fonts,
public-domain paintings). Your Claude plan is the only cost.

## Install (10-20 minutes, most of it downloads)
1. Download the Canvas zip. Don't unzip it.
2. Open Claude Code, start a new session. Use the best model you have (Opus 5.5 in Claude Code: type /model).
3. Open SETUP-PROMPT.txt, copy all of it, paste it into Claude Code, press Enter. Claude installs it, tests it, shows you a
   10-second preview and tells you how to use it.

## Use it (in a new Claude Code session)
- "Edit ~/Desktop/my-video.mov with canvas, long format"
- "Canvas, short format: ~/Downloads/take3.mp4"
It asks long or short first, cuts the mistakes, shows you its plan, builds, renders and opens the video. It never posts anything.

## Needs
Claude Code, Node.js 22+, Python 3.9+, ffmpeg, Google Chrome, ~3 GB of free disk while it renders. Mac (Apple Silicon is
fastest), Linux, or Windows through WSL.

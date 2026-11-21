# NextPhase Editor V3: the side silhouette edit, as a Claude Code skill

Give Claude your recording and it makes a cinematic 16:9 video: you as a backlit side-profile silhouette talking on red, blue and pale teal backdrops.

## What it makes

- **Your own silhouette**, made in Higgsfield from your real recording, so your mouth still moves on your words
- **One backdrop colour per chapter**, with the date inside your head
- **Huge words behind your head**, typed screens, counting charts, film burns, B-roll in small doses
- **Music and hard sound effects**, already in the kit

## What you need

- Claude Code, on macOS or Linux (Windows: inside WSL)
- ffmpeg and Python 3.9 to 3.13. The setup tells you if one is missing
- **A Higgsfield account with credits, connected to Claude.** The silhouette clips use about 100 credits for a 70 second video at the time this was written. Claude shows you the cost and waits for your yes. Everything else runs free on your computer

## What to record

1. One take talking to the camera. This gives the voice.
2. The same script filmed from the side. This gives the outline and the mouth.
3. If you can, some B-roll of you working at your desk, side on.

## Install

1. Download this zip and `SETUP-PROMPT (copy-paste).txt`. Don't unzip the zip.
2. Open Claude Code in any folder, paste the prompt and press Enter.
3. It installs everything and renders a short demo so you can see it works. The demo's head is a placeholder.
4. Start a new Claude Code session and say: "Make an Editor V3 video from ~/Desktop/front.mov and ~/Desktop/side.mov".

Claude never spends credits without asking, and never posts anything for you.

#!/usr/bin/env bash
# new-video.sh — start a new Canvas video from a recording, in LONG (16:9) or SHORT (9:16) format.
#
#   bash <skill>/scripts/new-video.sh <recording> --long  [name] [--dir <parent>]
#   bash <skill>/scripts/new-video.sh <recording> --short [name] [--fx 0.5] [--dir <parent>]
#
#   --long   16:9, 1920x1080 (YouTube). The default.
#   --short  9:16, 1080x1920 (TikTok, Reels, Shorts). A vertical take is scaled; a horizontal take is cropped to 9:16
#            around --fx (the speaker's face, 0 = left edge, 1 = right edge; default 0.5). Look at a frame first.
#   --dir    where videos live; default ~/canvas/videos
#
# Creates <parent>/<name>/ with
#   build.py  PLAN.md  kit.json        the template; kit.json holds the skill path and the format
#   assets/cv/                         tokens.css, canvas.css, fonts/, tex/, vendor/gsap.min.js
#   assets/icons/                      the Lucide line icons the explainer devices draw (ISC)
#   assets/media/src.<ext>             the recording (a hard link: no extra disk)
#   assets/media/cam_raw.mp4           the camera, RAW, 30 fps CFR, a keyframe a second, NO grade
#   assets/media/vo.wav                the voice, 48 kHz
#   assets/{img,clip}/  work/tx/  work/cut/  out/
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"
source "$SK/scripts/env.sh"
REC="${1:?usage: new-video.sh <recording> --long|--short [name] [--fx 0.5] [--dir parent]}"; shift
FMT="16x9"; NAME=""; PARENT="$HOME/canvas/videos"; FX="0.5"
while [ $# -gt 0 ]; do
  case "$1" in
    --long) FMT="16x9"; shift;;
    --short) FMT="9x16"; shift;;
    --fx) FX="$2"; shift 2;;
    --dir) PARENT="$2"; shift 2;;
    *) NAME="$1"; shift;;
  esac
done
[ -f "$REC" ] || { echo "new-video: no such file: $REC" >&2; exit 1; }
[ -s "$SK/assets/vendor/gsap.min.js" ] || { echo "new-video: GSAP missing: run scripts/doctor.sh first" >&2; exit 1; }
[ -s "$SK/assets/tex/paper.jpg" ] || { echo "new-video: textures missing: run scripts/doctor.sh first" >&2; exit 1; }
if [ -z "$NAME" ]; then
  base="$(basename "$REC")"; base="${base%.*}"
  NAME="$(date +%Y-%m-%d)-$(printf '%s' "$base" | tr 'A-Z' 'a-z' | tr -cs 'a-z0-9' '-' | sed 's/^-//;s/-$//' | cut -c1-40)"
  [ "$FMT" = "9x16" ] && NAME="$NAME-short"
fi
VD="$PARENT/$NAME"
[ -e "$VD" ] && { echo "new-video: $VD already exists" >&2; exit 1; }

mkdir -p "$VD"/assets/{cv,media,img,clip} "$VD"/work/{tx,cut} "$VD"/out
cp "$SK/assets/tokens.css" "$SK/assets/canvas.css" "$VD/assets/cv/"
cp -R "$SK/assets/fonts" "$SK/assets/vendor" "$SK/assets/tex" "$VD/assets/cv/"
cp -R "$SK/assets/icons" "$VD/assets/icons"
cp "$SK/template/build.py" "$SK/template/PLAN.md" "$VD/"
printf '{\n  "skill": "%s",\n  "format": "%s",\n  "created": "%s"\n}\n' "$SK" "$FMT" "$(date +%Y-%m-%d)" > "$VD/kit.json"

ext="${REC##*.}"
ln "$REC" "$VD/assets/media/src.$ext" 2>/dev/null || cp "$REC" "$VD/assets/media/src.$ext"
IFS=, read -r SW SH < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$VD/assets/media/src.$ext")
if [ "$FMT" = "16x9" ]; then
  VF="fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
elif [ "$SH" -ge "$SW" ]; then
  VF="fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
else
  # a horizontal take cropped to 9:16 around the face (fx), then scaled to 1080x1920
  VF="fps=30,crop=ih*9/16:ih:max(0\,min(iw-ih*9/16\,iw*${FX}-ih*9/32)):0,scale=1080:1920:flags=lanczos"
fi
echo "new-video: camera -> assets/media/cam_raw.mp4 ($FMT, raw, 30 fps CFR)"
ffmpeg -nostdin -v error -stats -y -i "$VD/assets/media/src.$ext" -map 0:v:0 -vf "$VF" \
  -c:v libx264 -crf 14 -preset medium -g 30 -keyint_min 30 -pix_fmt yuv420p \
  -color_range tv -colorspace bt709 -color_primaries bt709 -color_trc bt709 -an "$VD/assets/media/cam_raw.mp4"
echo "new-video: voice -> assets/media/vo.wav"
ffmpeg -nostdin -v error -y -i "$VD/assets/media/src.$ext" -map 0:a:0 -ac 2 -ar 48000 -c:a pcm_s24le "$VD/assets/media/vo.wav"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VD/assets/media/cam_raw.mp4")
echo
echo "new-video: $VD  (${D}s, $FMT)"
echo "next: \"\$CV_PY\" $SK/scripts/transcribe.py \"$VD\"  then  snap-onsets.py \"$VD\""

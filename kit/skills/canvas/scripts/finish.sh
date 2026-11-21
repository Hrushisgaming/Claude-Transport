#!/usr/bin/env bash
# finish.sh — picture + sound -> out/final.mp4 at -14 LUFS, measured, opened for review. Publishes nothing.
#
#   bash <skill>/scripts/finish.sh <video-dir> [picture.mp4]      (default picture: out/render.mp4 from render.sh)
#
# 1. lays work/premix.wav (voice + music bed, from bed-mix.py) under the silent render; with no premix, the cut voice
#    (assets/media/vo_cut.wav). Music is optional: only where the creator wants it (bed-mix.py --ramp ... -70 stops it).
# 2. lays the merged sfx-cues.txt on top (mix-sfx.py): one quiet sound per scene change, nothing per word
# 3. two-pass loudness to -14 LUFS / -1.5 dBTP (YouTube, TikTok and Reels all play around there)
# 4. prints loudness, duration and frame count, and opens the file
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"
source "$SK/scripts/env.sh"
VD="${1:?usage: finish.sh <video-dir> [picture.mp4]}"
cd "$VD"
PIC="${2:-out/render.mp4}"
[ -f "$PIC" ] || { echo "finish: no picture at $PIC (run render.sh first)" >&2; exit 1; }
AUD="work/premix.wav"; [ -f "$AUD" ] || AUD="assets/media/vo_cut.wav"
ffmpeg -nostdin -v error -y -i "$PIC" -i "$AUD" -map 0:v:0 -map 1:a:0 -c:v copy -c:a pcm_s24le out/_mux.mov
if [ -s sfx-cues.txt ]; then
  "$CV_PY" "$SK/scripts/mix-sfx.py" out/_mux.mov sfx-cues.txt out/_sfx.mp4
else
  ffmpeg -nostdin -v error -y -i out/_mux.mov -c:v copy -c:a aac -b:a 256k out/_sfx.mp4
fi
rm -f out/_mux.mov
J=$(ffmpeg -nostdin -hide_banner -i out/_sfx.mp4 -vn -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
g(){ echo "$J" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -nostdin -v error -y -i out/_sfx.mp4 -map 0:v -map 0:a -c:v copy \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(g input_i):measured_TP=$(g input_tp):measured_LRA=$(g input_lra):measured_thresh=$(g input_thresh):offset=$(g target_offset):linear=true,aresample=48000" \
  -c:a aac -b:a 256k out/final.mp4
rm -f out/_sfx.mp4
L=$(ffmpeg -nostdin -hide_banner -i out/final.mp4 -vn -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2 | awk '{print $2, $3}' | paste -sd' ' -)
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 out/final.mp4)
N=$(ffprobe -v error -count_packets -select_streams v:0 -show_entries stream=nb_read_packets -of csv=p=0 out/final.mp4)
echo "finish: out/final.mp4  ${D}s  ${N} frames  loudness / peak: $L"
case "$(uname -s)" in Darwin) open out/final.mp4 ;; Linux) (xdg-open out/final.mp4 >/dev/null 2>&1 &) ;; esac

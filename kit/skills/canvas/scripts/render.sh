#!/usr/bin/env bash
# render.sh — render every chapter of a Canvas video, frame-exact, and join them into out/render.mp4.
#
#   bash <skill>/scripts/render.sh <video-dir> [chapter-folder ...]     (no names = all chapters in work/chapters.json)
#
# Per chapter: cuts its piece of assets/cam.mp4 (frame-accurate), renders <chapter>/index.html with HyperFrames
# (2 workers, no shared frame cache: it fills small disks), checks the frame count, trims a one-frame overrun.
# Then joins all chapters with a stream copy and merges each chapter's sfx-cues.txt into one global sfx-cues.txt.
# A render that fails leaves NO old file behind to be mistaken for a new one.
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"
source "$SK/scripts/env.sh"
VD="${1:?usage: render.sh <video-dir> [chapter ...]}"; shift
cd "$VD"
[ -f work/chapters.json ] || { echo "render: run build.py first (no work/chapters.json)" >&2; exit 1; }
ALL=$(python3 -c "import json;print(' '.join(c['name'] for c in json.load(open('work/chapters.json'))))")
LIST="${*:-$ALL}"
FREE=$(df -k . | tail -1 | awk '{print int($4/1048576)}')
[ "$FREE" -lt 3 ] && echo "render: WARNING only ${FREE} GB free on this disk: renders need 1-2 GB each while they run"
for n in $LIST; do
  read -r f0 f1 < <(python3 -c "import json;c=[c for c in json.load(open('work/chapters.json')) if c['name']=='$n'][0];print(c['f0'],c['f1'])")
  k=$((f1 - f0))
  mkdir -p "$n/out" "$n/assets"
  ffmpeg -nostdin -v error -y -ss "$(python3 -c "print($f0/30)")" -i assets/cam.mp4 -frames:v $k -an -c:v libx264 -preset veryfast -crf 16 -g 30 \
    -pix_fmt yuv420p "$n/assets/cam.mp4"
  rm -f "$n/out/render.mp4" "$n/out/_new.mp4"
  (cd "$n" && hf render . -o out/_new.mp4 --workers 2 --frames-cache-dir off > ../work/render_$n.log 2>&1 < /dev/null) || true
  if [ ! -s "$n/out/_new.mp4" ]; then echo "render: $n FAILED, see work/render_$n.log"; exit 1; fi
  got=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$n/out/_new.mp4")
  if [ "$got" -gt "$k" ]; then ffmpeg -nostdin -v error -y -i "$n/out/_new.mp4" -c copy -frames:v $k "$n/out/render.mp4"; rm -f "$n/out/_new.mp4"
  else mv "$n/out/_new.mp4" "$n/out/render.mp4"; fi
  got=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$n/out/render.mp4")
  echo "render: $n  $got frames (expected $k) $([ "$got" = "$k" ] && echo OK || echo MISMATCH)"
done
: > work/concat.txt
for n in $ALL; do echo "file '../$n/out/render.mp4'" >> work/concat.txt; done
ffmpeg -nostdin -v error -y -f concat -safe 0 -i work/concat.txt -c copy -an out/render.mp4
python3 - <<'EOF'
import json
rows = []
for c in json.load(open('work/chapters.json')):
    try:
        for l in open(f"{c['name']}/sfx-cues.txt"):
            if l.strip() and not l.startswith('#'):
                t, s, g = l.split()
                rows.append((float(t) + c['f0'] / 30, s, float(g)))
    except FileNotFoundError:
        pass
rows.sort()
out, last = [], -9
for t, s, g in rows:            # one quiet sound per change: drop anything within 0.4 s of the last
    if t - last >= 0.4:
        out.append((t, s, g)); last = t
open('sfx-cues.txt', 'w').write('# global cue sheet (file starts), merged from the chapters\n' + ''.join(f'{t:.3f}  {s}  {g}\n' for t, s, g in out))
print(f'render: {len(out)} sound cues -> sfx-cues.txt')
EOF
N=$(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 out/render.mp4)
echo "render: out/render.mp4  $N frames (expected $(cat work/cut/frames.txt))"

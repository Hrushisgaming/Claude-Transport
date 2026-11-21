#!/usr/bin/env python3
"""fetch_clip.py - cut a found clip and fit it to your format (30 fps CFR, no audio, optional look).

  fetch_clip.py <url-or-file> out.mp4 [--ss 12] [--dur 1.2] [--format 9:16] [--look teal] [--speed 1] [--focus 0.5,0.5] [--zoom 1.0]
A direct video URL (find_footage 'media' field) is downloaded first (small files; HTTPS goes through your proxy settings);
a YouTube URL uses yt-dlp if installed. Rights: record the source + licence in plan.sources and FLAG anything unclear.
"""
import argparse, os, subprocess, sys, tempfile, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import FORMATS

LOOKS = {'natural': 'eq=contrast=1.08:saturation=1.02', 'mono': 'hue=s=0,eq=contrast=1.38:brightness=-0.02',
         'teal': 'eq=contrast=1.14:saturation=0.78,colorbalance=rs=-0.14:gs=-0.02:bs=0.12:rm=-0.04:bm=0.04:rh=0.06:gh=0.02:bh=-0.07',
         'warm': 'eq=contrast=1.12:saturation=0.6,colorchannelmixer=.45:.70:.18:0:.35:.62:.14:0:.22:.42:.10',
         'cold': 'eq=contrast=1.15:saturation=0.7:brightness=-0.03,colorbalance=rs=-0.10:bs=0.14:rm=-0.06:bm=0.08', 'archive': 'eq=contrast=1.10:saturation=0.9,noise=alls=9:allf=t'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--ss', type=float, default=0); ap.add_argument('--dur', type=float, default=1.2)
    ap.add_argument('--format', default='9:16'); ap.add_argument('--look', default='natural'); ap.add_argument('--speed', type=float, default=1.0)
    ap.add_argument('--focus', default='0.5,0.5'); ap.add_argument('--zoom', type=float, default=1.0); a = ap.parse_args()
    W, H = FORMATS[a.format]; fx, fy = [float(v) for v in a.focus.split(',')]; src = a.src; tmp = tempfile.mkdtemp(prefix='cefetch-')
    if src.startswith('http'):
        loc = os.path.join(tmp, 'dl.mp4')
        if 'youtube.com' in src or 'youtu.be' in src: subprocess.run(['yt-dlp', '-f', 'mp4/bv*', '-o', loc, src], check=True)
        else: urllib.request.urlretrieve(src, loc)
        src = loc
    vf = ','.join(v for v in [f'setpts=PTS/{a.speed}' if a.speed != 1 else None, f'scale=w={W}*{a.zoom}:h={H}*{a.zoom}:force_original_aspect_ratio=increase',
                              f'crop={W}:{H}:(in_w-{W})*{fx}:(in_h-{H})*{fy}', 'setsar=1', LOOKS[a.look], 'fps=30', 'format=yuv420p'] if v)
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f'{a.ss}', '-t', f'{a.dur * a.speed + 0.2}', '-i', src, '-vf', vf, '-t', f'{a.dur}', '-an', '-c:v', 'libx264',
                    '-crf', '17', '-preset', 'medium', '-g', '30', '-fps_mode', 'cfr', a.out], check=True); print('fetch_clip:', a.out)


if __name__ == '__main__':
    main()

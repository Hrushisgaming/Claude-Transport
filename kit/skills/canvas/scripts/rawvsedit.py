#!/usr/bin/env python3
"""rawvsedit.py — the "raw vs final edit" opener: a finished Canvas SHORT, played twice side by side and in sync — the cut
raw camera on the left, the finished edit on the right — each in a thin blue frame with a blue pill label on its top edge
("Raw", "Final Edit"), over paper, with the edit's REAL timeline underneath (its scenes, its voice and music waveforms) and
a playhead travelling in sync. Open a long video with it when the video is about the edit itself.

    "$CV_PY" <skill>/scripts/rawvsedit.py <finished-short-dir> <out-dir> [--left Raw --right "Final Edit"]
    then:  cd <out-dir> && npx -y hyperframes@$HF_VERSION render . -o visual.mp4 --workers 2
           ffmpeg -i visual.mp4 -i <finished-short-dir>/out/final.mp4 -map 0:v -map 1:a -c:v copy -c:a aac -shortest opener.mp4

<finished-short-dir> must be a 16:9 Canvas video that went through cut.py, build.py, render.sh and finish.sh.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, wave
import numpy as np

SK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def peaks(path, n, dur):
    w = wave.open(path)
    sr, ch = w.getframerate(), w.getnchannels()
    raw = w.readframes(w.getnframes())
    x = (np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768) if w.getsampwidth() == 2 else \
        (np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)[:, 1:].copy().view('<i2').astype(np.float32).ravel() / 32768)
    x = x.reshape(-1, ch).mean(1)[:int(dur * sr)]
    k = max(1, len(x) // n)
    p = np.array([np.abs(x[i * k:(i + 1) * k]).max() if len(x[i * k:(i + 1) * k]) else 0 for i in range(n)])
    return (p / (p.max() + 1e-9)) ** 0.7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('short'); ap.add_argument('out')
    ap.add_argument('--left', default='Raw'); ap.add_argument('--right', default='Final Edit')
    a = ap.parse_args()
    S = os.path.abspath(a.short)
    N = int(open(f'{S}/work/cut/frames.txt').read().split()[0])
    DUR = math.floor(N / 30 * 1e4) / 1e4
    os.makedirs(f'{a.out}/assets', exist_ok=True)
    if not os.path.exists(f'{a.out}/assets/cv'):
        shutil.copytree(f'{S}/assets/cv', f'{a.out}/assets/cv')
    for src, dst in ((f'{S}/assets/cam.mp4', 'raw.mp4'), (f'{S}/out/render.mp4', 'edited.mp4')):
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', src, '-vf', 'scale=1280:720:flags=lanczos', '-an', '-c:v', 'libx264',
                        '-crf', '15', '-g', '30', '-pix_fmt', 'yuv420p', f'{a.out}/assets/{dst}'], check=True)
    # the edit's real timeline: every scene clip of every chapter
    scenes = []
    for c in json.load(open(f'{S}/work/chapters.json')):
        h = open(f"{S}/{c['name']}/index.html").read()
        for st, d, src in re.findall(r'class="clip cv-layer cv-scene" data-start="([0-9.]+)" data-duration="([0-9.]+)"[^>]*><div class="cv-drift"[^>]*>'
                                     r'<div class="cv-world"[^>]*>(?:<img class="cv-ground" src="([^"]+)")?', h):
            scenes.append((float(st) + c['f0'] / 30, float(d), src or ''))
    X0, X1 = 250, 1860
    PX = (X1 - X0) / DUR
    def kind(src):
        n = os.path.basename(src)
        return ('acc', 'painting') if n.startswith('p_') else (('blu', 'quote') if 'blue' in n else (('drk', 'graph') if 'dark' in n else ('pap', 'scene')))
    blocks = ''.join(f'<div class="tb {kind(src)[0]}" style="left:{X0 + st * PX:.1f}px;width:{max(6, d * PX - 3):.1f}px"><span>{kind(src)[1]}</span></div>'
                     for st, d, src in scenes)
    NB = 230
    bw = (X1 - X0) / NB
    vo = f'{S}/assets/media/vo_cut.wav'
    tmpv = f'{a.out}/assets/_vo.wav'
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', vo, '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', tmpv], check=True)
    vp = peaks(tmpv, NB, DUR)
    bed = f'{S}/work/premix_bed.wav'
    if os.path.exists(bed):
        tmpb = f'{a.out}/assets/_bed.wav'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', bed, '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', tmpb], check=True)
        bp = peaks(tmpb, NB, DUR) * 0.55
    else:
        bp = np.zeros(NB)
    wv = lambda p: ''.join(f'<rect x="{i * bw:.1f}" y="{(1 - v) * 22:.1f}" width="{bw * 0.6:.1f}" height="{max(1.5, v * 44):.1f}"/>' for i, v in enumerate(p))
    ruler = ''.join(f'<div class="tick" style="left:{X0 + s * PX:.1f}px"><span>00:{s:02d}</span></div>' for s in range(0, int(DUR) + 1, 5))
    PW, PH, LX, RX, PY = 880, 495, 60, 980, 150
    doc = open(os.path.join(SK, 'template', 'rawvsedit.html')).read()
    for k, v in {'DUR': f'{DUR:.4f}', 'RULER': ruler, 'BLOCKS': blocks, 'WAVV': wv(vp), 'WAVB': wv(bp), 'TLW': str(X1 - X0), 'X0': str(X0),
                 'LEFT': a.left, 'RIGHT': a.right, 'PW': str(PW), 'PH': str(PH), 'PW6': str(PW - 6), 'PH6': str(PH - 6), 'LX': str(LX), 'RX': str(RX),
                 'PY': str(PY), 'LC': str(LX + PW / 2), 'RC': str(RX + PW / 2)}.items():
        doc = doc.replace('{{' + k + '}}', v)
    open(f'{a.out}/index.html', 'w').write(doc)
    print(f'rawvsedit: {a.out}/index.html  {DUR:.2f}s, {len(scenes)} scenes on the timeline')


if __name__ == '__main__':
    main()

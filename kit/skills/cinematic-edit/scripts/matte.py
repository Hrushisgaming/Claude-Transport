#!/usr/bin/env python3
"""matte.py - cut the speaker out for the cutout_world device (the world changes behind them, a huge word sits behind the head).

  matte.py --plate speaker.mp4 --start 15.5 --dur 4.4 --out matte.mp4 [--size 1080x1920] --trust-repo

Writes an ALPHA video (gray mp4: white = speaker). The device composites the live source frame with it, so no RGB is stored.
Needs PyTorch:  bash doctor.sh --install-matte   (about 1 GB, one time).
Model: Robust Video Matting (mobilenetv3) via torch.hub from github.com/PeterL1n/RobustVideoMatting (GPL-3.0, not shipped here).
torch.hub downloads and RUNS code from that repo, so you must pass --trust-repo to confirm. Pin a commit with CE_RVM_REF=<sha>.
In the plan: {"type":"cutout_world","t":15.5,"dur":4.4,"matte":"matte.mp4","matte_start":15.5,"mega":"NOBODY","images":[...]}
"""
import argparse, os, subprocess, sys
import numpy as np


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--plate', required=True); ap.add_argument('--start', type=float, required=True)
    ap.add_argument('--dur', type=float, required=True); ap.add_argument('--out', required=True); ap.add_argument('--size', default='1080x1920')
    ap.add_argument('--fps', type=int, default=30); ap.add_argument('--downsample', type=float, default=0.3); ap.add_argument('--harden', type=float, default=0.04)
    ap.add_argument('--device', default='auto', choices=['auto', 'cpu', 'mps', 'cuda']); ap.add_argument('--trust-repo', action='store_true')
    a = ap.parse_args(); W, H = [int(v) for v in a.size.split('x')]
    if not a.trust_repo: sys.exit('matte: torch.hub runs code from github.com/PeterL1n/RobustVideoMatting. Re-run with --trust-repo to confirm (pin with CE_RVM_REF).')
    try: import torch
    except ImportError: sys.exit('matte: PyTorch missing. Run: bash <skill>/scripts/doctor.sh --install-matte')
    dev = a.device if a.device != 'auto' else ('cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu'))
    model = torch.hub.load('PeterL1n/RobustVideoMatting' + (':' + os.environ['CE_RVM_REF'] if os.environ.get('CE_RVM_REF') else ''), 'mobilenetv3', trust_repo=True).eval().to(dev)
    n = int(round(a.dur * a.fps))
    dec = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-ss', f'{a.start:.4f}', '-i', a.plate, '-frames:v', str(n), '-vf', f'fps={a.fps},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
                            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-r', str(a.fps), '-i', '-', '-c:v', 'libx264', '-crf', '12',
                            '-pix_fmt', 'yuv420p', '-g', '30', a.out], stdin=subprocess.PIPE)
    rec, k = [None] * 4, 0
    with torch.no_grad():
        while True:
            buf = dec.stdout.read(W * H * 3)
            if len(buf) < W * H * 3: break
            x = torch.from_numpy(np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()).to(dev).permute(2, 0, 1)[None].float() / 255
            for _ in range(3 if k == 0 else 1): _, pha, *rec = model(x, *rec, downsample_ratio=a.downsample)
            al = pha[0, 0].clamp(0, 1).cpu().numpy()
            if a.harden > 0: al = np.clip((al - a.harden) / (1 - 2 * a.harden), 0, 1)
            enc.stdin.write((al * 255 + 0.5).astype(np.uint8).tobytes()); k += 1
            if k % 30 == 0: print(f'  {k}/{n}', file=sys.stderr)
    enc.stdin.close(); enc.wait(); dec.wait(); print(f'matte: {k} frames ({dev}) -> {a.out}  (frame 0 = source {a.start:.3f}s)')


if __name__ == '__main__':
    main()

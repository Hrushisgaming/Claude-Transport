#!/usr/bin/env python3
"""figure.py — the rough blue cut-out, from a PAINTED figure (never a frame of the speaker's own take).

    "$CV_PY" <skill>/scripts/figure.py <painting.jpg> <video-dir>/assets/img/figure.png
        -> figure.png + figure_halo.png, and prints the cut-out's size for cutout(nat=(w, h))

Pick a public-domain portrait or self-portrait from Wikimedia Commons (a head and shoulders against a plain, dark or
contrasting background mattes best; write its licence in PLAN.md). The person is cut out with Robust Video Matting
(doctor.sh --install-matte), stray islands are dropped, then cv_treat.py maps it onto the ultramarine ramp with cloth
texture, a ragged edge, a dry-brush fade at the bottom and a soft halo. A still of a talking face catches a half-blink or
an open mouth; a painted face never does.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    import torch
    dev = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
    model = torch.hub.load('PeterL1n/RobustVideoMatting', 'mobilenetv3', trust_repo=True).eval().to(dev)
    im = Image.open(src).convert('RGB')
    if im.height > 1400:
        im = im.resize((int(im.width * 1400 / im.height), 1400), Image.LANCZOS)
    rgb = np.asarray(im)
    x = torch.from_numpy(rgb).to(dev).permute(2, 0, 1)[None].float() / 255
    rec = [None] * 4
    with torch.no_grad():
        for _ in range(8):                      # a still: let the recurrent state settle on the same frame
            _, pha, *rec = model(x, *rec, downsample_ratio=0.5)
    al = pha[0, 0].clamp(0, 1).cpu().numpy()
    m = al > 0.15
    import cv2
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
    if n > 1:
        keep = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        al = np.where(lab == keep, al, 0)
    rgba = np.dstack([rgb, (al * 255).astype(np.uint8)])
    tmp = os.path.join(tempfile.mkdtemp(), 'rgba.png')
    Image.fromarray(rgba, 'RGBA').save(tmp)
    halo = out[:-4] + '_halo.png'
    r = subprocess.run([sys.executable, os.path.join(HERE, 'cv_treat.py'), 'figure', tmp, out, halo], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    f = Image.open(out)
    print(f'figure: {out}  nat=({f.width}, {f.height})  halo {halo}   -> cutout("{os.path.basename(out)}", "{os.path.basename(halo)}", nat=({f.width}, {f.height}))')


if __name__ == '__main__':
    main()

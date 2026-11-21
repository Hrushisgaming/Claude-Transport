#!/usr/bin/env python3
"""separate.py -- split a song into drums / bass / other / vocals with Demucs (OPTIONAL, ~1.5 GB: torch + model).

  python3 separate.py song.mp3 --out stems/ [--model htdemucs] [--two-stems vocals]

Install with:  bash doctor.sh --install separate     (the agent asks the user first: it is a large download)
Use the stems with:  analyze.py song.mp3 --stems stems/     (much more accurate drum pattern / bass / melody)
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("audio"); ap.add_argument("--out", default="stems"); ap.add_argument("--model", default="htdemucs")
ap.add_argument("--two-stems", help="e.g. vocals -> vocals.wav + no_vocals.wav"); ap.add_argument("--device", default="cpu")
a = ap.parse_args()
try:
    import demucs  # noqa
except Exception:
    sys.exit("demucs is not installed. It is an optional ~1.5 GB part (PyTorch). Run: bash doctor.sh --install separate")
tmp = tempfile.mkdtemp()
cmd = [sys.executable, "-m", "demucs", "-n", a.model, "-d", a.device, "-o", tmp]
if a.two_stems:
    cmd += ["--two-stems", a.two_stems]
r = subprocess.run(cmd + [a.audio])
if r.returncode:
    sys.exit("demucs failed")
src = glob.glob(os.path.join(tmp, a.model, "*"))[0]
os.makedirs(a.out, exist_ok=True)
for f in glob.glob(os.path.join(src, "*.wav")):
    shutil.move(f, os.path.join(a.out, os.path.basename(f)))
shutil.rmtree(tmp, ignore_errors=True)
print("stems ->", a.out, sorted(os.listdir(a.out)))

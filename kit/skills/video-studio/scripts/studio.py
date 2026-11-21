#!/usr/bin/env python3
"""studio.py - project helper for the video-studio skill.

  studio.py doctor                              JSON: where cinematic-edit and audio-forge are, and whether each is ready (exit 0 = cinematic-edit ready)
  studio.py new NAME --style STYLE [--source video.mp4]    create NAME/ with work/ and work/studio.json
"""
import argparse, json, os, subprocess, sys

SEARCH = ['./.opencode/skills', './.claude/skills', '~/.config/opencode/skills', '~/.claude/skills', '~/.agents/skills']


def find(name, marker):
    for s in SEARCH:
        d = os.path.join(os.path.expanduser(s), name)
        if os.path.isfile(os.path.join(d, 'SKILL.md')) and os.path.isfile(os.path.join(d, marker)): return os.path.abspath(d)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['doctor', 'new']); ap.add_argument('name', nargs='?'); ap.add_argument('--style'); ap.add_argument('--source')
    a = ap.parse_args(); ce = find('cinematic-edit', 'scripts/render.py'); af = find('audio-forge', 'scripts/af.py'); ce_ready = af_ready = False
    others = {n: find(n, 'SKILL.md') for n in ('style-copy', 'reference-check', 'canvas', 'editor-v3', '2d-animation-long-form-aivxer')}
    if ce:
        ce_ready = subprocess.run(['ffmpeg', '-version'], capture_output=True).returncode == 0 and subprocess.run([sys.executable, '-c', 'import numpy,cv2,PIL'], capture_output=True).returncode == 0
    if af:
        r = subprocess.run([sys.executable, os.path.join(af, 'scripts', 'af.py'), 'doctor', '--capabilities'], capture_output=True, text=True)
        try: af_ready = bool(json.loads(r.stdout).get('ready'))
        except Exception: pass
    if a.cmd == 'doctor':
        print(json.dumps(dict(cinematic_edit=dict(dir=ce, ready=ce_ready, fix=None if ce_ready else (f'bash {ce}/scripts/doctor.sh' if ce else 'install the kit: python3 install.py')),
                              audio_forge=dict(dir=af, ready=af_ready, fix=None if af_ready else (f'python3 {af}/scripts/af.py doctor' if af else 'optional: installed by the same kit')),
                              others=others, note='audio-forge is optional and is only used with the person\'s yes'), indent=1)); return 0 if ce_ready else 1
    if not a.name: ap.error('new needs a project NAME')
    os.makedirs(os.path.join(a.name, 'work'), exist_ok=True)
    json.dump(dict(style=a.style, source=os.path.abspath(a.source) if a.source else None, audio_forge=None), open(os.path.join(a.name, 'work', 'studio.json'), 'w'), indent=1)
    print('project ready:', a.name, '(style', a.style, ')'); return 0


if __name__ == '__main__':
    sys.exit(main())

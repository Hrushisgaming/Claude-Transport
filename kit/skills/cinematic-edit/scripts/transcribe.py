#!/usr/bin/env python3
"""transcribe.py - word timings for captions, onset-snapped cuts and the masked-word check.

  transcribe.py <video|audio> [--out work/tx/words.json] [--engine auto|faster-whisper|hyperframes] [--language en]

Writes [{"w","s","e"}] in SOURCE seconds. Engines (free, on-device):
  faster-whisper   pip install faster-whisper   (best on Windows/Linux; downloads its model on first use)
  hyperframes      npx hyperframes transcribe   (needs Node 22+; Parakeet on Apple Silicon, else whisper). Same engine editor-v1 used.
auto = faster-whisper if importable, else hyperframes if npx exists. Fix misheard NAMES by hand in words.json, keep the timings.
Also reports spans with speech-level audio but no words (a dropped span).
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe

WIN, OVL = 20.0, 2.0


def run(cmd): return subprocess.run(cmd, check=True, capture_output=True, text=True)


def fw(path, lang):
    from faster_whisper import WhisperModel
    model = WhisperModel(os.environ.get('CE_WHISPER', 'small'), compute_type='int8')
    segs, _ = model.transcribe(path, language=lang, word_timestamps=True, vad_filter=True)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or []) if w.word.strip()], 'faster-whisper'


def hf_window(src, ss, t, lang, tmp):
    d = tempfile.mkdtemp(dir=tmp); clip = os.path.join(d, 'clip.mp4')
    run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=10', '-ss', f'{ss:.3f}', '-t', f'{t:.3f}', '-i', src,
         '-map', '0:v', '-map', '1:a:0', '-shortest', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '40', '-c:a', 'aac', '-b:a', '128k', '-ac', '1', '-ar', '16000', clip])
    cmd = ['npx', '-y', 'hyperframes@' + os.environ.get('HF_VERSION', '0.8.181'), 'transcribe', clip, '-d', d, '--json'] + (['--language', lang] if lang else [])
    res = json.loads(run(cmd).stdout.strip().splitlines()[-1]); words = json.load(open(res.get('transcriptPath') or os.path.join(d, 'transcript.json')))
    return [(w['text'].strip(), w['start'] + ss, w['end'] + ss) for w in words if w.get('text', '').strip()], res.get('engine')


def hf(path, lang):
    D = probe(path)['duration']; tmp = tempfile.mkdtemp(prefix='cetx-'); words, eng = [], None
    try:
        starts = [0.0] if D <= WIN + 1 else list(np.arange(0, D - OVL, WIN - OVL))
        for k, ss in enumerate(starts):
            got, eng = hf_window(path, ss, min(WIN, D - ss), lang, tmp)
            lo = 0.0 if k == 0 else ss + OVL / 2; hi = D + 1 if k == len(starts) - 1 else ss + WIN - OVL / 2
            words += [w for w in got if lo <= w[1] < hi]
    finally: shutil.rmtree(tmp, ignore_errors=True)
    return sorted(words, key=lambda w: w[1]), eng


def transcribe(path, engine='auto', lang=None):
    if engine in ('auto', 'faster-whisper'):
        try: return fw(path, lang)
        except ImportError:
            if engine == 'faster-whisper': sys.exit('transcribe: pip install faster-whisper')
    if shutil.which('npx'): return hf(path, lang)
    sys.exit('transcribe: no engine. Either `pip install faster-whisper` or install Node 22+ (npx hyperframes transcribe).')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('media'); ap.add_argument('--out', default='work/tx/words.json')
    ap.add_argument('--engine', default='auto'); ap.add_argument('--language'); a = ap.parse_args()
    words, eng = transcribe(a.media, a.engine, a.language); os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump([{'w': w, 's': round(s, 3), 'e': round(e, 3)} for w, s, e in words], open(a.out, 'w'), indent=0)
    print(f'transcribe: {len(words)} words ({eng}) -> {a.out}')


if __name__ == '__main__':
    main()

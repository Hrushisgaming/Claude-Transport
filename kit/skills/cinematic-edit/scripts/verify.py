#!/usr/bin/env python3
"""verify.py - did a hit, riser or the music bed MASK a word? Re-transcribe the final video and diff it against the take.

  verify.py final.mp4 work/tx/words.json [--engine auto]        (or: --found other_words.json to skip transcribing)
Prints words in the take that the final no longer has, with times. A masked name ("Claude did" -> "Flaw dead") shows up here.
Fix: lower sfx_db, move the impact off the word, or shorten the riser.  Exit 1 if words are missing.
"""
import argparse, difflib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())


def diff(take, found, tol=0.0):
    a = [(norm(x['w']), x['s']) for x in take if norm(x['w'])]; b = [norm(x['w']) for x in found if norm(x['w'])]
    sm = difflib.SequenceMatcher(None, [w for w, _ in a], b, autojunk=False); bad = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ('replace', 'delete'): bad.append((a[i1][1], ' '.join(w for w, _ in a[i1:i2]), ' '.join(b[j1:j2])))
    return bad, sm.ratio()


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('final'); ap.add_argument('words'); ap.add_argument('--engine', default='auto'); ap.add_argument('--found')
    a = ap.parse_args(); take = json.load(open(a.words))
    if a.found: found = json.load(open(a.found))
    else:
        import transcribe; w, _ = transcribe.transcribe(a.final, a.engine); found = [dict(w=x, s=s, e=e) for x, s, e in w]
    bad, r = diff(take, found); print(f'verify: {len(take)} words in the take, similarity {r:.2f}')
    for t, was, now in bad: print(f"  MASKED? {t:7.2f}s  take: '{was}'  final: '{now or '(missing)'}'")
    print('verify: ' + ('every word survived' if not bad else f'{len(bad)} span(s) changed: listen at those times')); sys.exit(1 if bad else 0)

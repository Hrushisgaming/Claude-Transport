#!/usr/bin/env python3
"""plancheck.py - the plan you show the person, and the rights gate before a final render.

  plancheck.py plan.json [--md PLAN.md]

Writes PLAN.md (arc, events, devices, overlays, SOURCES with licences and FLAGs) and exits 1 when
something is undeclared or flagged-but-not-approved. render.py refuses a FINAL render until this passes
(--preview always works; --force-rights overrides, only when the person has decided).

plan["sources"] = [{"id":"s1","what":"drip close-up","path":"assets/drip.mp4","url":"https://...","licence":"Mixkit free licence",
                    "flag":false,"approved":false,"note":"..."}]
Used assets: music, every device image, the matte plate. The main "source" is treated as the person's own upload.
FLAG = unclear rights (a company's film, a news photo, someone else's clip, game footage). The person sets "approved": true.
"""
import json, os, sys


def _synth(plan):
    """the bed was synthesised on this machine by audio-forge (original, no third-party rights)"""
    af = plan.get('audio_forge') or {}
    return bool(af.get('bed') and plan.get('music') and os.path.abspath(os.path.join(plan.get('_dir', '.'), plan['music'])) == os.path.abspath(af['bed']) and af.get('synthesised'))


def used_assets(plan):
    a = []
    if plan.get('music') and not _synth(plan): a.append(('music', plan['music']))
    for i, d in enumerate(plan.get('devices', [])):
        for im in d.get('images', []):
            a.append((f"device {i + 1} ({d['type']})", im if isinstance(im, str) else im['path']))
    return a


def check(plan):
    base = plan.get('_dir', '.'); src = {os.path.abspath(os.path.join(base, s['path'])): s for s in plan.get('sources', []) if s.get('path')}
    byid = {s['id']: s for s in plan.get('sources', []) if s.get('id')}
    rows, problems = [], []
    rows.append(('main footage', plan.get('source', ''), 'your upload', 'OK: your rights'))
    if _synth(plan): rows.append(('music bed', plan['music'], 'synthesised by audio-forge: original, no third-party rights', 'OK'))
    seen = set()
    for where, p in used_assets(plan):
        if (where.split(' (')[0], p) in seen: continue
        seen.add((where.split(' (')[0], p))
        s = src.get(os.path.abspath(os.path.join(base, p)))
        if not s: rows.append((where, p, '-', 'UNDECLARED')); problems.append(f'{where}: {p} has no entry in sources'); continue
        lic = s.get('licence', '')
        if not lic: st = 'NO LICENCE'; problems.append(f'{where}: {p} has no licence recorded')
        elif s.get('flag') and not s.get('approved'): st = 'FLAG: needs your decision'; problems.append(f"{where}: {p} is FLAGGED ({s.get('note', lic)}) and not approved")
        elif s.get('flag'): st = 'FLAG: approved by you'
        else: st = 'OK'
        rows.append((where, p, lic or '-', st))
    # facts shown on screen must be verified (reference-check skill logs them in work/refs.json)
    rp = os.path.join(plan.get('_dir', '.'), 'work', 'refs.json')
    if os.path.exists(rp):
        try:
            for c in json.load(open(rp)).get('claims', []):
                if c.get('on_screen') and not c.get('verified'): problems.append(f"fact shown on screen is UNVERIFIED: {c.get('claim')} (verify it with a source, or remove it from the video)")
        except Exception: pass
    return rows, problems


def facts_table(plan):
    rp = os.path.join(plan.get('_dir', '.'), 'work', 'refs.json')
    if not os.path.exists(rp): return []
    try: cl = json.load(open(rp)).get('claims', [])
    except Exception: return []
    if not cl: return []
    import datetime
    L = ['', '## Checked facts', '', '| claim | source | verified | on screen | date | flag |', '|---|---|---|---|---|---|']
    for c in cl:
        age = (datetime.date.today() - datetime.date.fromisoformat(c['date'])).days
        L.append(f"| {c['claim']} | {c['source']} | {'yes' if c['verified'] else 'NO'} | {'yes' if c.get('on_screen') else 'no'} | {c['date']} | {'UNVERIFIED' if not c['verified'] else 'stale: re-check' if age > 30 else 'ok'} |")
    return L


def markdown(plan, rows, problems):
    L = ['# PLAN', '', f"Source: `{plan.get('source')}`  |  format {plan.get('format')}  |  {plan.get('dur')} s from {plan.get('start', 0)} s", '', '## Arc', '| t (s) | act | look | drone | heart BPM |', '|---|---|---|---|---|']
    L += [f"| {a['t']} | {a['name']} | {a.get('look')} | {a.get('drone')} | {a.get('heart_bpm')} |" for a in plan.get('acts', [])]
    L += ['', '## Events (what hits)', '| t (s) | strength | fx | sfx | riser | ramp |', '|---|---|---|---|---|---|']
    L += [f"| {e['t']} | {e.get('strength')} | {', '.join(e.get('fx', []))} | {e.get('sfx', '')} | {e.get('riser', '')} | {e.get('ramp', '')} |" for e in plan.get('events', [])]
    L += ['', '## Devices', '| t (s) | device | dur | images |', '|---|---|---|---|']
    L += [f"| {d['t']} | {d['type']} | {d.get('dur', 'auto')} | {len(d.get('images', []))} |" for d in plan.get('devices', [])]
    L += ['', '## Overlays', '| t (s) | type | text |', '|---|---|---|'] + [f"| {o['t']} | {o['type']} | {o['text']} |" for o in plan.get('overlays', [])]
    L += ['', '## Sources and rights', '| used for | file | licence | status |', '|---|---|---|---|'] + [f'| {r[0]} | {r[1]} | {r[2]} | {r[3]} |' for r in rows]
    L += facts_table(plan)
    L += ['', '**Gate: ' + ('PASS' if not problems else 'BLOCKED') + '**'] + [f'- {p}' for p in problems]
    L += ['', 'The final call on what goes into a published video is yours. Nothing is uploaded or posted by this skill.']
    return '\n'.join(L) + '\n'


def gate(plan, strict, quiet=False):
    rows, problems = check(plan)
    if problems:
        msg = 'rights/sources check:\n  ' + '\n  '.join(problems)
        if strict: sys.exit(msg + '\nrender: final render blocked. Fix sources (or set approved:true after the person decides); --preview still works.')
        if not quiet: print('WARNING ' + msg, file=sys.stderr)
    return rows, problems


if __name__ == '__main__':
    p = sys.argv[1]; plan = json.load(open(p)); plan['_dir'] = os.path.dirname(os.path.abspath(p))
    rows, problems = check(plan); md = markdown(plan, rows, problems)
    if '--md' in sys.argv: open(sys.argv[sys.argv.index('--md') + 1], 'w').write(md)
    print(md); sys.exit(1 if problems else 0)

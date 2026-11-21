#!/usr/bin/env python3
"""audioforge.py - the bridge between cinematic-edit and the audio-forge skill (free, local music / voice / sound effects).

  audioforge.py detect                          is audio-forge installed and ready?  (JSON; exit 0 only when ready)
  audioforge.py state [--set yes|partial|no|later] [--parts bed,sfx,voice]    the person's answer, kept in work/audio-forge.json
  audioforge.py brief plan.json [--shots work/shots.json] [--out work/af/brief.json]    what the edit looks like, in OUTPUT seconds
  audioforge.py score plan.json [--seed 1] [--genre G] [--bpm B] [--sfx] [--apply]      compose a bed that fits the edit
  audioforge.py sfx NAME [NAME ...] [--dir work/sfx]                                    synthesise sound effects
  audioforge.py cue plan.json --at 3.2 --sfx record_scratch [--gain 0.9] [--apply]      add one effect to the plan's cue sheet
  audioforge.py voice plan.json --subs lines.srt --yes-confirmed [--engine E --voice V] subtitles -> a voice track (needs the person's OK)
  audioforge.py clean-voice in.wav out.wav                                              rumble cut, denoise, even out, -16 LUFS

Nothing here edits plan.json unless you pass --apply (without it, a patched copy plan.scored.json is written and the change is
printed). The person decides. The bed is synthesised on this machine: original, no third-party rights (plancheck knows).
Rules that always hold: ask before using audio-forge; ask before any optional download; confirm before turning subtitles into speech.
"""
import argparse, json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import TimeMap

SEARCH = ['./.opencode/skills', './.claude/skills', '~/.config/opencode/skills', '~/.claude/skills', '~/.agents/skills']


def find_af():
    env = os.environ.get('AUDIO_FORGE_DIR')
    for d in ([env] if env else []) + [os.path.join(os.path.expanduser(s), 'audio-forge') for s in SEARCH]:
        if d and os.path.isfile(os.path.join(d, 'SKILL.md')) and os.path.isfile(os.path.join(d, 'scripts', 'af.py')): return os.path.abspath(d)
    return None


def af(*args, check=True):
    d = find_af()
    if not d: sys.exit('audio-forge is not installed (free, local: python3 install.py from its package). Continue without it, or install it first.')
    r = subprocess.run([sys.executable, os.path.join(d, 'scripts', 'af.py')] + [str(x) for x in args], capture_output=True, text=True)
    if check and r.returncode: sys.exit(f'audio-forge {args[0]} failed:\n' + (r.stderr or r.stdout)[-1200:])
    return r


def load(p): return json.load(open(p))


def intensity(a):
    d = float(a.get('drone', 0.3)); hb = float(a.get('heart_bpm', 0) or 0)
    return round(min(1.0, d * 0.7 + max(0.0, (hb - 50) / 80) * 0.3 if hb else d), 3)


def make_brief(plan, shots=None):
    plan = dict(plan); tm = TimeMap(plan); st = tm.start
    acts = [dict(name=a.get('name', ''), t=round(float(tm.to_out(a['t'] + st)), 3), intensity=intensity(a)) for a in sorted(plan.get('acts', []), key=lambda a: a['t'])]
    ev = [dict(t=round(float(tm.to_out(e['t'])), 3), strength=float(e.get('strength', 0.7)), kind=e.get('sfx') or 'tick') for e in plan.get('events', [])]
    cuts = []
    if shots and os.path.exists(shots):
        t0 = [s[0] if isinstance(s, list) else s['t0'] for s in load(shots)]
        cuts = [round(float(x), 3) for x in tm.to_out(np.array(t0) + st) if 0 <= x <= tm.D_out]
    speech = bool(plan.get('captions')) or plan.get('audio', {}).get('mode') == 'voice'
    return dict(schema='audio-forge/scorebrief@1', duration=round(tm.D_out, 3), style=plan.get('style'), acts=acts, events=ev, cuts=cuts, speech=speech)


def write_plan(plan_path, patch, apply):
    plan = load(plan_path); new = json.loads(json.dumps(plan))
    for k, v in patch.items():
        if isinstance(v, dict) and isinstance(new.get(k), dict): new[k].update(v)
        else: new[k] = v
    out = plan_path if apply else os.path.splitext(plan_path)[0] + '.scored.json'
    json.dump(new, open(out, 'w'), indent=1)
    print(('plan UPDATED: ' if apply else 'wrote a patched copy (your plan is unchanged): ') + out); print('change:', json.dumps(patch, indent=1))
    if not apply: print('apply with --apply, or render from the copy: render.py ' + out + ' out --preview')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['detect', 'state', 'brief', 'score', 'sfx', 'cue', 'voice', 'clean-voice']); ap.add_argument('args', nargs='*')
    ap.add_argument('--set'); ap.add_argument('--parts'); ap.add_argument('--shots'); ap.add_argument('--out'); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--genre'); ap.add_argument('--bpm', type=float); ap.add_argument('--sfx', nargs='?', const=True, default=False); ap.add_argument('--apply', action='store_true')
    ap.add_argument('--dir', default='work/sfx'); ap.add_argument('--at', type=float); ap.add_argument('--gain', type=float, default=0.9)
    ap.add_argument('--subs'); ap.add_argument('--engine'); ap.add_argument('--voice'); ap.add_argument('--yes-confirmed', action='store_true')
    ap.add_argument('--state', default='work/audio-forge.json'); ap.add_argument('--key'); ap.add_argument('--intensity', type=float)
    a = ap.parse_args()
    if a.cmd == 'detect':
        d = find_af()
        if not d: print(json.dumps(dict(found=False, hint='free + local: python3 install.py from the AudioForge package'))); return 1
        r = af('doctor', '--capabilities', check=False)
        try: caps = json.loads(r.stdout)
        except Exception: caps = {}
        print(json.dumps(dict(found=True, dir=d, ready=bool(caps.get('ready')), version=caps.get('version'), provides=caps.get('provides'), styles=caps.get('styles'),
                              fix=None if caps.get('ready') else f'python3 {d}/scripts/af.py doctor'), indent=1)); return 0 if caps.get('ready') else 2
    if a.cmd == 'state':
        if a.set:
            os.makedirs(os.path.dirname(os.path.abspath(a.state)) or '.', exist_ok=True); json.dump(dict(use=a.set, parts=[p for p in (a.parts or '').split(',') if p]), open(a.state, 'w'))
        print(open(a.state).read() if os.path.exists(a.state) else json.dumps(dict(use=None))); return 0
    if a.cmd == 'clean-voice':
        af('audio_edit', 'voice', a.args[0], a.args[1]); print('clean voice ->', a.args[1]); return 0
    if a.cmd == 'sfx':
        os.makedirs(a.dir, exist_ok=True)
        for n in a.args: af('sfx', '--name', n, '--out', os.path.join(a.dir, n + '.wav')); print('sfx', n, '->', os.path.join(a.dir, n + '.wav'))
        return 0
    plan_path = a.args[0]; plan = load(plan_path); plan['_dir'] = os.path.dirname(os.path.abspath(plan_path)); wd = os.path.join(plan['_dir'], 'work')
    if a.cmd == 'brief':
        out = a.out or os.path.join(wd, 'af', 'brief.json'); os.makedirs(os.path.dirname(out), exist_ok=True)
        b = make_brief(plan, a.shots or os.path.join(wd, 'shots.json')); json.dump(b, open(out, 'w'), indent=1); print(f"brief -> {out}  ({b['duration']}s, {len(b['acts'])} acts, {len(b['events'])} events, {len(b['cuts'])} cuts)"); return 0
    if a.cmd == 'score':
        od = os.path.join(wd, 'af'); os.makedirs(od, exist_ok=True); brief = os.path.join(od, 'brief.json')
        json.dump(make_brief(plan, os.path.join(wd, 'shots.json')), open(brief, 'w'), indent=1); bed = os.path.join(od, f'bed_s{a.seed}.wav')
        args = ['score', '--brief', brief, '--out', bed, '--seed', a.seed] + (['--style', plan['style']] if plan.get('style') else [])
        for flag, v in (('--genre', a.genre), ('--bpm', a.bpm), ('--key', a.key), ('--intensity', a.intensity)):
            if v is not None: args += [flag, v]
        if a.sfx: args.append('--sfx')
        r = af(*args); res = json.loads(r.stdout)
        print(f"bed: {res['genre']} {res['bpm']} BPM {res['key']} {res['scale']}  {res['bed_seconds']}s  drop at {res['drop_start_s']}s (hero moment {res['hero_s']}s, error {res['drop_error_ms']} ms)")
        for n in res['notes']: print('  -', n)
        rel = lambda p: os.path.relpath(p, plan['_dir'])
        patch = dict(music=rel(bed), music_start=0.0, audio_forge=dict(bed=bed, beatmap=res['beatmap'], genre=res['genre'], bpm=res['bpm'], seed=a.seed, score=bed + '.score.json', synthesised=True))
        if res.get('cues'): patch['sfx_cues'] = rel(res['cues'])
        print('NOTE: I have not listened to this bed; audition it (open', bed + ') and try --seed 2, 3 or --genre for another take.')
        write_plan(plan_path, patch, a.apply); return 0
    if a.cmd == 'cue':
        os.makedirs(a.dir, exist_ok=True); n = a.sfx if isinstance(a.sfx, str) else 'impact'; wp = os.path.abspath(os.path.join(a.dir, n + '.wav'))
        if not os.path.exists(wp): af('sfx', '--name', n, '--out', wp)
        sheet = os.path.join(wd, 'cues.txt'); os.makedirs(wd, exist_ok=True)
        with open(sheet, 'a') as f: f.write(f'{a.at:.3f} {wp} {a.gain:.2f}\n')
        write_plan(plan_path, dict(sfx_cues=os.path.relpath(sheet, plan['_dir'])), a.apply); return 0
    if a.cmd == 'voice':
        if not a.subs: sys.exit('voice: --subs file.srt is required')
        if not a.yes_confirmed: sys.exit('voice: the person must confirm first: speak the subtitles aloud? replace the original audio, keep it underneath, or a separate voice file? which voice? Re-run with --yes-confirmed after they answer.')
        od = os.path.join(wd, 'af'); os.makedirs(od, exist_ok=True); out = os.path.join(od, 'voice.wav')
        args = ['subs2speech', a.subs, '--duration', round(TimeMap(plan).D_out, 2), '--out', out] + (['--engine', a.engine] if a.engine else []) + (['--voice', a.voice] if a.voice else [])
        r = af(*args); print(r.stdout[-600:]); print('read', out + '.fit.json', 'to the person: lines that did not fit their slot are listed there.')
        write_plan(plan_path, dict(voice=os.path.relpath(out, plan['_dir']), voice_at=0.0, audio=dict(mode='voice')), a.apply); return 0


if __name__ == '__main__':
    sys.exit(main())

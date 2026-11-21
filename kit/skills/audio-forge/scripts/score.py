#!/usr/bin/env python3
"""score.py -- one-shot soundtrack for a video: reads what the edit looks like, composes an ORIGINAL bed whose structure
follows the video's acts and whose big drop lands on the video's biggest moment.

  af.py score --brief brief.json --out work/bed.wav                      # brief written by a video editor (see below)
  af.py score --duration 45 --style trailer --hero 31.2 --out bed.wav    # no brief: just a length, a style, an optional hero time
  af.py score --plan plan.json --out bed.wav                             # a cinematic-edit plan.json (speed ramps are NOT accounted for)
  af.py score --list-styles

Options: --style S (see --list-styles; default from the brief)  --genre G (overrides the style's genre)  --seed N  --bpm B
         --key K --scale S  --intensity X  --sfx (also write a beat-accent cue sheet <out>.cues.txt)  --no-tune (do not nudge tempo)  --exact [--fade S] (end exactly at the video length with a fade-out)

Brief (schema audio-forge/scorebrief@1, all times are VIDEO seconds after speed ramps):
  {"schema":"audio-forge/scorebrief@1","duration":42.3,"style":"hype-highlight",
   "acts":[{"name":"calm","t":0,"intensity":0.1},{"name":"finale","t":30,"intensity":1.0}],
   "events":[{"t":31.2,"strength":1.0,"kind":"impact"}], "cuts":[0,2.1,4.4], "speech":false}

Method: acts -> sections (quiet start = intro, the act before the peak = build, the most intense act = drop/climax, quiet end =
outro). The tempo is nudged (never more than +-10 percent, never outside the genre's useful range) so that a whole number of bars
precedes the hero moment, which puts the drop ON it. If the cuts already follow a grid, that tempo is preferred.
Writes <out>, <out>.beatmap.json, <out>.score.json (audio-forge/score@1: bpm, sections in video time, where the drop landed, hints).
"""
import argparse, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from forge import genres, song as songmod, styles as stylemod

BRIEF = "audio-forge/scorebrief@1"


def brief_from_plan(plan, dur=None):
    """Cheap conversion of a cinematic-edit plan.json (source seconds, no ramp stretch). Prefer the editor's own brief."""
    start = float(plan.get("start", 0)); D = float(dur or plan.get("dur", 30))
    warn = []
    if any(e.get("ramp") for e in plan.get("events", [])):
        warn.append("plan has speed ramps: times here are source seconds; cinematic-edit's audioforge.py writes an exact brief")
    acts = [dict(name=a.get("name", ""), t=max(0.0, float(a["t"])), intensity=float(a.get("drone", 0.3)) * 0.6 + (float(a.get("heart_bpm", 60)) - 50) / 80 * 0.4)
            for a in plan.get("acts", [])]
    ev = [dict(t=float(e["t"]) - start, strength=float(e.get("strength", 0.7)), kind=e.get("sfx", "tick")) for e in plan.get("events", [])]
    return dict(schema=BRIEF, duration=D, style=plan.get("style"), acts=acts, events=ev, speech=bool(plan.get("captions")), _warn=warn)


def pick_tempo(bpm_lo, bpm_hi, base, hero_t, tune, cuts):
    """-> (bpm, tuned?, note). Prefer the cut grid if it fits well, then tune so N whole bars precede hero_t."""
    note = ""
    if cuts and len(cuts) >= 8:
        import bridge
        try:
            fit = bridge.fit_tempo([[c, c, ""] for c in cuts], lo=max(60, int(bpm_lo * 0.9)), hi=int(bpm_hi * 1.1))[0]
            if fit["alignment"] >= 0.55:
                base = fit["bpm"]; note = f"cuts follow a {fit['bpm']} BPM grid (alignment {fit['alignment']}); using it"
        except Exception:
            pass
    bpm = float(base)
    if tune and hero_t and hero_t > 4:
        bar = 240.0 / bpm; B = max(2, int(round(hero_t / bar)))
        b2 = 240.0 * B / hero_t
        if abs(b2 - bpm) / bpm <= 0.10 and bpm_lo * 0.9 <= b2 <= bpm_hi * 1.1:
            return round(b2, 3), True, (note + "; " if note else "") + f"tempo nudged {bpm:.1f}->{b2:.2f} so {B} bars end exactly on the hero moment"
        note = (note + "; " if note else "") + f"could not tune within 10% ({b2:.1f} BPM needed); drop lands within half a bar of the hero moment instead"
    return round(bpm, 3), False, note


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief"); ap.add_argument("--plan"); ap.add_argument("--duration", type=float); ap.add_argument("--hero", type=float)
    ap.add_argument("--style"); ap.add_argument("--genre"); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--bpm", type=float)
    ap.add_argument("--key"); ap.add_argument("--scale"); ap.add_argument("--intensity", type=float); ap.add_argument("--sfx", action="store_true")
    ap.add_argument("--no-tune", action="store_true"); ap.add_argument("--out", default="bed.wav"); ap.add_argument("--list-styles", action="store_true")
    ap.add_argument("--tail", type=float, default=3.0, help="extra seconds of bed after the video ends (default 3)")
    ap.add_argument("--exact", action="store_true", help="cut the bed to exactly the video length with a fade-out (no manual trimming needed)")
    ap.add_argument("--fade", type=float, default=1.5, help="fade-out seconds for --exact (default 1.5)")
    a = ap.parse_args()
    if a.list_styles:
        for k, v in sorted(stylemod.STYLES.items()):
            print(f"{k:16s} {str(v['genre']):13s} {v['about']}")
        return 0
    if a.brief:
        brief = json.load(open(a.brief))
        if not str(brief.get("schema", "")).startswith("audio-forge/scorebrief@"):
            raise SystemExit("brief.schema must start with audio-forge/scorebrief@")
    elif a.plan:
        brief = brief_from_plan(json.load(open(a.plan)))
    elif a.duration:
        brief = dict(schema=BRIEF, duration=a.duration, acts=[], events=[])
    else:
        ap.error("give --brief, --plan or --duration")
    notes = list(brief.pop("_warn", []))
    D = float(brief["duration"]); sname, st = stylemod.get(a.style or brief.get("style") or "trailer")
    genre = a.genre or st["genre"]
    if not genre:
        raise SystemExit(f"style '{sname}' has no generated music: bring your own song, then use `bridge beatmap song.mp3` and `bridge snap`.")
    G = genres.resolve(genre); spec = genres.GENRES[G]
    acts = brief.get("acts") or []
    events = sorted(brief.get("events") or [], key=lambda e: -float(e.get("strength", 0)))
    if not acts:   # no arc given: calm start, peak at the hero (or 70% in), short release
        hero = a.hero or (events[0]["t"] if events else 0.7 * D)
        acts = [dict(name="open", t=0, intensity=0.25), dict(name="build", t=max(0.5, hero - 0.25 * D), intensity=0.55),
                dict(name="peak", t=hero, intensity=1.0), dict(name="release", t=min(D - 1, hero + 0.22 * D), intensity=0.3)]
        acts = [x for x in acts if x["t"] < D - 0.5]
    secs, peak_i = stylemod.acts_to_sections(acts, D, st["peak"])
    peak_sec = next(i for i, s in enumerate(secs) if s[0] == st["peak"]) if any(s[0] == st["peak"] for s in secs) else len(secs) - 1
    # hero moment: strongest event inside the peak section, else the peak section start
    ps, pe = secs[peak_sec][1], secs[peak_sec][2]
    inside = [e for e in events if ps - 1.0 <= float(e["t"]) <= pe]
    hero_t = a.hero or (float(inside[0]["t"]) if inside else ps)
    if hero_t < 4 or secs[peak_sec][1] < 4:
        hero_t = ps if ps >= 4 else 0
    lo, hi = spec["bpm"]; base = a.bpm or (st["bpm"][0] + st["bpm"][1]) / 2 if st["bpm"][1] else (lo + hi) / 2
    base = min(max(base, lo), hi) if not a.bpm else a.bpm
    cuts = brief.get("cuts") or []
    bpm, tuned, tnote = pick_tempo(lo, hi, base, hero_t, tune=(not a.no_tune and not a.bpm), cuts=cuts)
    if tnote: notes.append(tnote)
    bar_s = 240.0 / bpm
    total_bars = int(math.ceil((D + a.tail) / bar_s)) + 1
    # bars for each section: pre-peak sections share exactly round(hero_t/bar) bars when tuned
    names = [s[0] for s in secs]; durs = [max(0.1, s[2] - s[1]) for s in secs]
    bars = [max(1, int(round(d / bar_s))) for d in durs]
    if tuned and peak_sec > 0:
        B = int(round(hero_t / bar_s)); pre = durs[:peak_sec]
        # the peak section may START before the hero event (hero inside it): keep the drop on hero by letting pre-sections fill B bars
        scale = B / max(sum(pre), 1e-6); raw = [d * scale / bar_s * bar_s for d in pre]
        tot_raw = sum(pre); alloc = [max(1, int(B * d / tot_raw)) for d in pre]
        while sum(alloc) < B: alloc[max(range(len(alloc)), key=lambda i: B * pre[i] / tot_raw - alloc[i])] += 1
        while sum(alloc) > B and max(alloc) > 1: alloc[alloc.index(max(alloc))] -= 1
        bars[:peak_sec] = alloc
    used = sum(bars)
    if used < total_bars: bars[-1] += total_bars - used               # last section absorbs the tail
    elif used > total_bars: total_bars = used
    # genres.make_plan needs every section >= 2 bars once the song is >= 16 bars: lend bars from the longest section
    if total_bars >= 16:
        for i in range(len(bars)):
            while bars[i] < 2:
                j = max(range(len(bars)), key=lambda k: bars[k]); bars[j] -= 1; bars[i] += 1
    plan = [(n, b / total_bars) for n, b in zip(names, bars)]
    inten = a.intensity if a.intensity is not None else st["intensity"]
    s = genres.build(genre, total_bars, bpm, a.key, a.scale, a.seed, inten, None, plan, None)
    audio = s.mixdown(master=True, reverb_rt60=s.rt60, dynamics=st["dynamics"])
    if a.exact:                                                      # end exactly with the video, with a short fade so there is no click
        n = min(len(audio), int(round(D * s.sr))); audio = audio[:n].copy(); f = min(n, int(a.fade * s.sr))
        if f > 1: audio[n - f:] = audio[n - f:] * (np.linspace(1.0, 0.0, f) ** 1.5).reshape((-1,) + (1,) * (audio.ndim - 1))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    songmod.write_wav(a.out, audio, s.sr)
    bm = s.beatmap(); bm["meta"] = s.meta
    json.dump(bm, open(a.out + ".beatmap.json", "w"), indent=1)
    # where did the peak section really start?
    actual = None
    peak_nm = names[peak_sec]
    ps_names = [x["name"] for x in bm["sections"]]
    cum = 0; start_bar = sum(bars[:peak_sec])
    actual = start_bar * bar_s
    err_ms = None if not hero_t else round((actual - hero_t) * 1000, 1)
    sections = []
    t = 0.0
    for n, b, srcsec in zip(names, bars, secs):
        sections.append(dict(name=n.rstrip("_"), start=round(t, 3), end=round(t + b * bar_s, 3), act=srcsec[3])); t += b * bar_s
    notes.append(f"{genre} at {bpm:.1f} BPM, {total_bars} bars ({total_bars * bar_s:.1f}s) for a {D:.1f}s video; seed {a.seed}")
    if err_ms is not None and abs(err_ms) > 150: notes.append(f"the drop starts {err_ms:+.0f} ms from the hero moment: use --seed, --bpm or shift the bed with the editor's music_start")
    res = dict(schema="audio-forge/score@1", bed=os.path.abspath(a.out), beatmap=os.path.abspath(a.out + ".beatmap.json"), style=sname, genre=G,
               bpm=bpm, key=s.meta["key"], scale=s.meta["scale"], seed=a.seed, intensity=inten, bed_seconds=round(len(audio) / s.sr, 2), song_at=0.0,
               tempo_tuned=tuned, hero_s=round(hero_t, 3) if hero_t else None, drop_start_s=round(actual, 3), drop_error_ms=err_ms,
               sections=sections, speech_forward=st["speech"], music_db_hint=st["music_db"], sfx_density=st["sfx"], notes=notes)
    if a.sfx:
        import bridge
        text, n = bridge.sfx_cues(bm, 0.0, D, ["drops", "sections"], os.path.splitext(a.out)[0] + "-sfx")
        open(a.out + ".cues.txt", "w").write(text); res["cues"] = os.path.abspath(a.out + ".cues.txt"); res["cue_count"] = n
    json.dump(res, open(a.out + ".score.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

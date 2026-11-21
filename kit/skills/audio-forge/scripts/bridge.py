#!/usr/bin/env python3
"""bridge.py -- connect audio-forge to the NextPhase editor (editor-v1 today, newer versions through the same JSON).

Everything speaks one small, versioned file: audio-forge/beatmap@1
  {schema, bpm, beats_per_bar, beats[], downbeats[], sections[{name,start,end}], drops[], energy_per_beat[]?, duration}
compose.py writes one next to every song it makes; `beatmap` below makes one from any audio file or analyze profile.

  beatmap  SRC [--out map.json]            SRC = audio file, profile.json or another beatmap
  fit-tempo --shots work/shots.json        find the BPM (+offset) whose beat grid the existing CUTS already line up with
  snap     --beatmap map.json --shots work/shots.json [--song-at S] [--grid half] [--tol 0.12] [--fps 30]
                                           move cut times onto the nearest beat-grid point (writes shots.snapped.json + report)
  plan-bed --beatmap map.json --words work/tx/words.json --drop-at-word "Claude" [--occurrence 1] --dur 46.4
           [--cut-words "first,last"] [--grid-offset O] [--song bed.wav]
                                           the --song-at (and --ramp) values for editor-v1's bed-mix.py so the drop lands on a word
  sfx-cues --beatmap map.json --song-at S --dur D [--accent drops|sections|downbeats|beats] [--out forge-cues.txt]
                                           synthesise whooshes/impacts/ticks and write an editor-v1 sfx-cues.txt-compatible cue sheet
                                           (append it to the build's sfx-cues.txt before finish.sh)

Nothing here edits the editor's own files; it prints values / writes new files for the agent to apply.
"""
import argparse, json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── beatmap ────────────────────────────────────────────────────────────────
def load_beatmap(src):
    if src.lower().endswith(".json"):
        d = json.load(open(src))
        if d.get("schema", "").startswith("audio-forge/beatmap"):
            return d
        if d.get("schema", "").startswith("audio-forge/profile"):
            return from_profile(d)
        raise SystemExit("unrecognised json (expected beatmap or profile)")
    import analyze
    return from_profile(analyze.analyze(src, quiet=True))


def from_profile(p):
    secs = [dict(name=s["label"], start=s["start"], end=s["end"], bars=s["bars"], energy=s.get("energy")) for s in p.get("sections", [])]
    dur = p.get("analyzed_seconds", 0)
    return dict(schema="audio-forge/beatmap@1", source="analyze", duration=dur, bpm=p["tempo"]["bpm"],
                beats_per_bar=p["meter"]["beats_per_bar"], beats=p["beats"], downbeats=p["downbeats"], sections=secs,
                drops=p.get("drops", []), energy_per_beat=p.get("energy_per_beat"), key=p["key"]["best"], steady=p["tempo"]["steady"])


def grid_points(bm, grid="half"):
    beats = np.array(bm["beats"], dtype=float)
    if len(beats) < 2:
        raise SystemExit("beatmap has no beats")
    if grid == "bar":
        return np.array(bm["downbeats"], dtype=float)
    if grid == "beat":
        return beats
    div = {"half": 2, "quarter": 4, "triplet": 3}[grid]
    pts = [beats]
    step = np.diff(beats)
    step = np.append(step, step[-1])
    for k in range(1, div):
        pts.append(beats + step * k / div)
    return np.sort(np.concatenate(pts))


# ── shots ──────────────────────────────────────────────────────────────────
def load_shots(path):
    d = json.load(open(path))
    out = []
    for s in d:
        if isinstance(s, (list, tuple)):
            out.append([float(s[0]), float(s[1]), s[2] if len(s) > 2 else ""])
        elif isinstance(s, dict):
            out.append([float(s.get("t0", s.get("start", s.get("s")))), float(s.get("t1", s.get("end", s.get("e")))), s.get("name", "")])
        else:
            out.append([float(s), float(s), ""])
    return sorted(out)


def fit_tempo(shots, lo=80, hi=180, unit="half"):
    cuts = np.array(sorted({round(s[0], 4) for s in shots if s[0] > 0.2}))
    if len(cuts) < 6:
        raise SystemExit("need at least 6 cuts to fit a tempo")
    div = {"beat": 1, "half": 2, "quarter": 4}[unit]
    res = []
    for bpm in np.arange(lo, hi, 0.05):
        u = 60.0 / bpm / div
        ang = 2 * np.pi * (cuts % u) / u
        C, S_ = np.cos(ang).mean(), np.sin(ang).mean()
        R = float(np.hypot(C, S_))
        off = float((np.arctan2(S_, C) / (2 * np.pi)) % 1.0 * u)
        res.append((R * np.sqrt(len(cuts)) * (1.0 - 0.15 * abs(np.log2(bpm / 120.0))), bpm, off, R))
    res.sort(reverse=True)
    out = []
    for z, bpm, off, R in res:
        if all(abs(bpm - o["bpm"]) / o["bpm"] > 0.02 for o in out):
            u = 60.0 / bpm / div
            err = np.abs(((cuts - off + u / 2) % u) - u / 2).mean() * 1000
            out.append(dict(bpm=round(float(bpm), 2), offset_s=round(off, 4), alignment=round(R, 3), mean_error_ms=round(float(err), 1)))
        if len(out) >= 5:
            break
    return out


def snap_shots(shots, bm, grid="half", tol=0.12, fps=30.0, song_at=0.0):
    g = grid_points(bm, grid) - song_at  # song time -> video time
    snapped, rep = [], []
    prev_end = 0.0
    for t0, t1, name in shots:
        def snap(t):
            i = int(np.argmin(np.abs(g - t)))
            if abs(g[i] - t) <= tol:
                return float(g[i])
            return t
        n0, n1 = snap(t0), snap(t1)
        n0, n1 = round(n0 * fps) / fps, round(n1 * fps) / fps
        if n1 - n0 < 0.25:
            n0, n1 = round(t0 * fps) / fps, round(t1 * fps) / fps
        rep.append(dict(name=name, t0=t0, new_t0=round(n0, 4), shift_ms=round((n0 - t0) * 1000, 1)))
        snapped.append([round(n0, 4), round(n1, 4), name])
    sh = np.array([abs(r["shift_ms"]) for r in rep])
    stats = dict(shots=len(rep), moved=int((sh > 1).sum()), median_shift_ms=float(np.median(sh)), max_shift_ms=float(sh.max()))
    return snapped, rep, stats


# ── words ──────────────────────────────────────────────────────────────────
def load_words(path):
    out = []
    for w in json.load(open(path)):
        out.append((str(w.get("w", w.get("word", w.get("text", "")))), float(w.get("s", w.get("start", 0))), float(w.get("e", w.get("end", 0)))))
    return out


def find_word(words, word, occurrence=1):
    norm = lambda x: "".join(c for c in x.lower() if c.isalnum())  # noqa: E731
    hits = [(w, s, e) for w, s, e in words if norm(w) == norm(word)]
    if len(hits) < occurrence:
        raise SystemExit(f"word '{word}' occurrence {occurrence} not found ({len(hits)} found)")
    return hits[occurrence - 1]


def plan_bed(bm, words, a):
    if a.drop_at is not None:
        v_t = a.drop_at
        label = f"video time {v_t}"
    else:
        w, s, e = find_word(words, a.drop_at_word, a.occurrence)
        v_t, label = s, f"'{w}' onset {s:.3f}s"
    drops = bm.get("drops") or []
    if not drops:
        secs = bm.get("sections") or []
        drops = [s_["start"] for s_ in secs[1:2]] or [bm["downbeats"][min(8, len(bm["downbeats"]) - 1)]]
    song_drop = drops[min(a.drop_index, len(drops) - 1)]
    song_at = song_drop - v_t
    note = None
    resid = None
    if a.grid_offset is not None:
        # make the song's beats land on the cuts' grid (offset from fit-tempo), choosing the shift nearest to the drop target
        beat = 60.0 / bm["bpm"]
        unit = beat if a.grid_parity == "beat" else beat / 2
        k = round((song_at + a.grid_offset) / unit)
        new_at = -a.grid_offset + k * unit
        resid = round(new_at - song_at, 4)
        song_at = new_at
        label += f" (nudged {resid * 1000:+.0f} ms so beats sit on the cuts' grid)"
    if song_at < 0:
        bar = 60.0 / bm["bpm"] * bm["beats_per_bar"]
        k = int(np.ceil(-song_at / bar))
        note = (f"the drop at song {song_drop:.2f}s is too early to land on {label}; use a later drop (--drop-index) or "
                f"pad the bed with {k} bar(s) of intro ({k * bar:.2f}s) with: audio_edit.py concat intro.wav bed.wav")
    ramps = []
    if a.cut_words:
        first, last = [x.strip() for x in a.cut_words.split(",")][:2]
        _, s0, _ = find_word(words, first, 1)
        _, _, e1 = find_word(words, last, 1)
        ramps.append(f"--ramp {s0 - 0.02:.3f},{e1 + 0.12:.3f},-70,0.012")
    need = max(song_at, 0) + a.dur
    have = bm.get("duration") or 0
    if have and have < need - 0.05:
        extra = f"the bed is {have:.1f}s but bed-mix.py never loops: it needs {need:.1f}s from song-at {max(song_at,0):.2f}s. Regenerate it longer (compose.py --bars N) or use a later --drop-index/earlier drop."
        note = (note + " | " if note else "") + extra
    cmd = (f"$EV1_PY <editor-v1>/scripts/bed-mix.py --voice assets/media/vo.wav --song {a.song or 'BED.wav'} "
           f"--song-at {max(song_at, 0):.3f} --dur {a.dur} --under 5.5 " + " ".join(ramps) + " --out work/premix.wav")
    return dict(song_at=round(song_at, 4), lands_on=label, song_drop=song_drop, ramps=ramps, bed_mix_command=" ".join(cmd.split()), note=note,
                drop_lands_at_video_s=round(song_drop - song_at, 4), grid_nudge_s=resid)


# ── sfx cues ───────────────────────────────────────────────────────────────
def sfx_cues(bm, song_at, dur, accents, sfx_dir, gain=0.8):
    import sfx
    from forge.song import write_wav
    os.makedirs(sfx_dir, exist_ok=True)
    cache = {}
    def path(name, d=None):
        k = (name, d)
        if k not in cache:
            p = os.path.abspath(os.path.join(sfx_dir, f"{name}{'' if d is None else '_' + str(d)}.wav"))
            write_wav(p, sfx.render(name, d))
            cache[k] = p
        return cache[k]
    lines = ["# audio-forge cue sheet:  <time>  <sound>  <gain>   (editor-v1 mix-sfx.py format; times are video seconds)"]
    ev = []
    secs = bm.get("sections") or []
    if "drops" in accents:
        for t in bm.get("drops", []):
            ev += [(t - 0.9, "whoosh_up", 0.9, 0.7), (t, "impact", None, 0.9)]
    if "sections" in accents:
        for s in secs[1:]:
            ev.append((s["start"] - 0.35, "whoosh", 0.7, 0.55))
    if "downbeats" in accents:
        ev += [(t, "hit_low", 0.4, 0.5) for t in bm["downbeats"]]
    if "beats" in accents:
        ev += [(t, "tick", None, 0.35) for t in bm["beats"]]
    n = 0
    for t, name, d, g in sorted(ev):
        vt = t - song_at
        if 0 <= vt < dur:
            lines.append(f"{vt:.3f} {path(name, d)} {g * gain:.2f}")
            n += 1
    return "\n".join(lines) + "\n", n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["beatmap", "fit-tempo", "snap", "plan-bed", "sfx-cues"])
    ap.add_argument("src", nargs="?")
    ap.add_argument("--out"); ap.add_argument("--beatmap"); ap.add_argument("--shots"); ap.add_argument("--words")
    ap.add_argument("--grid", default="half", choices=["bar", "beat", "half", "quarter", "triplet"])
    ap.add_argument("--tol", type=float, default=0.12); ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--drop-at-word"); ap.add_argument("--drop-at", type=float); ap.add_argument("--occurrence", type=int, default=1)
    ap.add_argument("--drop-index", type=int, default=0); ap.add_argument("--cut-words"); ap.add_argument("--dur", type=float, default=60.0)
    ap.add_argument("--song"); ap.add_argument("--song-at", type=float, default=0.0)
    ap.add_argument("--grid-offset", type=float, help="offset_s from fit-tempo: align the bed's beats to the cuts' grid")
    ap.add_argument("--grid-parity", default="beat", choices=["beat", "any"])
    ap.add_argument("--accent", default="drops,sections"); ap.add_argument("--sfx-dir", default="forge-sfx")
    a = ap.parse_args()

    if a.cmd == "beatmap":
        bm = load_beatmap(a.src)
        out = a.out or "beatmap.json"
        json.dump(bm, open(out, "w"), indent=1)
        print(json.dumps(dict(out=out, bpm=bm["bpm"], beats=len(bm["beats"]), bars=len(bm["downbeats"]), sections=len(bm.get("sections", [])), drops=bm.get("drops", []))))
    elif a.cmd == "fit-tempo":
        res = fit_tempo(load_shots(a.shots), unit="half" if a.grid in ("half", "bar") else a.grid)
        print(json.dumps(res, indent=1))
        print(f"\nbest: compose.py --bpm {res[0]['bpm']} ...  then the cut grid sits at offset {res[0]['offset_s']}s; "
              f"use plan-bed to place the bed so beats land on the cuts.", file=sys.stderr)
    elif a.cmd == "snap":
        bm = load_beatmap(a.beatmap)
        shots = load_shots(a.shots)
        snapped, rep, stats = snap_shots(shots, bm, a.grid, a.tol, a.fps, a.song_at)
        out = a.out or os.path.splitext(a.shots)[0] + ".snapped.json"
        json.dump(snapped, open(out, "w"))
        json.dump(dict(stats=stats, shifts=rep), open(out + ".report.json", "w"), indent=1)
        print(json.dumps(dict(out=out, **stats)))
    elif a.cmd == "plan-bed":
        bm = load_beatmap(a.beatmap)
        words = load_words(a.words) if a.words else []
        if not words and a.drop_at is None:
            ap.error("--words (or --drop-at SECONDS) required")
        print(json.dumps(plan_bed(bm, words, a), indent=1))
    elif a.cmd == "sfx-cues":
        bm = load_beatmap(a.beatmap)
        text, n = sfx_cues(bm, a.song_at, a.dur, [x.strip() for x in a.accent.split(",")], a.sfx_dir)
        out = a.out or "forge-cues.txt"
        open(out, "w").write(text)
        print(json.dumps(dict(out=out, cues=n, sfx_dir=a.sfx_dir)))


if __name__ == "__main__":
    main()

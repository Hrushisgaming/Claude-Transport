#!/usr/bin/env python3
"""survey.py - run the deep analyzer over many tracks and print ONE table of what it finds (regression check + quick family overview).

  af.py survey DIR_OR_FILES... [--out survey.md] [--min-seconds 3]

For each track: length, BPM, section labels, breakdowns, builds, drops, end cut, loop-ready. Tracks shorter than 3 s (stingers) are listed as skipped.
Use it after ANY change to deep.py: run it before and after and diff the tables (see NOTES-FOR-AGENTS.md at the kit root).
"""
import argparse, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deep as D
EXT = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mpeg")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("paths", nargs="+"); ap.add_argument("--out")
    a = ap.parse_args(); files = []
    for p in a.paths: files += sorted(f for f in glob.glob(os.path.join(p, "*")) if f.lower().endswith(EXT)) if os.path.isdir(p) else [p]
    L = ["| track | s | BPM | sections | breakdowns (bar,len) | builds | drops (bar) | end cut | loop-ready |", "|---|---|---|---|---|---|---|---|---|"]
    for f in files:
        nm = os.path.basename(f)
        try: d = D.deep(f)
        except BaseException as e: L.append(f"| {nm} | - | - | skipped: {str(e)[:60]} | | | | | |"); continue
        hp = d["hard_points"]; tl = hp.get("tail")
        L.append(f"| {nm} | {d['seconds']:.0f} | {d['grid']['bpm']:.0f} | {' '.join(s['label'][:3] for s in d['sections'])} | {', '.join(f'{q['bar']},{q['bars']}' for q in hp['breakdowns']) or '-'} | {', '.join(f'{q['bar']},{q['bars']}' for q in hp['builds']) or '-'} | {', '.join(str(q['bar']) for q in hp['drops']) or '-'} | "
                 + (f"{tl['kind']} @ {tl['t_cut']} s" if tl else "-") + f" | {'yes' if d['loop']['loop_ready'] else 'no'} |")
    out = "\n".join(L) + "\n"; print(out)
    if a.out: open(a.out, "w").write(out)


if __name__ == "__main__":
    main()

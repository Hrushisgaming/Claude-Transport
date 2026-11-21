#!/usr/bin/env python3
"""aicheck.py - compare what an AI SAID it heard (Gemini, Qwen ...) with what the analyzer measured, and write the 'check my numbers' prompt.

  af.py aicheck deep.json answer.txt [--tol 2.5]        score an AI's listening answer: which of its timestamps the analyzer confirms, which it missed
  af.py aicheck deep.json --prompt                      print the 'check my numbers' prompt for this track (same format as the listening-test-pack)

How scoring works: every mm:ss (or mm:ss-mm:ss) in the answer becomes a claim; the nearest analyzer event within --tol seconds confirms it
(event = drop, breakdown, build, riser, stop, end cut, hit, section start). The claim's words (drop, breakdown, riser, fill, cut, climax, impact) are
checked for a sensible kind. It is a sanity check, not a judge: AI timestamps are usually good to about +-2 s, and an AI can be wrong.
"""
import argparse, json, re, sys
KIND = {"drop": ("drop", "climax", "slam", "kicks in", "beat drop"), "breakdown": ("breakdown", "break", "strip", "sparse", "pull back", "filtered", "drop out", "drops out"),
        "build": ("riser", "build", "roll", "sweep", "accelerat", "fill"), "cut": ("cut", "final", "end", "tail", "decay", "stop"), "impact": ("impact", "hit", "boom", "crash")}
TS = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?:\s*[-\u2013]\s*(?:(\d{1,2}):(\d{2})|(\d{2})))?(?!\d)")


def events(d):
    hp = d["hard_points"]; ev = []
    for q in hp["drops"]: ev.append((q["t"], "drop", "drop"))
    for q in hp.get("breakdowns", []): ev.append((q["t"], "breakdown", "breakdown"))
    for q in hp.get("builds", []): ev.append((q["t"], "build", "build"))
    for q in hp["risers"]: ev.append((q["t"], "build", "riser"))
    for q in hp["stops"]: ev.append((q["t"], "cut", "stop"))
    if hp.get("tail"): ev.append((hp["tail"]["t_cut"], "cut", "end cut"))
    for q in hp["hits"]: ev.append((q["t"], "impact", "hit"))
    for s in d["sections"]: ev.append((s["t0"], "section", f"section start ({s['label']})"))
    return sorted(ev)


def claims(text):
    out = []
    for line in re.split(r"\n|(?<=[.;])\s", text):
        for m in TS.finditer(line):
            t = int(m.group(1)) * 60 + int(m.group(2)); low = line.lower()
            kinds = [k for k, ws in KIND.items() if any(w in low for w in ws)]
            out.append((t, kinds, line.strip()[:140]))
    return out


def prompt(d, name):
    import deep as D
    return ("I will give you a track and a table a script produced about it (times are mm:ss; \"bar:beat\" is just the script's grid). The script cannot hear.\n"
            "For EACH row: say correct / roughly right (give the real mm:ss) / wrong, and what actually happens at that moment.\nThen list important moments the script MISSED.\n"
            "Then say whether its section names (intro, build, drop, break, outro) match what you hear, and rename them if not.\nSay \"unsure\" rather than guessing. Do not search the web; only use what you hear.\n\n"
            f"TRACK: {name}\n\nSCRIPT OUTPUT:\n" + D.timeline_md(d, name).split("## Loop-readiness")[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("deep_json"); ap.add_argument("answer", nargs="?"); ap.add_argument("--tol", type=float, default=2.5); ap.add_argument("--prompt", action="store_true")
    a = ap.parse_args(); d = json.load(open(a.deep_json))
    if a.prompt or not a.answer:
        import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); print(prompt(d, d["file"])); return
    ev = events(d); cl = claims(open(a.answer).read()); hit = set(); L = ["| AI says (time) | AI words | analyzer event | gap s | verdict |", "|---|---|---|---|---|"]
    for t, kinds, line in cl:
        strong = [e for e in ev if e[1] != "section" and abs(e[0] - t) <= a.tol]; weak = [e for e in ev if e[1] == "section" and abs(e[0] - t) <= a.tol]
        near = min(strong, key=lambda e: abs(e[0] - t)) if strong else (min(weak, key=lambda e: abs(e[0] - t)) if weak else None)
        if near:
            ok = (not kinds) or near[1] in kinds; hit.add(near); verdict = "weak: only a section boundary is near" if near[1] == "section" else ("confirmed" if ok else "time matches, kind differs")
            L.append(f"| {t // 60}:{t % 60:02d} | {line[:60]} | {near[2]} @ {near[0]:.1f} | {near[0] - t:+.1f} | {verdict} |")
        else: L.append(f"| {t // 60}:{t % 60:02d} | {line[:60]} | - | - | AI-only (analyzer has nothing within {a.tol} s) |")
    L += ["", "Analyzer events the AI did not mention (not necessarily wrong; hits and section starts are often skipped):"]
    L += [f"- {e[2]} @ {e[0]:.1f} s" for e in ev if e not in hit and e[1] in ("drop", "breakdown", "build", "cut")] or ["- none"]
    print("\n".join(L))


if __name__ == "__main__":
    main()

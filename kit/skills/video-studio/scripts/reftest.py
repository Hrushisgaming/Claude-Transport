#!/usr/bin/env python3
"""reftest.py - a small lab for finding which instructions make the agent draw/recreate a real thing most accurately.

  reftest.py init [dir]                      create the lab (default ./reflab): subjects.json, variants.json, runs.csv
  reftest.py subjects                        list subjects and their yes/no checks (edit subjects.json to change them)
  reftest.py variants                        list the instruction variants
  reftest.py prompt VARIANT SUBJECT [--model M]   print the exact text to give the agent for that variant
  reftest.py sheet REF.png RENDER.png [--out sheet.png]   side-by-side image, so you can score the render against the reference
  reftest.py score SUBJECT VARIANT --run N --model M [--hits 1,0,1,...] [--notes TEXT]   log one run (omit --hits to answer y/n per check)
  reftest.py report [--by variant|model|subject]       average score, spread and run count; the best row is marked
  reftest.py duel add run*.png --variant V --model M   register drawings;  duel run  = blind A/B judging (fast);  duel report = win rates

Method: pick ONE variant per run, same subject, same model; run each variant 3 times (results vary), score every run against
the SAME checks, compare averages. Change one thing at a time (variant OR model), never both. Needs only Python 3.9+ (Pillow for `sheet`).
"""
import argparse, csv, json, os, statistics, sys

LAB = os.environ.get("REFLAB", "reflab")
RULE = "The reference images are for looking only: do not paste or trace them into the output. Say which images you used."

VARIANTS = {
 "v1-baseline": ("Search for {s} and draw it.", "no guidance: the control"),
 "v2-analyse": ("Search for {s}. Fetch 2 clear reference images and look at them carefully. Then draw {s}. " + RULE, "look first, then draw"),
 "v3-checklist": ("Search for {s} and fetch 2 clear reference images. Look at them and write a numbered checklist of at least 10 concrete visual features "
                  "(shapes, colours, counts, positions, proportions, clothing, props) and save it. Draw {s} using ONLY that checklist. " + RULE, "written feature list, drawn from the list"),
 "v4-loop": ("Search for {s} and fetch 2 clear reference images. Write a numbered checklist of at least 10 concrete visual features and save it. Draw {s} from the checklist and render it. "
             "Then view your render next to the reference, mark every checklist item matched or off, fix the off items and re-render. Repeat up to 3 rounds, stop early if all match. "
             "Finally report which items you could not match. " + RULE, "checklist + compare-and-fix loop"),
 "v5-simplify": ("Search for {s} and fetch 2 clear reference images. Draw a flat, stylised version of {s} on purpose: priority is the silhouette, the colour palette and the 3 most "
                 "recognisable signature features; skip fine detail. Use few simple shapes. " + RULE, "less detail, fewer anatomy errors"),
 "v6-parts": ("Search for {s} and fetch 2 clear reference images. Draw it part by part: first the head only, render and compare with the reference, fix it; then the torso; then limbs and props; "
              "then assemble and compare the whole. Never move on until the current part matches. " + RULE, "one part at a time, checked each time"),
 "v8-skill": ("Follow the reference-check skill exactly, in order, for: {s}. Do not draw anything before the checklist passes `refs.py checklist check`. Report the references you used and the items you could not match. " + RULE, "the full enforced protocol (needs the reference-check skill installed)"),
 "v7-refs": ("Search for {s} and fetch 3 reference images from different angles. Write a checklist from ALL of them (note where they disagree), draw from it, then run the compare-and-fix loop "
             "up to 3 rounds against the clearest image. " + RULE, "more references + loop"),
}

SUBJECTS = {
 "controller": ["overall silhouette/shape correct", "colour of the body", "number and layout of face buttons", "thumbsticks present, position correct",
                "d-pad present, position correct", "triggers/bumpers visible", "touchpad / centre button as on the real model", "proportions (width vs height) close",
                "no extra or missing parts", "reads as that exact model, not a generic pad"],
 "character": ["hair shape and colour", "number and placement of eyes", "face markings in the right places", "face proportions (not generic)", "skin tone",
               "outfit and its colours", "number of limbs correct and anatomically joined", "signature prop or accessory present", "pose reads naturally", "recognisable as that character at a glance"],
 "product": ["overall shape", "main colour", "logo/label area plausible (no invented text)", "key parts present", "proportions", "materials/finish suggested",
             "no extra or missing parts", "viewing angle matches a reference", "background clean", "recognisable as that product"],
}


def p(*a): return os.path.join(LAB, *a)


def load(name, default):
    return json.load(open(p(name))) if os.path.exists(p(name)) else default


def cmd_init(a):
    os.makedirs(LAB, exist_ok=True)
    if not os.path.exists(p("subjects.json")): json.dump(SUBJECTS, open(p("subjects.json"), "w"), indent=1)
    json.dump({k: dict(text=v[0], idea=v[1]) for k, v in VARIANTS.items()}, open(p("variants.json"), "w"), indent=1)
    if not os.path.exists(p("runs.csv")): open(p("runs.csv"), "w").write("subject,variant,run,model,score,max,hits,notes\n")
    print(f"lab ready in {LAB}/ : edit subjects.json (checks), then `prompt`, run the agent, `score`.")


def cmd_list(a):
    if a.cmd == "subjects":
        for k, v in load("subjects.json", SUBJECTS).items(): print(f"{k}:\n" + "\n".join(f"  {i + 1}. {c}" for i, c in enumerate(v)))
    else:
        for k, v in VARIANTS.items(): print(f"{k:14s} {v[1]}")


def cmd_prompt(a):
    v = load("variants.json", {k: dict(text=t, idea=i) for k, (t, i) in VARIANTS.items()})
    if a.variant not in v: sys.exit("unknown variant; try: " + ", ".join(v))
    print(v[a.variant]["text"].format(s=a.subject))
    print(f"\n(log it with: reftest.py score {a.subject} {a.variant} --run N --model {a.model or 'MODEL'})", file=sys.stderr)


def cmd_sheet(a):
    from PIL import Image, ImageDraw
    A, B = Image.open(a.ref).convert("RGB"), Image.open(a.render).convert("RGB"); h = 900
    A = A.resize((int(A.width * h / A.height), h)); B = B.resize((int(B.width * h / B.height), h))
    S = Image.new("RGB", (A.width + B.width + 30, h + 50), (20, 20, 20)); S.paste(A, (10, 40)); S.paste(B, (A.width + 20, 40))
    d = ImageDraw.Draw(S); d.text((12, 12), "REFERENCE", fill=(255, 255, 255)); d.text((A.width + 22, 12), "RENDER", fill=(255, 255, 255))
    S.save(a.out); print("wrote", a.out)


def cmd_score(a):
    checks = load("subjects.json", SUBJECTS).get(a.subject)
    if not checks: sys.exit("unknown subject; see `subjects`")
    if a.hits: hits = [int(x) for x in a.hits.split(",")]
    elif sys.stdin.isatty(): hits = [1 if input(f"{i + 1}. {c}  [y/N] ").strip().lower().startswith("y") else 0 for i, c in enumerate(checks)]
    else: sys.exit("give --hits 1,0,1,... (one 0/1 per check) when not at a terminal")
    if len(hits) != len(checks): sys.exit(f"expected {len(checks)} values, got {len(hits)}")
    if not os.path.exists(p("runs.csv")): cmd_init(a)
    with open(p("runs.csv"), "a", newline="") as f: csv.writer(f).writerow([a.subject, a.variant, a.run, a.model, sum(hits), len(hits), "".join(map(str, hits)), a.notes or ""])
    print(f"logged {a.subject}/{a.variant} run {a.run} ({a.model}): {sum(hits)}/{len(hits)}")


def cmd_report(a):
    rows = list(csv.DictReader(open(p("runs.csv")))) if os.path.exists(p("runs.csv")) else []
    if not rows: sys.exit("no runs logged yet")
    if a.by != "model" and len({r['model'] for r in rows}) > 1: print("WARNING: runs from several models are mixed in this table; use `--by model`, or compare variants within ONE model.\n")
    groups = {}
    for r in rows: groups.setdefault(r[a.by], []).append(int(r["score"]) / int(r["max"]))
    table = sorted(((statistics.mean(v), statistics.pstdev(v) if len(v) > 1 else 0.0, len(v), k) for k, v in groups.items()), reverse=True)
    print(f"{a.by:16s} {'avg':>6s} {'spread':>7s} {'runs':>5s}")
    for i, (m, s, n, k) in enumerate(table): print(f"{k:16s} {100 * m:5.0f}% {100 * s:6.0f}% {n:5d}{'   <- best so far' if i == 0 else ''}{'   (few runs: treat as a hint)' if n < 3 else ''}")
    if len(table) > 1 and table[0][0] - table[1][0] < table[0][1] + 0.05: print("\nThe top two are within the run-to-run spread: not a clear winner yet. Add runs.")
    miss = {}
    for r in rows:
        for i, h in enumerate(r["hits"]):
            if h == "0": miss[(r["subject"], i + 1)] = miss.get((r["subject"], i + 1), 0) + 1
    if miss:
        checks = load("subjects.json", SUBJECTS); worst = sorted(miss.items(), key=lambda x: -x[1])[:5]
        print("\nMost-missed checks (the model's blind spots):"); [print(f"  {s} #{i}: {checks[s][i - 1]}  (missed {n}x)") for (s, i), n in worst]


# ── blind A/B duels: faster and steadier than ten yes/no checks ──
def dload():
    return json.load(open(p("duels.json"))) if os.path.exists(p("duels.json")) else dict(entries=[], results=[], pending=None)


def dsave(d):
    os.makedirs(LAB, exist_ok=True); json.dump(d, open(p("duels.json"), "w"), indent=1)


def duel_add(a):
    d = dload()
    for f in a.images:
        if not os.path.exists(f): sys.exit("no such file: " + f)
        d["entries"].append(dict(id=len(d["entries"]) + 1, file=os.path.abspath(f), variant=a.variant, run=a.run, model=a.model))
    dsave(d); print(f"{len(d['entries'])} drawings registered ({a.variant}, {a.model})")


def _pair_sheet(ref, fa, fb, out):
    from PIL import Image, ImageDraw
    ims = [Image.open(x).convert("RGB") for x in (ref, fa, fb)]; h = 820; ims = [i.resize((max(1, int(i.width * h / i.height)), h)) for i in ims]
    S = Image.new("RGB", (sum(i.width for i in ims) + 40, h + 50), (18, 18, 18)); x = 10; d = ImageDraw.Draw(S)
    for lab, i in zip(("REFERENCE", "A", "B"), ims): S.paste(i, (x, 40)); d.text((x + 6, 14), lab, fill=(255, 255, 255)); x += i.width + 10
    S.save(out)


def duel_next(a, quiet=False):
    import random, itertools
    d = dload()
    if d["pending"]: 
        if not quiet: print("a duel is already waiting for an answer:", d["pending"]["sheet"])
        return d["pending"]
    done = {frozenset((r["x"], r["y"])) for r in d["results"]}
    pairs = [(x, y) for x, y in itertools.combinations(d["entries"], 2) if x["variant"] != y["variant"] and frozenset((x["id"], y["id"])) not in done]
    if not pairs: return None
    rng = random.SystemRandom(); x, y = rng.choice(pairs)                    # a fresh random pick every time
    if rng.random() < 0.5: x, y = y, x                                       # random side: A/B is never tied to a variant
    os.makedirs(p("duels"), exist_ok=True); sheet = p("duels", f"duel_{len(d['results']) + 1:03d}.png"); _pair_sheet(a.ref, x["file"], y["file"], sheet)
    d["pending"] = dict(x=x["id"], y=y["id"], sheet=sheet); dsave(d)
    left = len(pairs) - 1
    if not quiet: print(f"{sheet}   (A vs B, about {left} more after this)")
    return d["pending"]


def duel_answer(a):
    d = dload(); pen = d["pending"]
    if not pen: sys.exit("no duel waiting: run `duel next` first")
    d["results"].append(dict(x=pen["x"], y=pen["y"], winner={"a": "x", "b": "y", "t": "tie"}[a.choice])); d["pending"] = None; dsave(d); print("recorded", a.choice)


def duel_run(a):
    import subprocess
    n = 0
    while n < a.max:
        pen = duel_next(a, quiet=True)
        if not pen: print("no more pairs to judge"); break
        if sys.platform == "darwin": subprocess.run(["open", pen["sheet"]])
        else: print("open this image:", pen["sheet"])
        c = input(f"[{n + 1}/{a.max}] which is closer to the REFERENCE?  a / b / t(ie) / q(uit): ").strip().lower()
        if c == "q": break
        if c in ("a", "b", "t"): a.choice = c; duel_answer(a); n += 1
    print(f"{n} duels judged. Next: reftest.py duel report")


def duel_report(a):
    d = dload(); E = {e["id"]: e for e in d["entries"]}
    if not d["results"]: sys.exit("no duels judged yet")
    key = {"variant": lambda e: e["variant"], "model": lambda e: e["model"]}[a.by]; w, n, h2h = {}, {}, {}
    for r in d["results"]:
        for me, other, mine in ((r["x"], r["y"], "x"), (r["y"], r["x"], "y")):
            k = key(E[me]); n[k] = n.get(k, 0) + 1; sc = 0.5 if r["winner"] == "tie" else (1.0 if r["winner"] == mine else 0.0); w[k] = w.get(k, 0) + sc
            ko = key(E[other]); h2h.setdefault((k, ko), [0, 0]); h2h[(k, ko)][0] += sc; h2h[(k, ko)][1] += 1
    rows = sorted(((w[k] / n[k], n[k], k) for k in w), reverse=True)
    print(f"{a.by:16s} {'win rate':>9s} {'duels':>6s}")
    for i, (r, c, k) in enumerate(rows): print(f"{k:16s} {100 * r:8.0f}% {c:6d}{'   <- closest to the reference' if i == 0 else ''}{'   (few duels: a hint only)' if c < 8 else ''}")
    print("\nhead to head (row beats column):")
    ks = [k for _, _, k in rows]; print(" " * 16 + "".join(f"{k[:12]:>13s}" for k in ks))
    for k in ks: print(f"{k:16s}" + "".join(f"{(100 * h2h[(k, o)][0] / h2h[(k, o)][1]):12.0f}%" if (k, o) in h2h else f"{'-':>13s}" for o in ks))
    if len(rows) > 1 and rows[0][0] - rows[1][0] < 0.10: print("\nThe top two are close (under 10 points): judge more pairs before trusting the order.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init"); sp.add_parser("subjects"); sp.add_parser("variants")
    x = sp.add_parser("prompt"); x.add_argument("variant"); x.add_argument("subject"); x.add_argument("--model")
    x = sp.add_parser("sheet"); x.add_argument("ref"); x.add_argument("render"); x.add_argument("--out", default="sheet.png")
    x = sp.add_parser("score"); x.add_argument("subject"); x.add_argument("variant"); x.add_argument("--run", type=int, default=1); x.add_argument("--model", default="unknown"); x.add_argument("--hits"); x.add_argument("--notes")
    x = sp.add_parser("report"); x.add_argument("--by", default="variant", choices=["variant", "model", "subject"])
    x = sp.add_parser("duel"); ds = x.add_subparsers(dest="dcmd", required=True)
    y = ds.add_parser("add"); y.add_argument("images", nargs="+"); y.add_argument("--variant", required=True); y.add_argument("--run", type=int, default=1); y.add_argument("--model", default="unknown")
    y = ds.add_parser("next"); y.add_argument("--ref", default="reference.jpeg")
    y = ds.add_parser("answer"); y.add_argument("choice", choices=["a", "b", "t"])
    y = ds.add_parser("run"); y.add_argument("--ref", default="reference.jpeg"); y.add_argument("--max", type=int, default=24)
    y = ds.add_parser("report"); y.add_argument("--by", default="variant", choices=["variant", "model"])
    ap.add_argument("--lab", default=None); a = ap.parse_args()
    global LAB
    if a.lab: LAB = a.lab
    if a.cmd == "duel": {"add": duel_add, "next": duel_next, "answer": duel_answer, "run": duel_run, "report": duel_report}[a.dcmd](a); return
    {"init": cmd_init, "subjects": cmd_list, "variants": cmd_list, "prompt": cmd_prompt, "sheet": cmd_sheet, "score": cmd_score, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()

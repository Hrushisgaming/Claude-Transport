#!/usr/bin/env python3
"""refs.py - keep a project's reference images, written checklist, compare rounds and verified facts. Standard library (+ Pillow for sheets).
See ../SKILL.md for the protocol. State: work/refs.json (claims, checklists, compare rounds), images in work/refs/<subject>/.
"""
import argparse, datetime, json, os, re, sys, urllib.parse, urllib.request

REQUIRED = ["silhouette", "colour", "count", "position", "clothing", "pose", "signature", "must_not"]
MIN_ITEMS = 14
UA = {"User-Agent": "reference-check/1.0 (local video tooling; contact: user)"}


def state_path(): return os.path.join("work", "refs.json")


def load():
    return json.load(open(state_path())) if os.path.exists(state_path()) else dict(claims=[], checklists={}, rounds={})


def save(s):
    os.makedirs("work", exist_ok=True); json.dump(s, open(state_path(), "w"), indent=1)


def slug(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40] or "subject"


def http(url, binary=False, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            d = r.read(); return d if binary else json.loads(d.decode("utf-8", "replace"))
    except Exception as e:
        sys.exit(f"refs: could not reach {url[:90]}: {e}\nNo web from this script? Use your own websearch/webfetch, or ask the person for 2-3 reference images or links.")


def cmd_wiki(a):
    q = urllib.parse.urlencode(dict(action="query", format="json", redirects=1, generator="search", gsrsearch=a.title, gsrlimit=3, prop="extracts|pageimages|info", exintro=1, explaintext=1, exsentences=6, piprop="original", inprop="url"))
    pages = (http("https://en.wikipedia.org/w/api.php?" + q).get("query") or {}).get("pages", {})
    if not pages: sys.exit("refs: no Wikipedia page found; try a different title or the franchise's official wiki")
    for p in sorted(pages.values(), key=lambda x: x.get("index", 9)):
        print(f"## {p['title']}  {p.get('fullurl', '')}\n{(p.get('extract') or '').strip()[:900]}\nimage: {(p.get('original') or {}).get('source', '-')}\n")
    print("These are starting points: confirm facts on a second source and log them with `claim`.")


def cmd_commons(a):
    q = urllib.parse.urlencode(dict(action="query", format="json", generator="search", gsrsearch=a.query, gsrnamespace=6, gsrlimit=a.n, prop="imageinfo", iiprop="url|extmetadata|size", iiurlwidth=1000))
    pages = (http("https://commons.wikimedia.org/w/api.php?" + q).get("query") or {}).get("pages", {})
    if not pages: sys.exit("refs: nothing on Commons (copyrighted characters and products are often not there); use the official site or ask the person for images")
    for p in sorted(pages.values(), key=lambda x: x.get("index", 9)):
        ii = (p.get("imageinfo") or [{}])[0]; lic = (ii.get("extmetadata", {}).get("LicenseShortName", {}) or {}).get("value", "?")
        print(f"{p['title']}\n  url: {ii.get('thumburl') or ii.get('url')}\n  size: {ii.get('width')}x{ii.get('height')}  licence: {lic}")


def cmd_get(a):
    data = http(a.url, binary=True)
    if len(data) < 3000: sys.exit("refs: that is not an image (too small); give a direct image URL")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True); open(a.out, "wb").write(data)
    try:
        from PIL import Image; w, h = Image.open(a.out).size; print(f"saved {a.out} ({w}x{h}); look-only: never ship or trace it" + ("  WARNING: small image, fine detail will be missing" if min(w, h) < 400 else ""))
    except Exception: print("saved", a.out, "(could not read it as an image: check the URL)")


def cmd_sheet(a):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        files = [a.pair[0], a.pair[1]] if a.pair else sorted(os.path.join(a.dir, f) for f in os.listdir(a.dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        print("refs: Pillow is not installed here, so no contact sheet. Do NOT install packages or decode pixels. View these image files ONE BY ONE with your image-viewing tool instead:\n  " + "\n  ".join(files)); return
    if a.pair:
        A, B = Image.open(a.pair[0]).convert("RGB"), Image.open(a.pair[1]).convert("RGB"); h = 900
        A = A.resize((max(1, int(A.width * h / A.height)), h)); B = B.resize((max(1, int(B.width * h / B.height)), h))
        S = Image.new("RGB", (A.width + B.width + 30, h + 50), (20, 20, 20)); S.paste(A, (10, 40)); S.paste(B, (A.width + 20, 40)); d = ImageDraw.Draw(S)
        d.text((12, 12), "REFERENCE", fill=(255, 255, 255)); d.text((A.width + 22, 12), "RENDER", fill=(255, 255, 255)); out = a.out or "pair.png"
    else:
        fs = sorted(f for f in os.listdir(a.dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")) and not f.startswith("sheet"))
        if not fs: sys.exit("refs: no images in " + a.dir)
        ims = [Image.open(os.path.join(a.dir, f)).convert("RGB") for f in fs]; h = 600; ims = [i.resize((max(1, int(i.width * h / i.height)), h)) for i in ims]
        S = Image.new("RGB", (sum(i.width for i in ims) + 10 * (len(ims) + 1), h + 40), (20, 20, 20)); x = 10; d = ImageDraw.Draw(S)
        for f, i in zip(fs, ims): S.paste(i, (x, 30)); d.text((x + 4, 8), f, fill=(255, 255, 255)); x += i.width + 10
        out = a.out or os.path.join(a.dir, "sheet.png")
    S.save(out); print("wrote", out, "- now LOOK at it")


def cmd_claim(a):
    s = load(); s["claims"].append(dict(claim=a.claim, source=a.source, verified=(a.verified == "yes"), on_screen=bool(a.on_screen), date=datetime.date.today().isoformat(), note=a.note or "")); save(s); print("logged claim", len(s["claims"]))


def cmd_checklist(a):
    s = load()
    if a.sub == "new":
        sl = slug(a.subject); os.makedirs(os.path.join("work", "refs", sl), exist_ok=True)
        s["checklists"][sl] = dict(subject=a.subject, items=[], template=dict(id="c1", category="|".join(REQUIRED), observation="what you SEE, concrete", ref="ref1.jpg", status="seen|unsure"))
        save(s); print(f"checklist '{sl}' created. Add items with: refs.py checklist add --category C --observation \"what you see\" --ref ref1.jpg   (>= {MIN_ITEMS} items; categories: {', '.join(REQUIRED)})"); return
    if a.sub == "add":
        if not (a.category in REQUIRED and a.observation and a.ref): sys.exit(f"refs: add needs --category ({'|'.join(REQUIRED)}), --observation, --ref")
        sl = a.name or (list(s["checklists"])[-1] if s["checklists"] else None)
        if not sl: sys.exit("refs: run `checklist new` first")
        its = s["checklists"][sl]["items"]; its.append(dict(id=f"c{len(its) + 1}", category=a.category, observation=a.observation, ref=a.ref, status="unsure" if a.unsure else "seen")); save(s); print(f"added c{len(its)} ({a.category}); {len(its)} items"); return
    sl = a.name or (list(s["checklists"])[-1] if s["checklists"] else None)
    if not sl or sl not in s["checklists"]: sys.exit("refs: no checklist; run `checklist new`")
    items = s["checklists"][sl]["items"]; cats = {i.get("category") for i in items}; miss = [c for c in REQUIRED if c not in cats]
    bad = [i.get("id") for i in items if not i.get("observation") or not i.get("ref")]
    ok = len(items) >= MIN_ITEMS and not miss and not bad
    print(f"{sl}: {len(items)} items; missing categories: {miss or 'none'}; items without observation/ref: {bad or 'none'}; unsure: {[i.get('id') for i in items if i.get('status') == 'unsure'] or 'none'}")
    if not ok: sys.exit(f"refs: checklist not ready (need >= {MIN_ITEMS} items, every category, each with an observation and a reference image). Do not draw yet.")
    print("checklist ready: draw from it.")


def tally(s, sl):
    last = {}
    for r in s["rounds"].get(sl, []): last[r["id"]] = r
    ids = [i["id"] for i in s["checklists"].get(sl, {}).get("items", [])] or list(last)
    m = sum(1 for i in ids if i in last and last[i]["verdict"] == "matched"); off = [last[i] for i in ids if i in last and last[i]["verdict"] != "matched"]
    return m, off, [i for i in ids if i not in last], max((r["round"] for r in s["rounds"].get(sl, [])), default=0)


def cmd_compare(a):
    s = load()
    if a.round == "status":
        for sl in s["rounds"]:
            m, off, un, rd = tally(s, sl)
            print(f"{sl}: {m} matched, {len(off)} off, {len(un)} NOT COMPARED yet, round {rd}")
            for r in off: print(f"  OFF {r['id']} ({r['verdict']}): {r['note']}")
            if un: print("  compare every item before you stop: " + ", ".join(un))
        return
    sl = a.name or (list(s["checklists"])[-1] if s["checklists"] else "subject")
    ids = {i.get("id") for i in s["checklists"].get(sl, {}).get("items", [])}
    if ids and a.id not in ids: sys.exit(f"refs: unknown item id '{a.id}'")
    s["rounds"].setdefault(sl, []).append(dict(round=int(a.round), id=a.id, verdict=a.verdict, note=a.note or "")); save(s); print("recorded", a.id, a.verdict)


def cmd_report(a):
    s = load(); today = datetime.date.today(); L = ["## Checked facts", "", "| claim | source | verified | on screen | date | flag |", "|---|---|---|---|---|---|"]
    for c in s["claims"]:
        age = (today - datetime.date.fromisoformat(c["date"])).days; flag = "UNVERIFIED" if not c["verified"] else "stale (>30 days): re-check" if age > 30 else "ok"
        L.append(f"| {c['claim']} | {c['source']} | {'yes' if c['verified'] else 'NO'} | {'yes' if c['on_screen'] else 'no'} | {c['date']} | {flag} |")
    for sl in s["rounds"]:
        m, off, un, rd = tally(s, sl); tot = m + len(off) + len(un)
        L.append(f"\n**{sl}**: {m}/{tot} checklist items matched after {rd} round(s). Not matched: " + (", ".join(f"{r['id']} ({r['note']})" for r in off) or "none") + (f". NOT COMPARED: {', '.join(un)}" if un else ""))
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__); sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init")
    x = sp.add_parser("wiki"); x.add_argument("title")
    x = sp.add_parser("commons"); x.add_argument("query"); x.add_argument("-n", type=int, default=6)
    x = sp.add_parser("get"); x.add_argument("url"); x.add_argument("--out", required=True)
    x = sp.add_parser("sheet"); x.add_argument("dir", nargs="?"); x.add_argument("--pair", nargs=2); x.add_argument("--out")
    x = sp.add_parser("claim"); x.add_argument("claim"); x.add_argument("--source", required=True); x.add_argument("--verified", choices=["yes", "no"], required=True); x.add_argument("--on-screen", action="store_true"); x.add_argument("--note")
    x = sp.add_parser("checklist"); x.add_argument("sub", choices=["new", "add", "check"]); x.add_argument("subject", nargs="?"); x.add_argument("--name"); x.add_argument("--category"); x.add_argument("--observation"); x.add_argument("--ref"); x.add_argument("--unsure", action="store_true")
    x = sp.add_parser("compare"); x.add_argument("round"); x.add_argument("id", nargs="?"); x.add_argument("verdict", nargs="?", choices=["matched", "off", "unsure"]); x.add_argument("--note"); x.add_argument("--name")
    sp.add_parser("report")
    a = ap.parse_args()
    if a.cmd == "init": os.makedirs(os.path.join("work", "refs"), exist_ok=True); save(load()); print("ready: work/refs/ and work/refs.json"); return
    if a.cmd == "sheet" and not (a.dir or a.pair): ap.error("sheet needs DIR or --pair REF RENDER")
    if a.cmd == "compare" and a.round != "status" and not (a.id and a.verdict): ap.error("compare ROUND ID matched|off|unsure")
    if a.cmd == "checklist" and a.sub == "new" and not a.subject: ap.error("checklist new needs the subject line")
    {"wiki": cmd_wiki, "commons": cmd_commons, "get": cmd_get, "sheet": cmd_sheet, "claim": cmd_claim, "checklist": cmd_checklist, "compare": cmd_compare, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""lyrics.py - analyse the LYRICS of a track: where the words sit against the bars, drops and sections, how dense, how repetitive, how rhymed.

  af.py lyrics track.mp3 [--deep deep.json] [--model small] [--language en] [--separate] [--keep-text]   transcribe with Whisper (OPTIONAL, ~500 MB, ask first)
  af.py lyrics track.mp3 --words words.json   [--deep deep.json]     words.json from `af.py listen --words` ([{"w","s","e"}]) - no Whisper needed here
  af.py lyrics --text lyrics.txt              [--deep deep.json]     lyrics you typed/pasted yourself: text statistics only (no timing)

Writes ./lyrics/<name>/lyrics.json (audio-forge/lyrics@1): STATISTICS ONLY by default - counts, rates, positions, repetition and rhyme shares, theme-word counts.
The words themselves are NOT stored unless you pass --keep-text, which also writes lyrics.local.json (private working copy: do not publish or commit it).

Honest limits: Whisper on music is noisy (instruments, effects, chopped samples, stylised vocals). Treat counts as approximate; `--separate` (Demucs vocal stem, ~1 GB, ask first)
makes it much better. No Whisper and no text = this tool says so and exits 3 so the agent can ask the person (it never downloads silently).
"""
import argparse, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STOP = set("a an the and or but if so to of in on at for with from by as is am are was were be been it its this that these those i me my we us our you your he she they them his her their not no do does did have has had will would can could just up down out over into than then there here what when who how all any".split())
THEMES = dict(
    fear="afraid fear scared terror dread horror nightmare scream panic shadow dark darkness haunt ghost monster".split(),
    chase="run running chase chased hunt hunted hunter follow behind catch caught fast hide hiding flee escape".split(),
    death="die dying dead death kill killed grave bury blood bleed cold last end ending final".split(),
    hope="hope hopeful free freedom light live alive survive survived dawn tomorrow morning home".split(),
    fight="fight fighting war battle stand strike break burn rage fury power strong".split(),
    time="time forever eternal eternity never always still again clock tick hour".split(),
    faith="god soul spirit heaven hell pray prayer fate destiny cursed holy".split())


def syllables(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w: return 0
    n = len(re.findall(r"[aeiouy]+", w)); n -= 1 if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1 else 0
    return max(1, n)


def norm(w):
    return re.sub(r"[^a-z']", "", w.lower())


def tail(line):
    ws = [norm(x) for x in line.split() if norm(x)]
    return re.sub(r"[^a-z]", "", ws[-1])[-3:] if ws else ""


def text_stats(lines, words):
    toks = [norm(w) for w in words if norm(w)]; n = max(len(toks), 1); uniq = len(set(toks))
    seen = Counter(" ".join(norm(x) for x in l.split()) for l in lines if l.strip()); rep_lines = sum(c - 1 for c in seen.values() if c > 1); total = max(sum(seen.values()), 1)
    top_line = seen.most_common(1)[0] if seen else ("", 0)
    pairs = [(tail(a), tail(b)) for a, b in zip(lines, lines[1:]) if tail(a) and tail(b)]
    rhyme = sum(1 for a, b in pairs if a[-2:] == b[-2:] and a != "") / max(len(pairs), 1)
    th = {k: sum(1 for w in toks if w in v) for k, v in THEMES.items()}
    return dict(words=len(toks), unique_word_share=round(uniq / n, 2), lines=len(lines), words_per_line_median=int(sorted(len(l.split()) for l in lines)[len(lines) // 2]) if lines else 0,
                repeated_line_share=round(rep_lines / total, 2), hook_line_words=len(top_line[0].split()) if top_line[1] > 1 else 0, hook_repeats=top_line[1] if top_line[1] > 1 else 0,
                rhyme_pair_share=round(rhyme, 2), syllables_per_word=round(sum(syllables(w) for w in toks) / n, 2), theme_word_counts={k: v for k, v in th.items() if v}), toks


def split_lines(words, gap=0.8):
    lines, cur = [], []
    for w in words:
        if cur and w["s"] - cur[-1]["e"] > gap: lines.append(cur); cur = []
        cur.append(w)
    if cur: lines.append(cur)
    return lines


def timing_stats(words, deep, dur):
    lines = split_lines(words); first, last = words[0]["s"], words[-1]["e"]; span = max(last - first, 1e-6); out = dict(
        first_word_s=round(first, 2), last_word_s=round(last, 2), vocal_span_share=round(span / dur, 2) if dur else None, words_per_min=round(len(words) / span * 60, 1),
        syllables_per_sec=round(sum(syllables(w["w"]) for w in words) / span, 2), phrase_count=len(lines), phrase_len_s_median=round(sorted(l[-1]["e"] - l[0]["s"] for l in lines)[len(lines) // 2], 2) if lines else 0,
        gap_s_median=round(sorted(b[0]["s"] - a[-1]["e"] for a, b in zip(lines, lines[1:]))[(len(lines) - 1) // 2], 2) if len(lines) > 1 else None)
    if deep:
        g = deep["grid"]; bar_s = g["bar_s"]; d0 = g["first_downbeat_s"]; bar = lambda t: int((t - d0) // bar_s) + 1
        out["first_word_bar"] = bar(first); out["words_per_bar_median"] = round(sorted(Counter(bar(w["s"]) for w in words).values())[len(set(bar(w["s"]) for w in words)) // 2], 1)
        drops = deep["hard_points"]["drops"]
        if drops:
            d1 = drops[0]["t"]; before = sum(1 for w in words if w["s"] < d1); out["words_before_first_drop"] = before; out["words_after_first_drop"] = len(words) - before
            out["vocal_enters_relative_to_first_drop_bars"] = round((first - d1) / bar_s, 1)
        secs = deep["sections"]; lab = Counter()
        for w in words:
            for s_ in secs:
                if s_["t0"] <= w["s"] < s_["t1"]: lab[s_["label"]] += 1; break
        out["words_by_section_label"] = dict(lab)
        hp = deep["hard_points"]["hits"] + [dict(t=p["t"]) for p in deep["hard_points"]["drops"]]
        near = sum(1 for w in words if any(abs(w["s"] - h["t"]) < 0.15 for h in hp)); out["words_landing_on_hard_points"] = near
        stops = deep["hard_points"]["stops"]; out["words_inside_stops"] = sum(1 for w in words if any(s_["t"] <= w["s"] <= s_["end"] for s_ in stops))
    return out, lines


def transcribe(path, model, language, separate):
    try:
        from faster_whisper import WhisperModel
    except Exception:
        print(json.dumps(dict(needs="whisper", why="lyrics from audio need faster-whisper (optional, ~500 MB for 'small')", install="python3 af.py doctor --install whisper  (ask the person first)",
                              alternatives=["--words words.json (from af.py listen)", "--text lyrics.txt (lyrics you provide: statistics only)"]))); sys.exit(3)
    src = path
    if separate:
        import subprocess, tempfile
        d = tempfile.mkdtemp(); r = subprocess.run([sys.executable, os.path.join(HERE, "separate.py"), path, "--out", d, "--stem", "vocals"], capture_output=True, text=True)
        cand = [os.path.join(d, f) for f in os.listdir(d) if "vocal" in f.lower()] if os.path.isdir(d) else []
        if r.returncode or not cand: sys.exit("separate failed (Demucs is optional, ~1 GB: doctor --install demucs). " + (r.stderr or "")[-200:])
        src = cand[0]
    m = WhisperModel(model, device="cpu", compute_type="int8"); segs, info = m.transcribe(src, language=language, word_timestamps=True, vad_filter=True)
    words = [dict(w=w.word.strip(), s=round(w.start, 3), e=round(w.end, 3)) for s in segs for w in (s.words or [])]
    return words, info.language, float(getattr(info, "language_probability", 0.0))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?"); ap.add_argument("--words"); ap.add_argument("--text"); ap.add_argument("--deep"); ap.add_argument("--model", default="small"); ap.add_argument("--language")
    ap.add_argument("--separate", action="store_true"); ap.add_argument("--keep-text", action="store_true"); ap.add_argument("--out"); ap.add_argument("--name")
    a = ap.parse_args()
    if not (a.audio or a.text): sys.exit(__doc__)
    deep = json.load(open(a.deep)) if a.deep else None; name = a.name or os.path.splitext(os.path.basename(a.audio or a.text))[0]
    name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name).strip("-").lower(); out = a.out or os.path.join("lyrics", name); os.makedirs(out, exist_ok=True)
    lang, prob, source = a.language, None, None
    if a.text:
        lines = [l.strip() for l in open(a.text, encoding="utf-8").read().splitlines() if l.strip()]; words = [w for l in lines for w in l.split()]; wl = None; source = "text file (no timing)"
    else:
        if a.words: wl = json.load(open(a.words)); source = "words.json"
        else: wl, lang, prob = transcribe(a.audio, a.model, a.language, a.separate); source = f"whisper {a.model}" + (" on a Demucs vocal stem" if a.separate else "")
        if not wl: sys.exit("no words found (instrumental, or the vocals were not recognised)")
        tl = split_lines(wl); lines = [" ".join(w["w"] for w in l) for l in tl]; words = [w["w"] for w in wl]
    st, toks = text_stats(lines, words)
    res = dict(schema="audio-forge/lyrics@1", name=name, source=source, language=lang, language_probability=prob, text=st, stored_text=bool(a.keep_text),
               caveat="Whisper on music is approximate; counts are indicative. Statistics only: the lyrics are not stored" + (" (except in lyrics.local.json because --keep-text)" if a.keep_text else "") + ".")
    if wl:
        dur = deep["seconds"] if deep else wl[-1]["e"]; res["timing"], _ = timing_stats(wl, deep, dur)
    json.dump(res, open(os.path.join(out, "lyrics.json"), "w"), indent=1)
    if a.keep_text: json.dump(dict(note="PRIVATE working copy of a transcript. Do not publish, commit or paste it.", words=wl, lines=lines), open(os.path.join(out, "lyrics.local.json"), "w"), indent=1)
    print(json.dumps(res, indent=1)); print(f"[wrote {out}/lyrics.json" + (", lyrics.local.json" if a.keep_text else "") + "]", file=sys.stderr)


if __name__ == "__main__":
    main()

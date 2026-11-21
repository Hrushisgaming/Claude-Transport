#!/usr/bin/env python3
"""feedback.py -- turn a listener's notes (Hydrogen or any listening AI) into changes the composers can apply.

  python3 feedback.py notes.txt --out overrides.json      # then: huntfight.py --apply overrides.json --seed <same seed>
Reads the JSON block that the prompt in TOOLS-GUIDE/HYDROGEN-PROMPT.md asks for (best), or scans prose for known phrases (rough).
Prints what it found, what it will change, and what it could NOT map (those go to a human / the agent as a to-do list).
Output json: {"locks": {...}, "mix_db": {track: dB}, "bpm_delta": n, "advice": [...], "unmapped": [...], "findings": [...]}.
Rules are conservative: nothing is changed that the listener did not ask for, and a listener's NUMBERS (tempo, durations) are never trusted over the analyzer.
"""
import argparse, json, re, sys

TRACKS = {  # words -> mix track names
    "guitar": ["gtrL", "gtrR"], "piano": ["piano", "pianoL"], "bell": ["bell"], "drum": ["kick", "snare"], "beat": ["kick", "snare"], "break": ["kick", "snare"],
    "bass": ["bass", "sub"], "sub": ["sub"], "choir": ["choir"], "string": ["strings"], "pad": ["choir", "strings"], "lead": ["sqlead"], "synth": ["sqlead"],
    "square": ["sqlead"], "sfx": ["sfx"], "crawl": ["sfx"], "static": ["sfx"], "hat": ["hat"], "clock": ["clock"], "chime": ["chime"], "heartbeat": ["heart"],
}
UP = r"\b(louder|more (present|forward|aggressive|audible|prominent)|forward|front|stronger|clearer|boost|bring up|up in the mix|punch|harder|heavier|bigger|buried|drowned( out)?|lost|hard to hear|can.?t hear)\b"
DOWN = r"\b(quieter|too loud|too prominent|less|softer|lower|turn down|pull back|overpowering)\b"


def find_json(text):
    for m in re.finditer(r"\{", text):
        depth = 0
        for i in range(m.start(), len(text)):
            depth += text[i] == "{"; depth -= text[i] == "}"
            if depth == 0:
                try:
                    j = json.loads(text[m.start():i + 1])
                    if isinstance(j, dict) and ("top_changes" in j or "heard_as" in j or "instrument_verdicts" in j): return j
                except Exception: pass
                break
    return None


RECIPE_RULES = [   # (regex on the whole reply, recipe fields to set): conservative, each tied to a phrase a listener actually wrote
    (r"heroic|triumphant|semitone lift|key lift|\+1 semitone", {"lift": "none"}, "a heroic key lift was heard: lift removed"),
    (r"stiff\s+(dnb|drum)|dnb\s+loop|(dnb).{0,60}(stiff|mechanical|loop)", {"drums_c": "amen"}, "a stiff DnB loop was heard: drop C uses chopped Amen"),
    (r"(square|arcade|retro).{0,40}(lead|stab|synth)|(lead|synth).{0,40}(arcade|retro|square)", {"lead": "bend_lead"}, "retro/arcade square lead: pitch-bent distorted saw"),
    (r"warm\s+(choir|pad)|choir.{0,30}warm|cold.{0,20}tremolo strings", {"pads": "trem_strings"}, "warm choir/pad: cold tremolo strings"),
    (r"bright\s+chimes?|downbeat.{0,30}bell|bells?.{0,40}(downbeat|predictable)|church bell", {"bell": "bell_church", "bell_pattern": "accents"}, "bright/predictable bells: low church bell on accents only"),
    (r"piano.{0,40}(bright|clean)|bright.{0,20}piano", {"piano": "piano_dark"}, "bright piano: dark low piano"),
    (r"guitars?.{0,50}(block|flat|fuzz)|syncopated.{0,30}(riff|chug)|palm-?muted.{0,30}riff", {"riff_a": "syncopated", "riff_c": "tritone"}, "block-chord guitars: syncopated / tritone riffs"),
    (r"bass.{0,40}(buried|mud)|reese", {"reese": True}, "buried bass: reese layer on"),
    (r"add\s+(a\s+)?low\s+(distorted\s+)?(cathedral\s+)?organ|low organ", {"organ_low": True}, "listener asked for a low organ: optional dark organ on"),
    (r"(dark|low)\s+brass\s+(stabs?|swells?)", {"brass_low": True}, "listener asked for dark low brass: optional brass stab on"),
]


def mix_from_sentence(s, out):
    low = s.lower(); hit = False; done = {}
    for word, tracks in TRACKS.items():
        i = low.find(word)
        if i < 0: continue
        seg = low[i:i + 90]
        d = -3.0 if re.search(DOWN, seg) else 3.0 if re.search(UP, seg) else 0.0
        if d:
            for t in tracks: done.setdefault(t, d)     # one change per track per sentence (drum/beat/break all mean kick+snare)
            hit = True
    for t, d in done.items(): out["mix_db"][t] = out["mix_db"].get(t, 0.0) + d
    return hit


def analyse(text):
    out = {"locks": {}, "recipe": {}, "mix_db": {}, "bpm_delta": 0, "advice": [], "unmapped": [], "findings": []}
    for pat, fields, why in RECIPE_RULES:
        if re.search(pat, text, re.I): out["recipe"].update(fields); out["findings"].append(why)
    j = find_json(text)
    sentences = []
    if j:
        out["findings"].append("structured JSON block found")
        h = str(j.get("heard_as", "")).lower()
        if h in ("happy", "heroic", "triumphant", "calm", "cheerful", "neutral"):
            out["findings"].append(f"heard as {h}: not hunted")
            out["advice"].append("Mood is wrong: check the recipe for major chords, brass, organ, glockenspiel, key lift, rising hero melody (the hunted mood forbids them); raise dread: drone, crawl SFX, choir, cold piano.")
            out["locks"].update(lift="none"); out["mix_db"].update(sfx=2.0, choir=1.5)
        e = str(j.get("ending_feels", "")).lower()
        if e in ("win", "peaceful", "neutral"):
            out["findings"].append(f"ending feels like {e}"); out["locks"]["ending"] = "tape_stop_hit"
        g = str(j.get("groove_feel", "")).lower()
        if g in ("bouncy", "laid-back", "half-time"):
            out["findings"].append(f"groove feels {g}"); out["locks"]["drums"] = "amen"; out["bpm_delta"] += 4
            out["advice"].append("Groove is not relentless: amen breakbeat locked, +4 BPM. Remove half-time sections if the listener keeps hearing half-time.")
        bpm = j.get("tempo_estimate_bpm")
        if isinstance(bpm, (int, float)) and bpm < 150:
            out["advice"].append(f"Listener estimates {bpm} BPM; the analyzer says the real tempo (check with af.py deep). A listener's tempo is a FEEL, usually half-time or off; do not change BPM on this alone.")
        for name, v in (j.get("instrument_verdicts") or {}).items():
            if isinstance(v, dict):
                if v.get("fits_target") is False: out["advice"].append(f"{name} does not fit: {v.get('change', '')}")
                if v.get("change"): sentences.append(f"{name} {v.get('change', '')}")
                if str(v.get("sounds", "")).lower() == "fake": out["advice"].append(f"{name} sounds fake: try the other voice for it (see instrument_showcase).")
        for c in j.get("top_changes") or []:
            sentences.append(f"{c.get('instrument', '')} {c.get('change', '')}")
        for c in j.get("variation_complaints") or []: out["advice"].append(f"samey: {c} -> run without --seed, or change the locked values.")
        for u in j.get("unsure") or []: out["findings"].append(f"listener unsure: {u}")
    else:
        out["findings"].append("no JSON block: scanned prose (rough). Use the prompt in TOOLS-GUIDE/HYDROGEN-PROMPT.md for reliable results.")
        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        low = text.lower()
        for pat, msg in ((r"\bhappy|cheerful|cozy|triumph|heroic", "listener hears happy/heroic parts"), (r"bouncy|danceable", "listener hears a bouncy groove"), (r"peaceful|resolved chord|fade", "listener mentions a peaceful/resolved ending")):
            if re.search(pat, low): out["findings"].append(msg)
    for s in sentences:
        s = s.strip()
        if len(s) < 8: continue
        low = s.lower()
        if mix_from_sentence(s, out): continue
        m = re.search(r"(faster|speed up|more urgent|more frantic)", low)
        if m: out["bpm_delta"] += 4; continue
        if re.search(r"(remove|delete|drop|no)\s+(the\s+)?(warm\s+)?(organ|brass|glockenspiel|celesta|pads?)", low): out["advice"].append(f"already excluded by the hunted mood: {s[:100]}"); continue
        if re.search(r"(tape.?stop|blunt|cut dead|collapse)", low): out["locks"].setdefault("ending", "tape_stop_hit"); continue
        out["unmapped"].append(s[:160])
    for k in list(out["mix_db"]): out["mix_db"][k] = max(-3.0, min(3.0, out["mix_db"][k]))   # prose mode can match many sentences: never move a track more than 3 dB per round
    out["unmapped"] = [u for u in out["unmapped"] if len(u) > 20][:25]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("notes"); ap.add_argument("--out", default="overrides.json"); a = ap.parse_args()
    text = sys.stdin.read() if a.notes == "-" else open(a.notes, encoding="utf-8", errors="replace").read()
    r = analyse(text); json.dump(r, open(a.out, "w"), indent=1)
    print("FINDINGS:"); [print("  -", f) for f in r["findings"]]
    print("WILL CHANGE: recipe", r["recipe"], "| locks", r["locks"], "| mix_db", r["mix_db"], "| bpm_delta", r["bpm_delta"])
    print("ADVICE:"); [print("  -", x) for x in r["advice"]]
    print("NOT MAPPED (read these yourself):"); [print("  -", x) for x in r["unmapped"][:12]]
    print("wrote", a.out)


if __name__ == "__main__":
    main()

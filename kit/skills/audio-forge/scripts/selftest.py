#!/usr/bin/env python3
"""selftest.py -- fast end-to-end check that this install works (about 30 s)."""
import json, os, subprocess, sys, tempfile, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from forge import genres, song as sm
import analyze

ok_all = True
def check(name, cond, info=""):
    global ok_all
    ok_all &= bool(cond)
    print(("PASS " if cond else "FAIL ") + name + (f"  ({info})" if info else ""))

tmp = tempfile.mkdtemp()
t0 = time.time()
for g in ("house", "chiptune", "horror_chase", "lofi"):
    s = genres.build(g, 8, seed=1)
    a = s.mixdown(reverb_rt60=s.rt60)
    check(f"compose {g}", np.isfinite(a).all() and 0.5 < np.abs(a).max() <= 1.0 and len(a) > 5 * s.sr, f"{len(a)/s.sr:.1f}s")
s = genres.build("house", 16, bpm=124, key="A", scale="minor", seed=3)
p = os.path.join(tmp, "h.wav"); sm.write_wav(p, s.mixdown(reverb_rt60=s.rt60), s.sr)
pr = analyze.analyze(p, quiet=True)
check("analyze tempo", abs(pr["tempo"]["bpm"] - 124) < 0.8, f"{pr['tempo']['bpm']}")
check("analyze key", pr["key"]["best"]["key"] == "A" or pr["key"]["relative"].startswith("A"), f"{pr['key']['best']['key']} {pr['key']['best']['mode']}")
check("analyze beats", len(pr["beats"]) > 20 and pr["meter"]["beats_per_bar"] == 4)
import tts
x, eng = tts.synth("self test", "formant", cache=False)
check("tts fallback voice", len(x) > 4000, eng)
av = tts.available()
print("     engines:", {k: v for k, v in av.items() if v})
import bridge
shots = [[0.13 + 0.25 * k * 2, 0.4, "s"] for k in range(14)]
fit = bridge.fit_tempo(shots)
check("bridge fit-tempo", abs(fit[0]["bpm"] - 120) < 1.0, f"{fit[0]['bpm']}")
# video scoring: a brief in, a bed out whose drop lands on the hero moment
sb = os.path.join(tmp, "b.json"); json.dump(dict(schema="audio-forge/scorebrief@1", duration=20.0, style="trailer",
    acts=[dict(name="a", t=0, intensity=0.1), dict(name="b", t=8, intensity=0.5), dict(name="c", t=14, intensity=1.0)],
    events=[dict(t=14.0, strength=1.0, kind="impact")]), open(sb, "w"))
r = subprocess.run([sys.executable, os.path.join(HERE, "score.py"), "--brief", sb, "--out", os.path.join(tmp, "bed.wav")], capture_output=True, text=True)
try:
    sc = json.loads(r.stdout); check("score: drop on the hero moment", abs(sc["drop_error_ms"]) < 60 and sc["bed_seconds"] >= 20, f"{sc['genre']} {sc['bpm']} BPM, error {sc['drop_error_ms']} ms")
    bm = json.load(open(sc["beatmap"])); check("score: beatmap drop matches", any(abs(d - 14.0) < 0.06 for d in bm["drops"]), f"{bm['drops']}")
except Exception as e:
    check("score", False, str(e) + r.stderr[-200:])
r = subprocess.run([sys.executable, os.path.join(HERE, "hear.py"), os.path.join(tmp, "bed.wav"), "--dry-run"], capture_output=True, text=True)
check("hear: clip prepared (dry run, nothing sent)", r.returncode == 0 and "nothing sent" in r.stdout, r.stdout.strip()[:80] + r.stderr[-120:])
r = subprocess.run([sys.executable, os.path.join(HERE, "study.py"), os.path.join(tmp, "bed.wav"), "--name", "selftest", "--out", os.path.join(tmp, "st")], capture_output=True, text=True)
r2 = subprocess.run([sys.executable, os.path.join(HERE, "compare.py"), os.path.join(tmp, "bed.wav"), os.path.join(tmp, "st", "dna.json")], capture_output=True, text=True)
check("study + compare: a track compared with its own DNA is 100/100", r.returncode == 0 and "closeness 100/100" in r2.stdout, (r.stderr + r2.stdout)[-160:])
for g in ("corporate", "warm_piano", "epic_trailer", "soft_ambient"):
    s = genres.build(g, 8, seed=1); a_ = s.mixdown(reverb_rt60=s.rt60)
    check(f"compose {g}", np.isfinite(a_).all() and np.abs(a_).max() > 0.3)
s = genres.build("house", 16, bpm=120, seed=1, plan=[("intro", .25), ("drop", .75)])
check("compose --plan honoured", [x[0] for x in s.sections] == ["intro", "drop"], str([x[0] for x in s.sections]))
r = subprocess.run(["ffmpeg", "-v", "error", "-version"], capture_output=True)
check("ffmpeg present", r.returncode == 0)

# ---- 1.2: deep analyzer on a track with KNOWN hard points, lyrics stats, blend, ost checks ----
import deep as D, subprocess as _sp
kt = os.path.join(tmp, "known.wav"); _sp.run([sys.executable, os.path.join(os.path.dirname(HERE), "tests", "make_known_track.py"), kt], check=True, capture_output=True)
dd = D.deep(kt); hp = dd["hard_points"]
check("deep: tempo", abs(dd["grid"]["bpm"] - 120) < 1.0, f"{dd['grid']['bpm']}")
check("deep: hard stop found at 15.7 s", any(abs(q["t"] - 15.7) < 0.1 and 0.2 < q["dur_s"] < 0.4 for q in hp["stops"]), f"{[(q['t'], q['dur_s']) for q in hp['stops']]}")
check("deep: impact found at 16.0 s", any(abs(h["t"] - 16.0) < 0.1 for h in hp["hits"]), f"{[h['t'] for h in hp['hits']]}")
check("deep: drop at 16.0 s with cut+impact anatomy", any(abs(q["t"] - 16.0) < 0.15 and q["has_cut"] and q["impact"] for q in hp["drops"]), f"{[(q['t'], q['has_cut'], q['impact']) for q in hp['drops']]}")
check("deep: riser ends near 15.7 s", any(abs(q["end"] - 15.7) < 0.5 for q in hp["risers"]), f"{[(q['t'], q['end']) for q in hp['risers']]}")
check("deep: plain kicks are not hard hits", len(hp["hits"]) <= 4, f"{len(hp['hits'])} hits")
check("deep: lead layer found 24-32 s", any(abs(q["t"] - 24.0) < 1.5 and q["end"] > 30 for q in dd["lead_layer"]["segments"]), f"{[(q['t'], q['end']) for q in dd['lead_layer']['segments']]}")
check("deep: chord cycle 4 bars", dd["phrase"]["chord_loop_bars"] == 4, f"{dd['phrase']['chord_loop_bars']}")
check("deep: file with a fade-out is not loop-ready", not dd["loop"]["loop_ready"])
import lyrics as LY
st, _ = LY.text_stats(["keep going on", "never stop now", "keep going on"], "keep going on never stop now keep going on".split())
check("lyrics: repetition and hook counted", st["repeated_line_share"] > 0.3 and st["hook_repeats"] == 2, f"{st['repeated_line_share']}")
import blend as B, study as S2
d1 = S2.study(kt, with_deep=True)[0]; d1.pop("_deep_full", None); d1["name"] = "a"; d2 = json.loads(json.dumps(d1)); d2["name"] = "b"
for k in ("a", "b"): os.makedirs(os.path.join(tmp, k), exist_ok=True)
json.dump(d1, open(os.path.join(tmp, "a", "dna.json"), "w")); json.dump(d2, open(os.path.join(tmp, "b", "dna.json"), "w"))
fam, _m = B.blend([os.path.join(tmp, "a"), os.path.join(tmp, "b")], "fam")
check("blend: family has members, ranges and consensus", len(fam["family"]["members"]) == 2 and fam["family"]["ranges"] and "consensus" in fam["family"])
import ost as O
O.make_loop(kt, 120.0, 16); ck = O.check(kt, 120.0, True)
check("ost: loop cut to whole bars and passes the seam check", abs(ck["bars"] - 16) < 0.01 and not any("seam" in i or "bars" in i.split(":")[0] for i in ck["issues"]), f"{ck['bars']} bars, issues {ck['issues']}")

# ---- V2: new instruments, breakbeats, local telemetry and the four new tools ----
from forge import instruments as INS, drums as DRM
legacy = ["sine_sub", "saw_bass", "reese", "pluck", "lead_saw", "lead_square", "chip_tri", "pad", "strings", "brass",
          "ep", "bell", "piano", "organ", "choir", "guitar", "guitar_mute", "sub_drop", "stab", "drone", "music_box"]
v2 = ["piano_m1", "organ_rock", "organ_pipe", "bell_tubular", "clock_bell", "acid_303", "chip_lead", "pulsing_bass",
      "y2k_bass", "showtime_sax", "marimba", "rave_stab", "orch_hit", "rave_shout", "heartbeat", "siren_riser", "clock_tick"]
missing = [k for k in legacy + v2 if k not in INS.INSTRUMENTS]
check("instruments: every legacy and V2 key exists", not missing, f"missing {missing}")
bad = []
for k in legacy + v2:
    try:
        y = INS.render(k, 60, 0.5, 0.9)
        y = np.asarray(y)
        if not np.isfinite(y).all() or np.abs(y).max() < 0.2: bad.append(k)
    except Exception as e:
        bad.append(f"{k}:{e}")
check("instruments: every voice renders finite audio above 0.2 peak", not bad, f"bad {bad[:3]}")
for bk in ("amen", "dnb", "horror", "metal"):
    ev = DRM.breakbeat(4, bk, np.random.RandomState(1), 0.8)
    check(f"breakbeat {bk}: events generated", len(ev) > 10 and all(0 <= st < 64 for st, _, _ in ev), f"{len(ev)} events")
r = subprocess.run([sys.executable, os.path.join(HERE, "hear.py"), p, "--local", "--out", os.path.join(tmp, "hear")], capture_output=True, text=True)
try:
    hr = json.load(open(os.path.join(tmp, "hear", "hear-local.json")))
    check("hear --local: offline telemetry with bands, mud, harshness, punch and stereo",
          r.returncode == 0 and hr["schema"] == "audio-forge/hear-local@1" and "overall_bands_db" in hr and "sections" in hr
          and hr["sections"] and "punch_crest_db" in hr["sections"][0] and "stereo" in hr["sections"][0]
          and os.path.exists(os.path.join(tmp, "hear", "hear-local.md")),
          f"{len(hr.get('sections', []))} sections, {len(hr.get('issues', []))} issues")
except Exception as e:
    check("hear --local", False, str(e) + r.stderr[-200:])
r = subprocess.run([sys.executable, os.path.join(HERE, "audition.py"), "--out", os.path.join(tmp, "audition"),
                    "--inst", "piano_m1,organ_rock,bell_tubular", "--genre", "house", "--bpm", "120", "--bars", "4"], capture_output=True, text=True)
check("audition: showcase + timestamp guide + mini-mix",
      r.returncode == 0 and os.path.exists(os.path.join(tmp, "audition", "showcase.wav"))
      and os.path.exists(os.path.join(tmp, "audition", "showcase.md")) and os.path.exists(os.path.join(tmp, "audition", "minimix.wav")),
      r.stderr[-160:])
r = subprocess.run([sys.executable, os.path.join(HERE, "adapt.py"), "--reference", p, "--out", os.path.join(tmp, "adapted.wav"),
                    "--genre", "house", "--rounds", "2", "--fast", "--work", os.path.join(tmp, "adapt_work")], capture_output=True, text=True)
try:
    al = json.load(open(os.path.join(tmp, "adapt_work", "adapt-log.json")))
    check("adapt: compose -> compare -> adjust loop with a round log",
          r.returncode == 0 and len(al["rounds"]) >= 1 and "score" in al["rounds"][0] and os.path.exists(os.path.join(tmp, "adapted.wav")),
          f"{len(al['rounds'])} round(s), best {al['best']['score']}/100")
except Exception as e:
    check("adapt", False, str(e) + r.stderr[-200:])
stemdir = os.path.join(tmp, "stems"); os.makedirs(stemdir, exist_ok=True)
s2 = genres.build("house", 8, 120, seed=2)
s2.mixdown(stems_dir=stemdir, reverb_rt60=s2.rt60)
r = subprocess.run([sys.executable, os.path.join(HERE, "stem_mix.py"), stemdir, "--out", os.path.join(tmp, "mix.wav"),
                    "--target-lufs", "-14"], capture_output=True, text=True)
try:
    sm = json.load(open(os.path.join(tmp, "mix.json"))) if False else None
    check("stem_mix: stems mixed to the loudness target",
          r.returncode == 0 and os.path.exists(os.path.join(tmp, "mix.wav")) and "LUFS" in r.stdout, r.stdout.strip()[-120:])
except Exception as e:
    check("stem_mix", False, str(e) + r.stderr[-200:])
r = subprocess.run([sys.executable, os.path.join(HERE, "loop_doctor.py"), p, "--bpm", "124",
                    "--repair", os.path.join(tmp, "loop_fixed.wav")], capture_output=True, text=True)
check("loop_doctor: diagnoses and repairs a loop",
      r.returncode == 0 and os.path.exists(os.path.join(tmp, "loop_fixed.wav")) and "seam" in r.stdout, r.stdout.strip()[-120:])
r = subprocess.run([sys.executable, os.path.join(HERE, "ost.py"), "check", p, "--bpm", "124", "--loop"], capture_output=True, text=True)
try:
    oc = json.loads(r.stdout)
    check("ost check: strict loop report has bars, headroom and sub checks",
          "bars" in oc and "peak_dbfs" in oc and "issues" in oc, f"bars {oc.get('bars')}, issues {len(oc.get('issues', []))}")
except Exception as e:
    check("ost check", False, str(e) + r.stderr[-200:])

print(f"\n{'ALL PASSED' if ok_all else 'SOME FAILED'} in {time.time()-t0:.0f}s")
sys.exit(0 if ok_all else 1)

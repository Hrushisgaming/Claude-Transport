#!/usr/bin/env python3
"""study_video.py - measure the EDITING / ANIMATION style of a reference video and write a Style DNA + a brief any model can follow.

  study_video.py ref.mp4 --name my-style [--out styles/my-style] [--kind edit|animation]
  study_video.py --compare candidate.mp4|dna.json reference.mp4|dna.json

Writes <out>/dna.json (style-copy/video-dna@1), brief.md, contact.jpg (one frame per shot: for models that can SEE images), preset.json
(a draft cinematic-edit style: copy it to ~/.config/cinematic-edit/styles/ to use `analyze.py --style NAME`).

WHAT IS AND IS NOT COPIED: measurements only (cut rhythm, shot lengths, camera/subject motion, flash and shake rate, frame cadence, colour
palette and grade, contrast, vignette, letterbox, line/edge density, loudness, music tempo). No footage, characters, logos, text or music is
stored or reproduced. What cannot be measured here (on-screen text, the subject, jokes) is listed as UNKNOWN: ask the person or look at contact.jpg.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ce_common import probe
import looks as L

W, H = 192, 108


def sample_frames(path, fps_s, dur, n_full=0):
    cap = cv2.VideoCapture(path); fps = cap.get(cv2.CAP_PROP_FPS) or 30.0; step = max(1, int(round(fps / fps_s))); fr, t, i = [], [], 0
    while True:
        ok, f = cap.read()
        if not ok: break
        if i % step == 0: fr.append(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA)); t.append(i / fps)
        i += 1
    cap.release(); return fr, np.array(t), fps


def cuts_from(fr):
    hs = [cv2.calcHist([cv2.cvtColor(f, cv2.COLOR_BGR2HSV)], [0, 1], None, [16, 8], [0, 180, 0, 256]) for f in fr]; d = []
    for a, b in zip(hs, hs[1:]):
        a = a / (a.sum() + 1e-9); b = b / (b.sum() + 1e-9); d.append(1 - float(np.minimum(a, b).sum()))
    d = np.array(d); thr = max(0.35, float(np.median(d) + 5 * (np.median(np.abs(d - np.median(d))) + 1e-3))); return [i + 1 for i in range(len(d)) if d[i] > thr and d[i] == d[max(0, i - 2):i + 3].max()], d


def cadence(path, fps, start_s, n=120):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_s * fps)); prev, same, runs, cur = None, 0, [], 1; cnt = 0
    while cnt < n:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(f, (W, H)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            if np.abs(g - prev).mean() < 0.35: same += 1; cur += 1
            else: runs.append(cur); cur = 1
        prev = g; cnt += 1
    cap.release(); runs.append(cur); hold = int(np.bincount(runs).argmax()) if runs else 1
    return dict(duplicate_frame_share=round(same / max(cnt - 1, 1), 2), typical_hold_frames=hold, effective_fps=round(fps / max(hold, 1), 1))


def palette(frames, k=5):
    px = np.concatenate([cv2.cvtColor(f[::3, ::3], cv2.COLOR_BGR2LAB).reshape(-1, 3) for f in frames[::max(1, len(frames) // 40)]]).astype(np.float32)
    _, lab, c = cv2.kmeans(px, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 12, 1.0), 2, cv2.KMEANS_PP_CENTERS)
    share = np.bincount(lab.flatten(), minlength=k) / len(lab); out = []
    for i in np.argsort(-share):
        bgr = cv2.cvtColor(c[i].astype(np.uint8).reshape(1, 1, 3), cv2.COLOR_LAB2BGR)[0, 0]; out.append(dict(hex="#%02x%02x%02x" % (bgr[2], bgr[1], bgr[0]), share=round(float(share[i]), 2)))
    return out


def grade(frames):
    hsv = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2HSV) for f in frames[::max(1, len(frames) // 60)]]); S, V = hsv[..., 1] / 255.0, hsv[..., 2] / 255.0
    bgr = np.stack(frames[::max(1, len(frames) // 60)]).astype(np.float32) / 255.0; warm = float((bgr[..., 2] - bgr[..., 0]).mean())
    edge = V[:, :, :12].mean() + V[:, :, -12:].mean(); centre = V[:, 40:70, 70:120].mean() * 2
    g = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames[::max(1, len(frames) // 60)]]); rows = (g.mean(axis=2) < 12).mean(axis=0)
    lb = float(max(0.0, min(0.3, (rows[: H // 4] > 0.9).sum() / H)))
    return dict(saturation=round(float(S.mean()), 3), brightness=round(float(V.mean()), 3), contrast=round(float(V.std()), 3), warmth=round(warm, 3),
                vignette=round(float(1 - edge / (centre + 1e-9)), 2), letterbox=round(lb, 2), black_share=round(float((V < 0.06).mean()), 3))


def line_style(frames):
    ed, thick = [], []
    for f in frames[::max(1, len(frames) // 40)]:
        g = cv2.cvtColor(cv2.resize(f, (480, 270)), cv2.COLOR_BGR2GRAY); e = cv2.Canny(g, 60, 140); ed.append((e > 0).mean())
        dark = (g < 70).astype(np.uint8)
        if dark.sum() > 50: dt = cv2.distanceTransform(dark, cv2.DIST_L2, 3); thick.append(float(np.percentile(dt[dt > 0], 75) * 2))
    return dict(edge_density=round(float(np.mean(ed)), 4), ink_stroke_px_at_270p=round(float(np.median(thick)), 1) if thick else None)


def flash_shake(fr, t):
    v = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean() for f in fr]); dv = np.abs(np.diff(v)); fl = int(((dv > 18) & (np.arange(len(dv)) % 1 == 0)).sum() / 2)
    sh = []
    for a, b in zip(fr[::1], fr[1:]):
        (dx, dy), _ = cv2.phaseCorrelate(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32), cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)); sh.append(np.hypot(dx, dy))
    sh = np.array(sh); return fl, sh


def contact(path, fr, t, cuts, out, maxn=16):
    starts = [0] + cuts; pick = starts if len(starts) <= maxn else [starts[i] for i in np.linspace(0, len(starts) - 1, maxn).astype(int)]
    tiles = [cv2.resize(fr[min(i + 1, len(fr) - 1)], (320, 180)) for i in pick]
    while len(tiles) % 4: tiles.append(np.zeros((180, 320, 3), np.uint8))
    rows = [np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]; cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])


def nearest_look(g):
    best, bs = "natural", 1e9
    sat_f = g["saturation"] / 0.33; con_f = g["contrast"] / 0.25
    for n, p in L.LOOKS.items():
        tint = (p["hi"][0] - p["hi"][2]) + (p["sh"][0] - p["sh"][2]); w = g["warmth"] * 4
        d = abs(p["sat"] - sat_f) * 1.2 + abs(p["con"] - con_f) + abs(tint - w) * 2 + abs(p["bri"] - 1.0) * 0.3
        if d < bs: best, bs = n, d
    return best


def study(path, kind=None):
    info = probe(path); D = info["duration"]; fr, t, fps = sample_frames(path, 6, D)
    cuts, dd = cuts_from(fr); times = [0.0] + [float(t[i]) for i in cuts] + [D]; lens = np.diff(times)
    fl, sh = flash_shake(fr, t); mot = [float(np.mean([np.abs(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32) - cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32)).mean() for a, b in zip(fr[s:e], fr[s + 1:e])])) for s, e in zip([0] + cuts, cuts + [len(fr)]) if e - s > 2] or [0.0]
    cad = cadence(path, fps, min(D * 0.4, max(0, D - 6))); g = grade(fr); ls = line_style(fr); pal = palette(fr)
    kind = kind or ("animation" if (cad["duplicate_frame_share"] > 0.3 and ls["edge_density"] > 0.01) else "edit")
    dna = dict(schema="style-copy/video-dna@1", name=os.path.splitext(os.path.basename(path))[0], kind=kind, seconds=round(D, 1), size=[info["width"], info["height"]], fps=round(fps, 2),
               cutting=dict(shots=len(lens), cuts_per_min=round(60 * (len(lens) - 1) / D, 1), shot_len_mean=round(float(lens.mean()), 2), shot_len_median=round(float(np.median(lens)), 2),
                            shot_len_p10=round(float(np.percentile(lens, 10)), 2), shot_len_p90=round(float(np.percentile(lens, 90)), 2), first_shot=round(float(lens[0]), 2)),
               motion=dict(subject_motion=round(float(np.mean(mot)), 2), camera_shift_px_per_s=round(float(sh.mean() * 6), 2), shake_spikes_per_min=round(float((sh > 3.0).sum() * 60 / D), 1), flashes_per_min=round(fl * 60 / D, 1)),
               cadence=cad, grade=dict(g, nearest_look_GUESS=nearest_look(g)), palette=pal, line=ls, unknown=["on-screen text / captions", "what the subject is", "jokes / story", "music melody (never copied)"])
    if info["has_audio"]:
        wav = tempfile.mktemp(suffix=".wav")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-vn", "-ar", "44100", "-ac", "2", wav], capture_output=True)
        try:
            import audioforge; af = audioforge.find_af()
            if af:
                out = tempfile.mkdtemp(); r = subprocess.run([sys.executable, os.path.join(af, "scripts", "af.py"), "study", wav, "--name", "audio", "--out", out], capture_output=True, text=True)
                if os.path.exists(os.path.join(out, "dna.json")): dna["audio"] = json.load(open(os.path.join(out, "dna.json")))
        except Exception: pass
    return dna, (fr, t, cuts)


def preset_from(d, name):
    c, m, g = d["cutting"], d["motion"], d["grade"]; per_min = int(max(0, min(30, round(0.35 * c["cuts_per_min"] + m["flashes_per_min"] + m["shake_spikes_per_min"] * 0.5))))
    mode = "none" if per_min == 0 else "beats" if d.get("audio") and d["audio"]["rhythm"]["grid_confidence"] > 0.6 and c["cuts_per_min"] > 20 else "moments"
    look = g["nearest_look_GUESS"]
    return dict(name=name, about=f"measured from a reference ({d['kind']}); starting point", format="9:16" if d["size"][1] > d["size"][0] else "16:9", reframe=dict(mode="cover", x=0.5, bg="blur"),
                look=dict(grain=0.05, vignette=max(0.0, min(0.7, g["vignette"])), bloom=0.2, letterbox=g["letterbox"], beat_zoom=0.02 if per_min > 8 else 0.0),
                acts=[dict(name="all", f=0, look=look, drone=0.2, heart_bpm=0)],
                events=dict(mode=mode, per_min=per_min, gap=round(max(0.4, c["shot_len_median"] * 0.8), 2), big_frac=0.1, ramps=1 if per_min > 8 else 0, riser=0.8,
                            fx_big=["punch", "flash", "shake"], fx_mid=["punch"], fx_small=["punch"], sfx=["impact", "boom", "tick"], every=2 if c["cuts_per_min"] > 25 else 4),
                visualizer=None, audio=dict(game_db=-6, music_db=-10, duck_db=-6, sfx_db=-6, lufs=(d.get("audio") or {}).get("mix", {}).get("lufs") or -14, mode="music" if d.get("audio") else "hybrid"),
                pacing=f"median shot {c['shot_len_median']} s, {c['cuts_per_min']} cuts/min (measured)", workflow=["analyze --style", "preview", "final", "export"])


def brief_md(d, name):
    c, m, g, cad, ln, pal = d["cutting"], d["motion"], d["grade"], d["cadence"], d["line"], d["palette"]
    L_ = [f"# Style brief: {name} ({d['kind']})", "", "Made by `study_video.py` from measurements only. Nothing was watched: where it says GUESS or UNKNOWN, look at `contact.jpg` (if you can see images) or ask the person. No footage, characters, text or music of the reference are stored.", "",
          "## 1. Numbers to hit (check with `study_video.py --compare`)", "| what | target |", "|---|---|",
          f"| cutting | {c['shots']} shots, **{c['cuts_per_min']} cuts/min**, shot length median {c['shot_len_median']} s (mean {c['shot_len_mean']}, fastest tenth under {c['shot_len_p10']} s, slowest tenth over {c['shot_len_p90']} s), first shot {c['first_shot']} s |",
          f"| motion | subject motion {m['subject_motion']}, camera shift {m['camera_shift_px_per_s']} px/s (at 192 px wide), shake spikes {m['shake_spikes_per_min']}/min, flashes {m['flashes_per_min']}/min |",
          f"| frame cadence | {cad['duplicate_frame_share']} of frames are repeats; typical hold **{cad['typical_hold_frames']} frame(s)**, i.e. drawn at about {cad['effective_fps']} fps inside a {d['fps']} fps file |",
          f"| colour | saturation {g['saturation']}, brightness {g['brightness']}, contrast {g['contrast']}, warmth {g['warmth']} (R minus B), vignette {g['vignette']}, letterbox {g['letterbox']}, near-black share {g['black_share']}; nearest cinematic-edit look (GUESS): **{g['nearest_look_GUESS']}** |",
          "| palette (share) | " + ", ".join(f"{p['hex']} ({int(p['share'] * 100)}%)" for p in pal) + " |",
          f"| line / ink | edge density {ln['edge_density']}, ink stroke about {ln['ink_stroke_px_at_270p']} px at 480x270 |"]
    if d.get("audio"): a = d["audio"]; L_ += [f"| audio | {a['tempo']['bpm']} BPM, {a['key']['tonic']} {a['key']['mode']}, {a['mix']['lufs']} LUFS (copy the audio style with `af.py study` / the style-copy skill) |"]
    L_ += ["", "## 2. UNKNOWN (cannot be measured here)", *[f"- {u}" for u in d["unknown"]], "",
           "## 3. How to build it", f"1. Copy `preset.json` to `~/.config/cinematic-edit/styles/{name}.json` (or use the shipped style if one exists).",
           f"2. `analyze.py your.mp4 --out work --plan plan.json --style {name}`; edit the plan by hand (the preset is a start).",
           "3. Render a preview, then `study_video.py --compare preview.mp4 " + name + "/dna.json`; change ONE thing per round (cut rate = events.per_min / gap; grade = acts[].look; frame cadence = hold frames), at most 5 rounds.",
           "4. Animation styles: match the typical hold (e.g. animate on 2s), stroke weight, palette and shot length BEFORE detail; use `2d-animation-long-form-aivxer` for the drawing itself and keep its original-characters rule.",
           "5. Report the numbers that match and the ones still off. Say you have not watched it; the person judges.", "",
           "## 4. Do not", "- Do not copy footage, characters, logos, text or the soundtrack. Copy the way it is cut, moved, coloured and timed."]
    return "\n".join(L_) + "\n"


def compare(a, b):
    A = json.load(open(a)) if a.endswith(".json") else study(a)[0]; B = json.load(open(b)) if b.endswith(".json") else study(b)[0]
    rows = [("cuts per minute", B["cutting"]["cuts_per_min"], A["cutting"]["cuts_per_min"], 15, 35, "events.per_min / gap, or cut more/less"), ("median shot (s)", B["cutting"]["shot_len_median"], A["cutting"]["shot_len_median"], 20, 45, "shot length"),
            ("subject motion", B["motion"]["subject_motion"], A["motion"]["subject_motion"], 25, 50, "speed ramps / punch"), ("shake spikes/min", B["motion"]["shake_spikes_per_min"], A["motion"]["shake_spikes_per_min"], 40, 80, "shake fx"),
            ("flashes/min", B["motion"]["flashes_per_min"], A["motion"]["flashes_per_min"], 40, 80, "flash fx"), ("typical hold (frames)", B["cadence"]["typical_hold_frames"], A["cadence"]["typical_hold_frames"], 0, 0.01, "animate on that hold"),
            ("saturation", B["grade"]["saturation"], A["grade"]["saturation"], 12, 25, "look sat"), ("contrast", B["grade"]["contrast"], A["grade"]["contrast"], 12, 25, "look con"), ("brightness", B["grade"]["brightness"], A["grade"]["brightness"], 10, 20, "look bri"),
            ("warmth", B["grade"]["warmth"], A["grade"]["warmth"], 60, 120, "look tint"), ("vignette", B["grade"]["vignette"], A["grade"]["vignette"], 40, 80, "look.vignette"), ("edge density", B["line"]["edge_density"], A["line"]["edge_density"], 25, 50, "line detail")]
    print(f"{'measure':24s} {'reference':>10s} {'candidate':>10s}  verdict   change this"); pts = 0
    for n, r, c, ok, close, knob in rows:
        rel = abs(c - r) / (abs(r) + 1e-6) * 100 if r else (0 if c == 0 else 100); v = "OK" if rel <= ok else "CLOSE" if rel <= close else "OFF"; pts += {"OK": 1, "CLOSE": .5, "OFF": 0}[v]
        print(f"{n:24s} {r:10.3f} {c:10.3f}  {v:7s}   {knob if v == 'OFF' else ''}")
    print(f"\ncloseness {100 * pts / len(rows):.0f}/100 (heuristic from {len(rows)} measurements, not watching). Change ONE thing per round, max 5 rounds.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("video", nargs="?"); ap.add_argument("--name"); ap.add_argument("--out"); ap.add_argument("--kind", choices=["edit", "animation"])
    ap.add_argument("--compare", nargs=2, metavar=("CANDIDATE", "REFERENCE")); a = ap.parse_args()
    if a.compare: return compare(*a.compare)
    if not a.video: ap.error("give a video or --compare")
    name = "".join(c if c.isalnum() or c in "-_" else "-" for c in (a.name or os.path.splitext(os.path.basename(a.video))[0])).strip("-").lower(); out = a.out or os.path.join("styles", name); os.makedirs(out, exist_ok=True)
    dna, (fr, t, cuts) = study(a.video, a.kind); dna["name"] = name; json.dump(dna, open(os.path.join(out, "dna.json"), "w"), indent=1)
    json.dump(preset_from(dna, name), open(os.path.join(out, "preset.json"), "w"), indent=1); contact(a.video, fr, t, cuts, os.path.join(out, "contact.jpg"))
    open(os.path.join(out, "brief.md"), "w").write(brief_md(dna, name)); print(open(os.path.join(out, "brief.md")).read()); print(f"[wrote {out}/dna.json, brief.md, preset.json, contact.jpg]")


if __name__ == "__main__":
    main()

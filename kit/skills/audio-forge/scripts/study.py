#!/usr/bin/env python3
"""study.py - measure the STYLE of a reference track and write a Style DNA + a plain-text brief any model can follow (even one that cannot hear).

  af.py study ref.mp3 --name roblox-guitar-cover [--out styles/roblox-guitar-cover] [--bpm-range 150 190]

Writes  <out>/dna.json (style-copy/audio-dna@1), <out>/brief.md (what to build, with numbers), <out>/spectrogram.png (if Pillow exists),
        <out>/genre.json (a draft audio-forge custom genre: copy it to ~/.config/audio-forge/genres/ to use it with `af.py compose --genre NAME`).

WHAT IS AND IS NOT COPIED: only measurements of the production style (tempo, key/mode, rhythmic density, brightness, distortion, stereo width,
loudness, arrangement shape, instrument-type hints). The notes, melody, riffs, lyrics and audio of the reference are NOT stored or reproduced.
The chord line is reduced to mode + vocabulary + how often chords change; the example loop is flavour only: write a NEW progression.
Heuristic guesses (instrument family, drums present) are labelled as guesses: confirm with the person if it matters.
"""
import argparse, json, os, subprocess, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A

SR = 44100
NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ROMAN = {0: "I", 1: "bII", 2: "II", 3: "bIII", 4: "III", 5: "IV", 6: "#IV", 7: "V", 8: "bVI", 9: "VI", 10: "bVII", 11: "VII"}


def load_wav(path):
    if not path.lower().endswith(".wav"):
        tmp = tempfile.mktemp(suffix=".wav")
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", path, "-ar", str(SR), "-ac", "2", tmp], capture_output=True)
        if r.returncode: raise SystemExit("study: could not decode the file (ffmpeg needed for mp3/m4a): " + r.stderr.decode()[-200:])
        path = tmp
    import wave
    with wave.open(path) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes(); raw = w.readframes(n)
        x = np.frombuffer(raw, "<i2").astype(np.float32).reshape(-1, ch) / 32768.0 if w.getsampwidth() == 2 else None
    if x is None: raise SystemExit("study: only 16-bit PCM is read directly; give an mp3/wav")
    return path, sr, (x if ch == 2 else np.repeat(x, 2, axis=1))


def stft_mag(m, sr, n=4096, hop=1024):
    from scipy.signal import stft
    f, t, Z = stft(m, sr, nperseg=n, noverlap=n - hop, boundary=None, padded=False)
    return f, t, np.abs(Z)


def onset_steps(m, sr, downbeat0, bar_s):
    """onset times by spectral flux -> positions on a 16-step bar grid (aggregate rhythmic density: a style fingerprint, not a riff)"""
    f, t, S = stft_mag(m, sr, 2048, 512)
    S = np.log1p(30 * S); flux = np.maximum(S[:, 1:] - S[:, :-1], 0).sum(0); flux = flux / (flux.max() + 1e-9)
    thr = np.median(flux) + 0.9 * flux.std(); peaks = [i for i in range(2, len(flux) - 2) if flux[i] > thr and flux[i] == flux[i - 2:i + 3].max()]
    times = t[1:][peaks]
    step = bar_s / 16.0; hist = np.zeros(16); good = 0
    for ts in times:
        k = (ts - downbeat0) / step; r = k - round(k)
        if abs(r) <= 0.3: hist[int(round(k)) % 16] += 1; good += 1
    return times, (hist / (hist.max() + 1e-9)).round(2).tolist(), good / max(len(times), 1)


def band_rhythm(m, sr, downbeat0, bar_s):
    """separate the LOW (kick/bass) and MID (snare/vocal/guitar) attack grids: they usually tell different stories.
    Returns each band's 16-step density (style fingerprint, not a riff) and attacks per beat."""
    from scipy.signal import stft, find_peaks
    f, t, Z = stft(m, sr, nperseg=2048, noverlap=2048 - 512, boundary=None, padded=False)
    L = np.log1p(np.abs(Z) * 40)
    d = np.maximum(np.diff(L, axis=1, prepend=L[:, :1]), 0)
    out = {}
    for name, (lo, hi) in dict(low=(30, 150), mid=(150, 2500)).items():
        env = d[(f >= lo) & (f < hi)].sum(0)
        env = env - np.median(env)
        pk, _ = find_peaks(np.maximum(env, 0), height=np.percentile(env, 90), distance=int(0.08 * sr / 512))
        times = t[np.clip(pk, 0, len(t) - 1)]
        hist = np.zeros(16); good = 0
        for ts in times:
            k = (ts - downbeat0) / (bar_s / 16.0); r = k - round(k)
            if abs(r) <= 0.3: hist[int(round(k)) % 16] += 1; good += 1
        out[name + "_step16_density"] = (hist / (hist.max() + 1e-9)).round(2).tolist()
        out[name + "_onsets_per_beat"] = round(len(times) / max(len(m) / sr, 1e-9) * (bar_s / 4.0), 2)
    out["note"] = "low band ~ kick/bass, mid band ~ snare/vocal/guitar; separate attack grids, measured from the full mix"
    return out


def sustain_ms(m, sr, onset_times):
    """median time for the level to fall 12 dB after an onset: short = muted/plucked/staccato, long = ringing/sustained"""
    hop = int(0.005 * sr); e = np.sqrt(np.convolve(m ** 2, np.ones(hop) / hop, mode="same"))[::hop] + 1e-9; out = []
    for i, ts in enumerate(onset_times[:-1]):
        a = int(ts / 0.005); b = int(min(onset_times[i + 1], ts + 0.6) / 0.005)
        if b - a < 6: continue
        seg = e[a:b]; pk = seg[:6].max(); below = np.where(seg < pk * 0.25)[0]
        out.append((below[0] if len(below) else len(seg)) * 5.0)
    return float(np.median(out)) if out else None


def chord_stats(m, sr, downbeats, bar_s, key_pc, mode):
    f, t, S = stft_mag(m, sr, 8192, 4096)
    band = (f > 70) & (f < 2000); fb = f[band]; chroma_t = np.zeros((12, S.shape[1]))
    for k, fr in enumerate(fb):
        pc = int(round(12 * np.log2(fr / 440.0) + 69)) % 12; chroma_t[pc] += S[band][k]
    third, power, rows, roots = 0, 0, [], []
    for d in downbeats[:-1]:
        sel = (t >= d) & (t < d + bar_s)
        if not sel.any(): continue
        c = chroma_t[:, sel].mean(1); root = int(np.argmax(c))
        r = c[root] + 1e-9; has3 = max(c[(root + 3) % 12], c[(root + 4) % 12]) / r; has5 = c[(root + 7) % 12] / r
        roots.append(root); rows.append((has3, has5))
        if has5 > 0.45 and has3 < 0.35: power += 1
        if has3 >= 0.5: third += 1
    n = max(len(roots), 1); changes = sum(1 for a, b in zip(roots, roots[1:]) if a != b)
    deg = [(r - key_pc) % 12 for r in roots]
    from collections import Counter
    top = [d for d, _ in Counter(deg).most_common(4)]
    loop = [ROMAN[d] for d in (deg[:4] if len(deg) >= 4 else deg)]
    return dict(power_chord_share=round(power / n, 2), third_share=round(third / n, 2), chord_changes_per_bar=round(changes / n, 2),
                common_degrees=[ROMAN[d] for d in top], example_loop_FLAVOUR_ONLY=loop)


def bar_energy_curve(m, sr, downbeats, bar_s):
    out = []
    for d in downbeats[:-1]:
        seg = m[int(d * sr):int((d + bar_s) * sr)]
        out.append(float(20 * np.log10(np.sqrt(np.mean(seg ** 2) + 1e-12))) if len(seg) else -90.0)
    a = np.array(out); a = np.maximum(a - a.max(), -40.0)           # a fade-out/silent last bar must not dominate the curve
    return a.round(1).tolist()


def band_corr(L, R, sr):
    from scipy.signal import butter, sosfilt
    res = {}
    for name, (lo, hi) in dict(low=(30, 150), mid=(150, 3000), high=(3000, 12000)).items():
        sos = butter(4, [lo / (sr / 2), hi / (sr / 2)], "band", output="sos"); a, b = sosfilt(sos, L), sosfilt(sos, R)
        res[name] = round(float(np.corrcoef(a, b)[0, 1]), 2)
    return res


def study(path, bpm_range=None, with_deep=True):
    wav, sr, x = load_wav(path); m = x.mean(1); L, R = x[:, 0], x[:, 1]
    prof = A.analyze(wav, quiet=True, bpm_range=bpm_range) if True else None
    bpm = prof["tempo"]["bpm"]; downs = prof.get("downbeats") or []; bar_s = 240.0 / bpm
    if len(downs) < 3: downs = [prof["tempo"].get("first_beat", 0.0) + i * bar_s for i in range(int(len(m) / sr / bar_s))]
    times, fp, fp_conf = onset_steps(m, sr, downs[0], bar_s)
    sus = sustain_ms(m, sr, times)
    key = prof["key"]["best"]; key_pc = NOTE.index(key["key"]); ch = chord_stats(m, sr, downs, bar_s, key_pc, key["mode"])
    curve = bar_energy_curve(m, sr, downs, bar_s); dur = len(m) / sr
    S_f, S_t, S = stft_mag(m, sr, 4096, 1024); hf = float(10 * np.log10((S[(S_f > 3000) & (S_f < 8000)] ** 2).sum() / ((S[(S_f > 200) & (S_f < 3000)] ** 2).sum() + 1e-12) + 1e-12))
    onps = len(times) / dur; per_beat = onps / (bpm / 60.0)
    br = band_rhythm(m, sr, downs[0], bar_s)
    try:
        import hear as _H
        arch = []
        for sc in (prof.get("sections") or [])[:8]:
            a_f = int(sc["start"] / (1024.0 / sr)); b_f = int(sc["end"] / (1024.0 / sr))
            arch.append(dict(label=sc["label"], start=sc["start"], guesses=_H._archetypes(S, S_f, S_t, a_f, b_f, m[int(sc["start"] * sr):int(sc["end"] * sr)], sr, hop=1024)))
        tot = {}
        for q in arch:
            for g in q["guesses"][:2]: tot[g["guess"]] = tot.get(g["guess"], 0.0) + g["score"]
        dominant = [k for k, _ in sorted(tot.items(), key=lambda kv: -kv[1])[:3]]
    except Exception:
        arch, dominant = [], []
    secs = [dict(label=s["label"], bars=s["bars"], start=s["start"], end=s["end"], energy=s["energy"]) for s in prof.get("sections", [])]
    flat = prof["spectral"]["flatness"]; harm = prof.get("harmonic_ratio")
    guess = []
    guess.append(f"distortion: {'high' if flat > 0.5 or hf > -6 else 'moderate' if flat > 0.3 else 'low (clean)'} (flatness {flat}, 3-8k vs 0.2-3k {hf:.1f} dB)")
    guess.append(f"articulation: {'muted / staccato' if (sus or 999) < 140 else 'mixed' if (sus or 999) < 260 else 'sustained / ringing'} (median 12 dB fall {sus} ms)")
    guess.append(f"chords: {'mostly power chords (no third)' if ch['power_chord_share'] > 0.5 else 'full chords with thirds' if ch['third_share'] > 0.5 else 'mixed'}")
    guess.append(f"drums: {'probably yes' if prof['pattern']['kick'].count('X') + prof['pattern']['snare'].count('X') >= 2 else 'unclear'} (kick {prof['pattern']['kick']}, snare {prof['pattern']['snare']}; from a full mix, approximate)")
    dna = dict(schema="style-copy/audio-dna@1", name=os.path.splitext(os.path.basename(path))[0], kind="audio", seconds=round(dur, 1),
               tempo=dict(bpm=bpm, alt_octaves=prof["tempo"].get("alt_octaves"), steady=prof["tempo"]["steady"], ambiguous=prof["tempo"].get("ambiguous"), beats_per_bar=prof["meter"]["beats_per_bar"], swing=prof["swing"]),
               key=dict(tonic=key["key"], mode=key["mode"], relative=prof["key"].get("relative")),
               harmony=dict(ch, note="reduced on purpose: mode + vocabulary + change rate. Write a new progression."),
               rhythm=dict(onsets_per_sec=round(onps, 2), onsets_per_beat=round(per_beat, 2), step16_density=fp, grid_confidence=round(fp_conf, 2),
                           kick=prof["pattern"]["kick"], snare=prof["pattern"]["snare"], hat=prof["pattern"]["hat"], sustain_ms=sus, **br),
               timbre=dict(centroid_hz=prof["spectral"]["centroid_hz"], rolloff85_hz=prof["spectral"]["rolloff85_hz"], flatness=flat, hf_ratio_db=round(hf, 1),
                           harmonic_ratio=harm, bands_db=prof["bands_db"]),
               mix=dict(lufs=prof["loudness"]["lufs"], lra=prof["loudness"]["lra"], true_peak_db=prof["loudness"]["true_peak_db"], crest_db=prof["dynamics"]["crest_db"],
                        rms_db=prof["dynamics"]["rms_db"], side_to_mid_db=prof["stereo"]["side_to_mid_db"], lr_correlation=prof["stereo"]["lr_correlation"], band_correlation=band_corr(L, R, sr)),
               structure=dict(sections=secs, drops=prof.get("drops"), energy_per_bar_db=curve),
               instruments=dict(dominant_archetypes=dominant, per_section=arch, method="odd/even harmonic ratio, autocorrelation harmonicity, decay slope, attack rate, band balance (heuristics)",
                               note="These are guesses from a full mix; confirm with the person. They only pick starting instruments, they never transcribe the reference."),
               guesses=guess, analyzer_summary=prof.get("summary"), analyzer_genre_guess=[g.get("genre") for g in prof.get("genre_guess", []) if g.get("genre")][:3])
    if with_deep:
        import deep as D
        dd = D.deep(path, prof=prof, decoded=(wav, sr, x)); dna["schema"] = "style-copy/audio-dna@2"; dna["deep"] = deep_summary(dd); dna["_deep_full"] = dd
    return dna, (S_f, S_t, S)


def deep_summary(d):
    """the compact, style-only part of deep.json that lives inside dna.json (positions and measurements, no notes or words)"""
    hp = d["hard_points"]
    return dict(tempo_feel=d["tempo_feel"],
                hard_points=dict(drops=[{k: q[k] for k in ("bar", "t", "pct", "jump_db", "bass_jump_db", "has_cut", "has_riser", "impact", "anatomy")} for q in hp["drops"]],
                                 hits_per_min=hp["hits_per_min"], stops_per_min=hp["stops_per_min"], hit_types=hp["hit_types"], hits_on_16th_grid_share=hp["hits_on_16th_grid_share"], hits_on_beat1_share=hp["hits_on_beat1_share"],
                                 risers=[{k: q[k] for k in ("t", "dur_s", "rise_db", "pct")} for q in hp["risers"]], stops=[{k: q[k] for k in ("t", "dur_s", "pct", "then")} for q in hp["stops"]], starts_hot=hp["starts_hot"],
                                 breakdowns=[{k: q[k] for k in ("t", "bars", "depth_db", "bass_drop_db", "pct", "leads_into_drop")} for q in hp.get("breakdowns", [])],
                                 builds=[{k: q[k] for k in ("t", "bars", "onset_density_rise", "level_slope_db_per_bar", "pct")} for q in hp.get("builds", [])],
                                 tone_shifts=[{k: q[k] for k in ("t", "bar", "centroid_shift_hz", "brightness_shift_db", "level_change_db", "pct", "detail")} for q in hp.get("tone_shifts", [])],
                                 fill_dips=[{k: q[k] for k in ("t", "bar", "bars", "depth_db", "recovery_db", "onset_peak", "pct", "detail")} for q in hp.get("fill_dips", [])],
                                 snare_rolls=[{k: q[k] for k in ("t", "bar", "beats", "onsets", "density_per_s", "pct", "detail")} for q in hp.get("snare_rolls", [])],
                                 chroma_changes=[{k: q[k] for k in ("t", "bar", "chroma_distance", "pre_root", "post_root", "pct", "detail")} for q in hp.get("chroma_changes", [])],
                                 tail=({k: hp["tail"][k] for k in ("t_cut", "tail_s", "kind", "pct", "fall_db_in_1s")} if hp.get("tail") else None)),
                form=dict(sequence=d["form"], sections=[{k: q[k] for k in ("label", "form", "start_bar", "bars", "pct", "energy_rel_db", "onsets_per_beat")} for q in d["sections"]], chord_cycle_bars=d["phrase"]["chord_loop_bars"]),
                layer_moves=d["layer_moves"], loop=dict(loop_ready=d["loop"]["loop_ready"], issues=d["loop"]["issues"], fade_out_s=d["loop"]["fade_out_s"], lead_in_s=d["loop"]["lead_in_s"]),
                lead_layer=dict(share_of_bars=d["lead_layer"]["share_of_bars"], segments=[{k: q[k] for k in ("bar", "end_bar")} for q in d["lead_layer"]["segments"]]), role_guess=d["role_guess"],
                grid=dict(downbeat_phase_confidence=d["grid"]["downbeat_phase_confidence"], steady=d["grid"]["steady"]))


def plan_from_energy(curve):
    """arrangement shape from the loudness of each bar (more reliable than the analyzer's section labels):
    quiet bars at the start = intro, rising bars before the loud part = build, loud = drop, quieter after the loud part = break (outro if last)"""
    if not curve: return [["drop", 1.0]]
    cls = ["q" if v < -12 else "m" if v < -4.5 else "f" for v in curve]
    runs = []
    for c in cls:
        if runs and runs[-1][0] == c: runs[-1][1] += 1
        else: runs.append([c, 1])
    changed = True
    while changed and len(runs) > 1:                                  # absorb flickers: runs shorter than 3 bars join their neighbour
        changed = False
        for i, (c, n) in enumerate(runs):
            if n < 3 and len(runs) > 1 and not (i == 0 and n >= 2):
                j = i - 1 if i > 0 else i + 1; runs[j][1] += n; del runs[i]; changed = True; break
        merged = [runs[0]]
        for r in runs[1:]:
            if r[0] == merged[-1][0]: merged[-1][1] += r[1]
            else: merged.append(r)
        runs = merged
    first_full = next((i for i, r in enumerate(runs) if r[0] == "f"), None); out = []
    for i, (c, n) in enumerate(runs):
        if c == "f": nm = "drop"
        elif first_full is None: nm = "verse"
        elif i < first_full: nm = "intro" if i == 0 else "build"
        else: nm = "outro" if i == len(runs) - 1 else "break_"
        if out and out[-1][0] == nm: out[-1][1] += n
        else: out.append([nm, n])
    tot = sum(n for _, n in out)
    return [[nm, round(n / tot, 3)] for nm, n in out]


def draft_genre(dna, name):
    """Turn the measurements into a DRAFT audio-forge genre. V2: the instrument archetypes and the
    separate low/mid attack grids choose the base genre and the actual V2 voices, instead of always
    drafting a guitar/metal spec."""
    d = dna; r = d["rhythm"]; fp = r["step16_density"]; tb = d["timbre"]
    dist = tb["flatness"] > 0.5 or tb["hf_ratio_db"] > -6
    bpm = d["tempo"]["bpm"]
    arch = [a.split(" (")[0] for a in (d.get("instruments", {}) or {}).get("dominant_archetypes", [])]
    low_fp = r.get("low_step16_density") or fp
    mid_fp = r.get("mid_step16_density") or fp
    def pat_of(v, max_notes=8):
        v = list(v); order = np.argsort(v)[::-1]; keep = set(order[:max_notes].tolist())
        thr = float(np.percentile(v, 55))
        return "".join("X" if (i in keep and v[i] >= 0.8) else "x" if (i in keep and v[i] >= thr) else "o" if (i in keep and v[i] >= 0.2) else "." for i in range(len(v)))
    low_pat = pat_of(low_fp)
    mid_pat = pat_of(mid_fp)
    if (r["sustain_ms"] or 999) < 140:            # short notes -> muted guitar hits ('m' in the rhythm string)
        mid_pat = mid_pat.replace("x", "m").replace("X", "x")
    # base genre from the strongest measured archetype, then tempo
    if "guitar" in arch: base = "metal" if dist and bpm >= 140 else "rock"
    elif "breakbeat" in arch: base = "dnb" if bpm >= 145 else "boombap"
    elif "303" in arch: base = "techno" if bpm >= 120 else "house"
    elif "chip" in arch: base = "chiptune"
    elif "bell" in arch: base = "cinematic" if bpm < 110 else "horror_chase"
    elif "piano" in arch: base = "warm_piano"
    else: base = "metal" if dist and bpm >= 140 else "rock"
    # lead/chord/bass voices from the archetypes (all shipped V2 instruments)
    lead_inst = ("bell_tubular" if "bell" in arch else "chip_lead" if "chip" in arch else "piano" if "piano" in arch
                 else "guitar_elec" if "guitar" in arch else "pluck")
    chord_inst = ("bell_tubular" if "bell" in arch else "organ_pipe" if "piano" in arch and bpm < 100 else
                  "piano_m1" if "piano" in arch else "guitar_elec" if "guitar" in arch else "pad")
    bass_inst = ("acid_303" if "303" in arch else "y2k_bass" if "breakbeat" in arch else
                 "saw_bass" if "guitar" in arch else "sine_sub")
    ov = dict(bpm=[int(bpm - 4), int(bpm + 4)], scales=["minor" if d["key"]["mode"] == "minor" else "major"], swing=d["tempo"]["swing"],
              guitar=dict(inst="guitar_elec" if dist else "guitar_pluck", rhythm=mid_pat, kind="power" if d["harmony"]["power_chord_share"] > 0.5 else "triad",
                          kw=dict(drive=10.0 if dist else 1.0)),
              chords=dict(inst=chord_inst, oct=3, rhythm="x-------x-------", kind="triad" if d["harmony"]["power_chord_share"] > 0.5 else "seventh"),
              bass=dict(inst=bass_inst, oct=1 if "303" in arch else 2, rhythm=low_pat if low_pat.count("x") >= 2 else "x-------x-------"),
              lead=dict(inst=lead_inst, oct=5, density=round(min(0.8, max(0.2, r["onsets_per_beat"] / 3.0)), 2), contour="arch", leap=0.25),
              plan=plan_from_energy(d["structure"]["energy_per_bar_db"]), lufs=d["mix"]["lufs"],
              chord_len=1 if d["harmony"]["chord_changes_per_bar"] >= 0.5 else 2)
    if "breakbeat" in arch and bpm >= 140: ov["breakbeat"] = "dnb"
    if "guitar" in arch: ov["mix"] = {"guitar": {"gain_db": -8}, "bass": {"gain_db": -2}}
    return dict(name=name, base=base, override=ov, instruments_used=dict(lead=lead_inst, chords=chord_inst, bass=bass_inst),
                detected_archetypes=arch, note="DRAFT from measurements (archetypes are heuristics): tune with `af.py compare` until the numbers match, then ship it.")


def spectrogram_png(S_f, S_t, S, out):
    try:
        from PIL import Image
    except Exception:
        return False
    sel = S_f < 10000; M = 20 * np.log10(S[sel] + 1e-6); lo, hi = np.percentile(M, 8), np.percentile(M, 99.7); M = np.clip((M - lo) / (hi - lo + 1e-9), 0, 1)[::-1]
    w = min(1400, M.shape[1]); idx = np.linspace(0, M.shape[1] - 1, w).astype(int); M = M[:, idx]
    h = 420; idy = np.linspace(0, M.shape[0] - 1, h).astype(int); M = M[idy]
    rgb = np.stack([np.clip(M * 3 - 1.2, 0, 1), np.clip(M * 2.4 - 0.7, 0, 1) ** 1.5, np.clip(1.2 - np.abs(M - 0.35) * 3, 0, 1)], -1)
    Image.fromarray((rgb * 255).astype("uint8")).save(out); return True


def deep_brief(d):
    dp = d.get("deep")
    if not dp: return []
    hp, fm, tf = dp["hard_points"], dp["form"], dp["tempo_feel"]
    L = ["", "## 5b. Hard points and transitions (positions as % of the track, so they scale to any length)",
         f"Tempo feel: analyzer says {tf['analyzer_bpm']}, it behaves like **{tf['feel_bpm']} BPM** ({tf['confidence']} confidence; ask which they tap). Role guess (heuristic): {dp['role_guess']['role']}.",
         f"Form: **{fm['sequence']}** = " + ", ".join(f"{q['label']} {q['bars']} bars ({q['pct']}%)" for q in fm["sections"]) + f". Chord cycle: {fm['chord_cycle_bars'] or 'none found'} bars."]
    for q in hp["drops"]: L.append(f"- DROP at {q['pct']}% (bar {q['bar']}): {q['anatomy']}")
    L.append(f"- Hard hits {hp['hits_per_min']}/min (types {hp['hit_types']}), stops {hp['stops_per_min']}/min, hits on the 16th grid {hp['hits_on_16th_grid_share']}, on beat 1 {hp['hits_on_beat1_share']}." + (" Starts at full energy." if hp["starts_hot"] else ""))
    for q in hp["risers"]: L.append(f"- Riser at {q['pct']}% for {q['dur_s']} s (+{q['rise_db']} dB in the high bands)")
    for q in hp["stops"]: L.append(f"- Hard stop at {q['pct']}% for {q['dur_s']} s" + (f", then {q['then']}" if q["then"] else ""))
    if dp["layer_moves"]: L += ["Layers at section boundaries (what to add or take away there):"] + [f"- bar {m['bar']} ({m['section']}): {', '.join(m['moves']) or 'no big change'}" for m in dp["layer_moves"]]
    L.append(f"Loop-readiness of the reference file: {'ready' if dp['loop']['loop_ready'] else 'NOT ready (' + '; '.join(dp['loop']['issues'][:2]) + ')'}. YOUR file for a looping Roblox Sound must pass `af.py deep` loop check.")
    L.append("Rule: reproduce the ANATOMY (cut, riser, impact, bass entry) and the proportions at the same % positions, not the notes.")
    return L


def brief_md(d, name):
    t, k, h, r, tb, mx, st = d["tempo"], d["key"], d["harmony"], d["rhythm"], d["timbre"], d["mix"], d["structure"]
    bd = tb["bands_db"]; sec = ", ".join(f"{s['label']} {s['bars']} bars (energy {s['energy']})" for s in st["sections"])
    L = [f"# Style brief: {name}", "", f"Made by `af.py study` from measurements only (`dna.json`). Nobody has listened: where this says *guess*, confirm with the person. The reference's notes, melody and audio are not stored.", "",
         "## 1. Numbers to hit (check them with `af.py compare`)", "| what | target |", "|---|---|",
         f"| tempo | **{t['bpm']} BPM**" + (f" (could also feel like {', '.join(str(x) for x in (t['alt_octaves'] or []))}: ask which feels right)" if t.get("ambiguous") else "") + f", {t['beats_per_bar']}/4, swing {t['swing']} |",
         f"| key / mode | **{k['tonic']} {k['mode']}** (relative {k['relative']}) |",
         f"| loudness | {mx['lufs']} LUFS integrated, loudness range {mx['lra']} LU, true peak {mx['true_peak_db']} dB, crest {mx['crest_db']} dB |",
         f"| brightness | spectral centroid {tb['centroid_hz']} Hz, 85% rolloff {tb['rolloff85_hz']} Hz, flatness {tb['flatness']}, 3-8 kHz vs 0.2-3 kHz {tb['hf_ratio_db']} dB |",
         f"| balance (dB re full scale) | sub {bd['sub']}, bass {bd['bass']}, low-mid {bd['low_mid']}, mid {bd['mid']}, high-mid {bd['high_mid']}, air {bd['air']} |",
         f"| stereo | side/mid {mx['side_to_mid_db']} dB, L/R correlation {mx['lr_correlation']}; by band {mx['band_correlation']} |",
         f"| rhythmic density | {r['onsets_per_sec']} attacks/s = {r['onsets_per_beat']} per beat; sustain (12 dB fall) {r['sustain_ms']} ms |", "",
         "## 2. Arrangement shape", f"Sections: {sec}. Drops at {st['drops']} s. Energy per bar (dB below the loudest bar): `{st['energy_per_bar_db']}`.",
         "Rule: build the SAME shape (same proportions and the same quiet-to-loud ramp), not the same bars.", "",
         "## 3. Rhythm fingerprint (16 steps per bar, 1.0 = most attacks; style density, not a riff)", f"`{r['step16_density']}`  (grid confidence {r['grid_confidence']})", f"Drum hints (full mix, approximate): kick `{r['kick']}`, snare `{r['snare']}`, hat `{r['hat']}`.", "",
         "## 4. Harmony (reduced on purpose)", f"Power-chord share {h['power_chord_share']}, third share {h['third_share']}, chord changes per bar {h['chord_changes_per_bar']}, most-used degrees {h['common_degrees']}. Example loop (FLAVOUR ONLY, do not copy): {h['example_loop_FLAVOUR_ONLY']}. Write a NEW progression in the same mode.", "",
         "## 5. Guesses about the sound (confirm if it matters)"] + [f"- {g}" for g in d["guesses"]] + [
         ] + deep_brief(d) + [
         "", "## 6. How to build it with audio-forge", "1. Copy `genre.json` to `~/.config/audio-forge/genres/` (or use the shipped genre if one exists). It is a DRAFT: base genre + overrides from the numbers above.",
         f"2. `af.py compose --genre {name.replace(chr(45), chr(95))} --bars 48 --out cand.wav` (add `--bpm`, `--key`, `--seed 2` for other takes).", f"3. `af.py compare cand.wav {name}/dna.json` and change ONE knob per round (the compare output names the knob), at most 5 rounds.",
         "4. Report the final numbers table and the items still off. Say you have not listened; the person judges the sound.", "",
         "## 7. Do not", "- Do not reproduce the reference's melody, riff, lyrics or any audio. This is a style, not a transcription.", "- Do not claim it 'sounds the same'. Say which measured numbers match."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio"); ap.add_argument("--name"); ap.add_argument("--out"); ap.add_argument("--bpm-range", nargs=2, type=float); ap.add_argument("--no-deep", action="store_true")
    a = ap.parse_args(); name = a.name or os.path.splitext(os.path.basename(a.audio))[0]; name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name).strip("-").lower()
    out = a.out or os.path.join("styles", name); os.makedirs(out, exist_ok=True)
    dna, spec = study(a.audio, tuple(a.bpm_range) if a.bpm_range else None, with_deep=not a.no_deep); dna["name"] = name
    full = dna.pop("_deep_full", None)
    if full:
        import deep as D
        full["file"] = name; json.dump(full, open(os.path.join(out, "deep.json"), "w"), indent=1); open(os.path.join(out, "timeline.md"), "w").write(D.timeline_md(full, name))
        D.write_labels(full, os.path.join(out, "labels.txt")); D.write_csv(full, os.path.join(out, "hardpoints.csv")); D.timeline_png(full, os.path.join(out, "timeline.png"))
    json.dump(dna, open(os.path.join(out, "dna.json"), "w"), indent=1)
    gj = draft_genre(dna, name.replace("-", "_")); json.dump(gj, open(os.path.join(out, "genre.json"), "w"), indent=1)
    open(os.path.join(out, "brief.md"), "w").write(brief_md(dna, name)); png = spectrogram_png(*spec, os.path.join(out, "spectrogram.png"))
    print(open(os.path.join(out, "brief.md")).read()); print(f"[wrote {out}/dna.json, brief.md, genre.json" + (", spectrogram.png" if png else "") + (", deep.json, timeline.md, labels.txt, hardpoints.csv, timeline.png" if full else "") + "]")


if __name__ == "__main__":
    main()

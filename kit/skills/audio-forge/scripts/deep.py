#!/usr/bin/env python3
"""deep.py - the deep analyzer: HARD POINTS, structure, layers, loop-readiness, tempo feel and mid-range lead layer, bar by bar.

  af.py deep track.mp3 [--out DIR] [--name N] [--bpm-range LO HI] [--no-png] [--json]

Writes into DIR (default ./deep/<name>/):
  deep.json     (audio-forge/deep@1)  everything below, machine readable
  timeline.md   the whole track as text: hard points, sections, bar map (for a model that cannot hear)
  labels.txt    Audacity label track (File > Import > Labels) - also readable by most DAWs as markers
  hardpoints.csv
  timeline.png  energy / bands / markers picture (if Pillow exists)

WHAT IT FINDS (all from measurements; nobody listens):
  hits        impacts and accents: where the energy jumps inside ~120 ms; type (sub/kick, crash/high, full), strength, tail length, position in bar
  stops       hard stops / cuts: the music drops >= 14 dB for >= 80 ms and comes back (the 'silence before the drop' trick)
  risers      rising brightness/high-band ramps (>= 1 beat): sweeps, snare rolls, build-ups
  drops       the big entrances (bar-level energy jump) with their ANATOMY: cut before, riser before, impact on it, bass entry, brightness change
  breakdowns  runs of >=2 bars sitting >= 2 dB under surroundings; builds ramping into drops
  tone shifts spectral texture shifts (centroid jumps or band balance changes) with flat loudness (rev 3)
  fill dips   1-2 bar level dips with fast recovery and onset bursts before impacts (rev 3)
  harmonics   harmonic content shifts via mean-centered chroma distance under flat loudness (rev 3)
  sections    novelty segmentation on bars; labels intro/build/drop/break/outro are heuristics; form string (A B A' C) from similarity
  layers      which frequency layers enter or leave at each section boundary
  phrase/loop chord-loop length in bars; whether the FILE is loop-ready (fade/silence at the ends, level jump, bar-grid length)
  tempo       local tempo map (drift), and the 'feel' octave (e.g. 96 BPM that behaves like 193)
  lead layer  when a pitched mid-range layer (vocal, lead synth or guitar) is prominent, relative to the track itself. It cannot say which.
              For real vocals/lyrics use  af.py lyrics  (needs Whisper, asked first).
Only measurements and positions are stored: no notes, melodies or lyrics.
"""
import argparse, csv, json, math, os, sys
import numpy as np
from scipy import signal
from scipy.ndimage import median_filter, uniform_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A
import study as S

NFFT, HOP = 2048, 512
BANDS = dict(sub=(20, 60), bass=(60, 250), lowmid=(250, 500), mid=(500, 2000), highmid=(2000, 6000), air=(6000, 16000))
BAND_NAMES = list(BANDS)
MAX_S = 420.0          # Roblox audio limit is 7 minutes


def db(x):
    return 10 * np.log10(np.maximum(x, 1e-12))


def clean(o):
    """numpy scalars/arrays -> plain python so json.dump never fails"""
    if isinstance(o, dict): return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [clean(v) for v in o]
    if isinstance(o, np.generic): return o.item()
    if isinstance(o, np.ndarray): return clean(o.tolist())
    return o


def mmss(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


# ── frames ───────────────────────────────────────────────────────────────────
def frames(m, sr):
    f, t, Z = signal.stft(m, sr, nperseg=NFFT, noverlap=NFFT - HOP, boundary=None, padded=False)
    return f, t, np.abs(Z)


def band_energy(Sx, f):
    out = {}
    for k, (lo, hi) in BANDS.items():
        sel = (f >= lo) & (f < hi)
        out[k] = db((Sx[sel] ** 2).sum(0)) if sel.any() else np.full(Sx.shape[1], -120.0)
    return out


def flux_curves(Sx, f):
    L = np.log1p(Sx * 50.0)
    d = np.maximum(np.diff(L, axis=1, prepend=L[:, :1]), 0)
    return d.sum(0), d[f < 250].sum(0), d[f > 4000].sum(0)


# ── bar grid ─────────────────────────────────────────────────────────────────
class Grid:
    def __init__(self, prof, dur):
        self.bpm = float(prof["tempo"]["bpm"]); self.bpb = int(prof["meter"]["beats_per_bar"]); self.bar_s = 60.0 / self.bpm * self.bpb
        downs = np.array(prof.get("downbeats") or [], float)
        if len(downs) >= 3:
            d0 = float(np.median(downs[:64] - self.bar_s * np.arange(min(len(downs), 64)))) if prof["tempo"]["steady"] else float(downs[0])
        else:
            d0 = float(prof["tempo"].get("first_beat") or 0.0)
        self.d0 = d0; self.dur = dur
        pre = int(math.floor(d0 / self.bar_s + 1e-6)); post = int(math.ceil((dur - d0) / self.bar_s))
        self.idx = np.arange(-pre, post)                           # bar k starts at d0 + k*bar_s; bar number = k+1 (bar 1 = first detected downbeat)
        self.t = d0 + self.bar_s * self.idx
        keep = (self.t + self.bar_s * 0.5 < dur)                   # drop a trailing stub shorter than half a bar
        self.idx, self.t = self.idx[keep], self.t[keep]
        self.n = len(self.t); self.phase_conf = float(prof["meter"].get("confidence") or 0.0)

    def pos(self, t):
        k = (t - self.d0) / self.bar_s; kb = math.floor(k)
        return int(kb) + 1, round(1 + (k - kb) * self.bpb, 2)

    def bar_no(self, i):
        return int(self.idx[i]) + 1

    def at(self, bar_no):                                          # array index of a bar number
        j = np.where(self.idx + 1 == bar_no)[0]
        return int(j[0]) if len(j) else None

    def grid_off_ms(self, t):                                      # distance to the nearest 16th note, ms
        step = self.bar_s / 16.0; k = (t - self.d0) / step
        return round((k - round(k)) * step * 1000, 1)


# ── hits, stops, risers ──────────────────────────────────────────────────────
ONSET_LAG = (NFFT / 2) / 44100.0 * 0.95        # frame centres lag the true attack by about half a window; measured ~+25 ms on kicks before this fix


def detect_hits(t, tot, bands, flux, G, fps, min_jump=6.0, max_hits=None):
    """HARD hits only: a sudden jump of >= 6 dB inside ~120 ms on a strong onset. Ordinary kicks/snares are groove, not hard points (they are counted in rhythm)."""
    n = len(t); thr = np.percentile(flux, 98.5)
    pk, _ = signal.find_peaks(flux, height=max(thr, 1e-6), distance=max(1, int(0.12 * fps)))
    a, b = max(2, int(0.25 * fps)), max(2, int(0.12 * fps)); out = []
    lo_db = db(10 ** (bands["sub"] / 10) + 10 ** (bands["bass"] / 10)); hi_db = db(10 ** (bands["highmid"] / 10) + 10 ** (bands["air"] / 10))
    for i in pk:
        if i < a or i + b + 1 >= n: continue
        before = db(np.mean(10 ** (tot[i - a:i - 1] / 10))); after = db(np.mean(10 ** (tot[i:i + b] / 10))); jump = float(min(after - before, 60.0))   # 60 = 'from silence'
        if jump < 3.0: continue
        lj = float(db(np.mean(10 ** (lo_db[i:i + b] / 10))) - db(np.mean(10 ** (lo_db[i - a:i - 1] / 10))))
        hj = float(db(np.mean(10 ** (hi_db[i:i + b] / 10))) - db(np.mean(10 ** (hi_db[i - a:i - 1] / 10))))
        kind = "full impact" if lj >= 4 and hj >= 4 else "sub/kick impact" if lj >= 4 and lj >= hj + 2 else "crash/high burst" if hj >= 4 and lj < 3 else "accent"
        seg = tot[i:i + int(4 * fps)]; back = np.where(seg < before + 3.0)[0]; back = back[back > b] if len(back) else back
        tail = float(back[0] / fps) if len(back) else None                     # None = the level stays up for 4 s+ (an entrance, not a one-shot)
        ts = float(t[i]) - ONSET_LAG; bar, beat = G.pos(ts)
        out.append(dict(t=round(ts, 3), bar=bar, beat=beat, type=kind, jump_db=round(jump, 1), low_jump_db=round(lj, 1), high_jump_db=round(hj, 1),
                        tail_s=(round(tail, 2) if tail is not None else None), grid_off_ms=G.grid_off_ms(ts), pct=round(100 * ts / G.dur, 1)))
    keep = []                                                    # a hard hit must stand out from the local groove: >= 6 dB AND >= 4 dB above the typical jump within +-4 s (plain kicks do not)
    for h in out:
        near = [q["jump_db"] for q in out if abs(q["t"] - h["t"]) <= 4.0 and q is not h]; typical = float(np.median(near)) if len(near) >= 3 else 3.0
        if h["jump_db"] >= min_jump and h["jump_db"] >= typical + 4.0: keep.append(h)
    keep.sort(key=lambda h: -h["jump_db"]); cap = max_hits or max(8, int(G.n * 0.5))
    return sorted(keep[:cap], key=lambda h: h["t"])


def detect_stops(t, tot, hits, G, fps):
    sm = uniform_filter1d(tot, size=max(1, int(0.04 * fps)))
    ref = median_filter(sm, size=int(3 * fps) | 1, mode="nearest")
    mask = (sm < ref - 14.0); out = []; i = 0; n = len(t)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]: j += 1
            dur = (j - i + 1) / fps; t0, t1 = float(t[i]), float(t[j])
            pre = sm[max(0, i - int(0.5 * fps)):i]
            if dur >= 0.08 and t0 > 1.5 and t1 < G.dur - 1.5 and len(pre) and pre.mean() > ref[i] - 6:
                nxt = [h for h in hits if t1 - 0.05 <= h["t"] <= t1 + 0.6]
                bar, beat = G.pos(t0)
                out.append(dict(t=round(t0, 3), end=round(t1, 3), dur_s=round(dur, 2), bar=bar, beat=beat, depth_db=round(float(ref[i] - sm[i:j + 1].min()), 1),
                                then=(nxt[0]["type"] if nxt else None), pct=round(100 * t0 / G.dur, 1)))
            i = j + 1
        else:
            i += 1
    return out


def detect_risers(t, bands, tot, G, fps):
    """sweeps/risers = the HIGH band rises >= 8 dB in a straight ramp AND faster than the overall level (so a plain fade-in is not a riser)"""
    hf = uniform_filter1d(db(10 ** (bands["highmid"] / 10) + 10 ** (bands["air"] / 10)), size=max(1, int(0.25 * fps))); tt = uniform_filter1d(tot, size=max(1, int(0.25 * fps)))
    floor = tt.max() - 45.0; hf = np.maximum(hf, hf.max() - 60.0); tt = np.maximum(tt, tt.max() - 60.0); step = max(1, int(60.0 / G.bpm * fps)); out = []
    for wbeats in (4, 8, 16):
        w = int(wbeats * 60.0 / G.bpm * fps)
        for s0 in range(0, len(hf) - w, step):
            seg, tseg = hf[s0:s0 + w], tt[s0:s0 + w]
            if tseg[:max(2, w // 6)].min() < floor: continue                          # starts from near silence: a fade-in
            x = np.arange(w); r = float(np.corrcoef(x, seg)[0, 1]) if seg.std() > 1e-6 else 0.0
            k = max(2, w // 6); rise = float(seg[-k:].mean() - seg[:k].mean()); trise = float(tseg[-k:].mean() - tseg[:k].mean())
            if r >= 0.85 and rise >= 8.0 and rise - trise >= 4.0: out.append((s0, s0 + w, rise, r))
    merged = []
    for s0, e, rise, r in sorted(out):
        if merged and s0 <= merged[-1][1]: merged[-1] = (merged[-1][0], max(e, merged[-1][1]))
        else: merged.append((s0, e))
    res = []
    for s0, e in merged:
        e = min(e, len(hf) - 1); pk = s0 + int(np.argmax(hf[s0:e + 1])); base = float(hf[s0:pk + 1].min()); top = float(hf[pk]); total = top - base
        if total < 8.0: continue
        s1 = s0 + int(np.where(hf[s0:pk + 1] <= base + 0.2 * total)[0][-1])                  # the ramp starts where the level last sat near its floor
        if (pk - s1) / fps < 0.5: continue
        rise = float(hf[pk] - hf[s1]); trise = float(tt[pk] - tt[s1]); x = np.arange(pk - s1 + 1); r = float(np.corrcoef(x, hf[s1:pk + 1])[0, 1]) if pk - s1 > 2 else 0.0
        if rise < 8.0 or rise - trise < 4.0: continue
        t0, t1 = float(t[s1]), float(t[pk]); bar, beat = G.pos(t0)
        res.append(dict(t=round(t0, 3), end=round(t1, 3), dur_s=round(t1 - t0, 2), bar=bar, beat=beat, rise_db=round(rise, 1), linearity=round(r, 2), pct=round(100 * t0 / G.dur, 1)))
    return res


# ── breakdowns, build-ups, final cut (added in rev 2) ───────────────────────
def detect_tail(t, tot, rows, G, fps):
    """the ending: where the music last sits near its normal level (t_cut), and how it leaves (hard cut + decay, or slow fade). None when the file ends at full level."""
    sm = uniform_filter1d(tot, size=max(1, int(0.1 * fps))); ref = float(np.percentile(sm, 75)); loud = np.where(sm >= ref - 4.0)[0]
    if not len(loud): return None
    t_cut = float(t[loud[-1]]); tail_s = G.dur - t_cut
    if tail_s < 0.5: return None
    i0 = int(loud[-1]); i1 = min(len(sm) - 1, i0 + int(1.0 * fps)); fall = float(sm[i0] - sm[i1]); bar, beat = G.pos(t_cut)
    bi = int(np.searchsorted(G.t, t_cut, side="right") - 1); bi = max(0, min(bi, G.n - 1))
    return dict(t_cut=round(t_cut, 2), tail_s=round(tail_s, 2), bar=bar, beat=beat, bar_index=bi, fall_db_in_1s=round(fall, 1), pct=round(100 * t_cut / G.dur, 1),
                kind=("hard cut then decay" if fall >= 6.0 else "fade-out"))


def detect_dips(rows, G, tail, drops=(), min_bars=2, depth_db=2.0):
    """breakdowns = a run of >= 2 bars whose level sits >= 2 dB under the bars around it (a one-bar recovery inside the run does not end it).
    If the run ends at a drop, its last 2-4 bars are reported as a BUILD when the onset density or level ramps up (a snare roll / riser feel that is not a bright sweep).
    These are energy facts at bar level; a model that heard the track can say whether it is a breakdown, a filtered section or a quiet verse."""
    n = len(rows) if tail is None else min(len(rows), tail["bar_index"])
    if n < 8: return [], []
    en = np.array([r["total_db"] for r in rows[:n]]); opb = np.array([r["onsets_per_beat"] for r in rows[:n]]); lo = np.array([db(10 ** (r["sub"] / 10) + 10 ** (r["bass"] / 10)) for r in rows[:n]])
    ref = np.zeros(n)
    for i in range(n):                                              # local reference: upper-middle level of the 8 bars each side (loud neighbours, so a dip stands out)
        nb = np.r_[en[max(0, i - 8):i], en[i + 1:min(n, i + 9)]]; ref[i] = np.percentile(nb, 70) if len(nb) else en[i]
    low = en < ref - depth_db; runs = []; i = 0
    while i < n:
        if low[i]:
            j = i
            while j + 1 < n and (low[j + 1] or (j + 2 < n and low[j + 2] and not low[j + 1])): j += 1
            if j - i + 1 >= min_bars and i >= 3: runs.append((i, j))                  # a quiet start is an intro, not a breakdown
            i = j + 1
        else: i += 1
    dips, builds = [], []
    for a, b in runs:
        depth = float(np.mean(ref[a:b + 1] - en[a:b + 1])); bass = float(np.mean([np.percentile(lo[max(0, k - 8):k + 9], 70) - lo[k] for k in range(a, b + 1)]))
        dix = [G.at(q["bar"]) for q in drops]; nxt = [d_ for d_ in dix if d_ is not None and b < d_ <= b + 2]
        ends_at_drop = bool(nxt) or (b + 1 < len(rows) and b + 1 < n and en[b + 1] >= ref[b] - 1.0)
        bend = (nxt[0] - 1) if nxt else b                           # the build may run on to the bar just before the drop even if that bar had recovered in level
        bld = None
        if ends_at_drop and bend - a + 1 >= 4:
            for k in (4, 3, 2):
                a2 = bend - k + 1
                if a2 - a < 2: continue
                before = float(opb[a:a2].mean()); after = float(opb[a2:bend + 1].mean()); slope = float((en[bend] - en[a2]) / max(1, bend - a2))
                if after - before >= 0.3 or slope >= 0.4: bld = (a2, bend, after - before, slope); break
        a_dip, b_dip = (a, (bld[0] - 1) if bld else b)
        dips.append(dict(t=round(float(rows[a_dip]["t"]), 2), end=round(float(rows[b_dip]["t"] + G.bar_s), 2), bar=rows[a_dip]["bar"], end_bar=rows[b_dip]["bar"], bars=b_dip - a_dip + 1, a_index=a_dip, depth_db=round(depth, 1), bass_drop_db=round(bass, 1),
                         pct=round(100 * float(rows[a_dip]["t"]) / G.dur, 1), leads_into_drop=bool(ends_at_drop)))
        if bld:
            a2, b2, d_opb, slope = bld
            builds.append(dict(t=round(float(rows[a2]["t"]), 2), end=round(float(rows[b2]["t"] + G.bar_s), 2), bar=rows[a2]["bar"], end_bar=rows[b2]["bar"], bars=b2 - a2 + 1, a_index=a2, onset_density_rise=round(d_opb, 2), level_slope_db_per_bar=round(slope, 2),
                               pct=round(100 * float(rows[a2]["t"]) / G.dur, 1), note="bar-level ramp (onsets and/or level), not a bright sweep: check by ear whether it is a snare roll or riser"))
    return dips, builds


# ── tone shifts (spectral section changes with flat loudness, rev 3) ─────────
def detect_tone_shifts(rows, G, tail, min_hold=6, level_cap=3.0, cent_delta=400, band_delta=2.5):
    """Section changes where the SPECTRUM moves but loudness stays within level_cap dB.
    A shift = the centroid or a band-balance ratio jumps and holds for >= min_hold bars.
    These are real section boundaries that the energy-only slicer misses (lmsy2k 0:09, 0:29, 0:47).
    Returns a list of dicts with the bar where the shift happens, what moved and by how much."""
    n = len(rows) if tail is None else min(len(rows), tail.get("bar_index", len(rows)))
    if n < min_hold * 2:
        return []
    en = np.array([r["total_db"] for r in rows[:n]])
    cent = np.array([r["centroid_hz"] for r in rows[:n]], float)
    # band balance: bass-weight (sub+bass vs mid+highmid) and brightness (highmid+air vs sub+bass)
    lo = np.array([db(10 ** (r["sub"] / 10) + 10 ** (r["bass"] / 10)) for r in rows[:n]])
    hi = np.array([db(10 ** (r["highmid"] / 10) + 10 ** (r["air"] / 10)) for r in rows[:n]])
    bright = hi - lo  # higher = brighter

    shifts = []
    # scan every bar as a potential boundary: compare the min_hold bars before vs after
    for i in range(min_hold, n - min_hold):
        # level must be stable across the boundary
        pre_en = en[i - min_hold:i].mean()
        post_en = en[i:i + min_hold].mean()
        if abs(post_en - pre_en) > level_cap:
            continue
        # centroid shift
        pre_cent = cent[i - min_hold:i].mean()
        post_cent = cent[i:i + min_hold].mean()
        d_cent = post_cent - pre_cent
        # brightness shift
        pre_bright = bright[i - min_hold:i].mean()
        post_bright = bright[i:i + min_hold].mean()
        d_bright = post_bright - pre_bright
        # check: at least one metric jumps meaningfully
        cent_ok = abs(d_cent) >= cent_delta
        band_ok = abs(d_bright) >= band_delta
        if not (cent_ok or band_ok):
            continue
        # check the shift HOLDS: the post window's std should be < the shift magnitude (not just noise)
        if cent_ok and cent[i:i + min_hold].std() > abs(d_cent) * 0.7:
            cent_ok = False
        if band_ok and bright[i:i + min_hold].std() > abs(d_bright) * 0.7:
            band_ok = False
        if not (cent_ok or band_ok):
            continue
        # score: bigger shifts score higher
        score = (abs(d_cent) / 500 if cent_ok else 0) + (abs(d_bright) / 3 if band_ok else 0)
        detail_parts = []
        if cent_ok:
            detail_parts.append(f"centroid {int(pre_cent)}->{int(post_cent)} Hz ({d_cent:+.0f})")
        if band_ok:
            detail_parts.append(f"brightness balance {d_bright:+.1f} dB")
        shifts.append(dict(bar_index=i, bar=rows[i]["bar"], t=round(float(rows[i]["t"]), 2),
                           pct=round(100 * float(rows[i]["t"]) / G.dur, 1),
                           level_change_db=round(post_en - pre_en, 1),
                           centroid_shift_hz=int(d_cent) if cent_ok else 0,
                           brightness_shift_db=round(d_bright, 1) if band_ok else 0.0,
                           score=round(score, 2), detail="; ".join(detail_parts)))

    # merge: if two shifts are within 2 bars, keep the stronger one
    merged = []
    for s in sorted(shifts, key=lambda x: -x["score"]):
        if all(abs(s["bar_index"] - q["bar_index"]) >= 3 for q in merged):
            merged.append(s)
    return sorted(merged, key=lambda x: x["t"])


# ── 1-bar fill dips (rev 3) ─────────────────────────────────────────────────
def detect_fill_dips(rows, G, tail, min_dip_db=1.0, max_bars=2):
    """Short dips (1-2 bars) where the level drops >= min_dip_db then jumps back.
    These are fills / impacts that the bar-level breakdown detector skips because they are too short.
    Confirmed cases: onebounce 0:19 (-1.1 to -1.7 dB for 1 bar, onset peak, then recovery)."""
    n = len(rows) if tail is None else min(len(rows), tail.get("bar_index", len(rows)))
    if n < 6:
        return []
    en = np.array([r["total_db"] for r in rows[:n]])
    opb = np.array([r["onsets_per_beat"] for r in rows[:n]])
    fills = []
    for i in range(1, n - 2):
        for w in range(1, max_bars + 1):  # 1 or 2 bar dip
            if i + w >= n:
                continue
            before = en[max(0, i - 1)] if i == 1 else en[max(0, i - 2):i].mean()
            dip = en[i:i + w].mean()
            after = en[i + w] if i + w + 1 >= n else en[i + w:min(n, i + w + 2)].mean()
            depth = before - dip
            recovery = after - dip
            # Immediate adjacent check as alternative to smoothed check
            adj_depth = en[i - 1] - dip
            adj_recovery = en[i + w] - dip
            best_depth = max(depth, adj_depth)
            best_recovery = max(recovery, adj_recovery)
            if best_depth < min_dip_db or best_recovery < min_dip_db:
                continue
            # the bars around it must be at a reasonable level (not in a fade-out)
            if before < en.max() - 15 or after < en.max() - 15:
                continue
            # onset density in the dip bar(s) — a fill often has an onset peak
            dip_onsets = opb[i:i + w].mean()
            pre_onsets = opb[max(0, i - 2):i].mean()
            onset_peak = dip_onsets > pre_onsets + 0.2
            fills.append(dict(bar_index=i, bar=rows[i]["bar"], t=round(float(rows[i]["t"]), 2),
                              bars=w, pct=round(100 * float(rows[i]["t"]) / G.dur, 1),
                              depth_db=round(float(best_depth), 1), recovery_db=round(float(best_recovery), 1),
                              onset_peak=onset_peak,
                              detail=f"{w}-bar dip {best_depth:.1f} dB, recovery {best_recovery:.1f} dB" +
                                     (", onset burst" if onset_peak else "")))
    # merge overlapping fills: keep the deeper one
    merged = []
    for f in sorted(fills, key=lambda x: -x["depth_db"]):
        if all(abs(f["bar_index"] - q["bar_index"]) >= max_bars + 1 for q in merged):
            merged.append(f)
    return sorted(merged, key=lambda x: x["t"])


# ── half-bar fills / snare rolls (rev 4) ────────────────────────────────────
def detect_snare_rolls(peaks, fps, G, tail, min_onsets=5, max_gap_s=0.30):
    """Half-bar fills: a burst of >= min_onsets attacks crowded into the last two beats of a bar
    (typically the snare/tom roll on beat 4). Returns bar, beats 3-4 window and density."""
    n = len(G.t) if tail is None else min(len(G.t), tail.get("bar_index", len(G.t)))
    if n < 2 or len(peaks) == 0:
        return []
    pt = np.asarray(peaks, float) / fps
    beat_s = G.bar_s / G.bpb
    out = []
    for b in range(n):
        t0 = G.t[b] + 2 * beat_s; t1 = G.t[b] + G.bar_s + 1e-6
        sel = pt[(pt >= t0 - 0.02) & (pt < t1)]
        if len(sel) < min_onsets:
            continue
        gaps = np.diff(sel)
        if len(gaps) and float(np.median(gaps)) > max_gap_s:
            continue
        density = len(sel) / max(2 * beat_s, 1e-6)
        out.append(dict(bar=G.bar_no(b), t=round(float(t0), 2), pct=round(100 * float(t0) / G.dur, 1),
                        beats="3-4", onsets=int(len(sel)), density_per_s=round(float(density), 1),
                        detail=f"{len(sel)} attacks in beats 3-4 ({density:.1f}/s) = snare roll / drum fill"))
    merged = []
    for q in sorted(out, key=lambda x: -x["onsets"]):
        if all(abs(q["bar"] - m["bar"]) >= 2 for m in merged):
            merged.append(q)
    return sorted(merged, key=lambda x: x["t"])


# ── chroma-change detector (harmonic section changes with flat loudness, rev 3)
def detect_chroma_changes(rows, chroma_bar, G, tail, min_hold=4, level_cap=3.0, chroma_thresh=0.25):
    """Detects where the harmonic content (chord voicing) changes while loudness stays flat.
    Uses mean-centered chroma cosine distance between consecutive multi-bar windows.
    Confirmed cases: onebounce 0:40 and 1:00 (chord content changes, level flat)."""
    n = len(rows) if tail is None else min(len(rows), tail.get("bar_index", len(rows)))
    if n < min_hold * 2 or chroma_bar.shape[0] < n:
        return []
    en = np.array([r["total_db"] for r in rows[:n]])
    cb = chroma_bar[:n].copy()
    # mean-centre across bars so distinct chord distributions emerge
    cc = cb - cb.mean(0)
    norms = np.linalg.norm(cc, axis=1, keepdims=True) + 1e-9
    cn = cc / norms

    changes = []
    for i in range(min_hold, n - min_hold):
        # level stability across the boundary
        pre_en = en[i - min_hold:i].mean()
        post_en = en[i:i + min_hold].mean()
        if abs(post_en - pre_en) > level_cap:
            continue
        # skip quiet sections (intro / outro)
        if pre_en < en.max() - 15 or post_en < en.max() - 15:
            continue
        # mean normalized chroma before and after
        pre_chroma = cn[i - min_hold:i].mean(0)
        post_chroma = cn[i:i + min_hold].mean(0)
        pre_norm = np.linalg.norm(pre_chroma) + 1e-9
        post_norm = np.linalg.norm(post_chroma) + 1e-9
        cosine_sim = float((pre_chroma @ post_chroma) / (pre_norm * post_norm))
        chroma_dist = 1.0 - cosine_sim
        if chroma_dist < chroma_thresh:
            continue
        # find the dominant chroma note before and after
        pre_root = int(np.argmax(cb[i - min_hold:i].sum(0)))
        post_root = int(np.argmax(cb[i:i + min_hold].sum(0)))
        NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        changes.append(dict(bar_index=i, bar=rows[i]["bar"], t=round(float(rows[i]["t"]), 2),
                            pct=round(100 * float(rows[i]["t"]) / G.dur, 1),
                            level_change_db=round(float(post_en - pre_en), 1),
                            chroma_distance=round(float(chroma_dist), 3),
                            pre_root=NOTE_NAMES[pre_root], post_root=NOTE_NAMES[post_root],
                            detail=f"harmonic shift (chroma dist {chroma_dist:.2f}), "
                                   f"dominant {NOTE_NAMES[pre_root]}->{NOTE_NAMES[post_root]}, "
                                   f"level {post_en - pre_en:+.1f} dB"))

    # merge: within 4 bars, keep the strongest
    merged = []
    for c in sorted(changes, key=lambda x: -x["chroma_distance"]):
        if all(abs(c["bar_index"] - q["bar_index"]) >= 4 for q in merged):
            merged.append(c)
    return sorted(merged, key=lambda x: x["t"])


# ── per-bar features ─────────────────────────────────────────────────────────
def bar_features(t, tot, bands, flux, cent, m, side, sr, G, chroma_bar):
    fi = np.searchsorted(t, G.t); fi = np.append(fi, len(t)); rows = []; energy = []; opb = []
    pk, _ = signal.find_peaks(flux, height=np.median(flux) + 0.9 * flux.std(), distance=max(1, int(0.04 * (sr / HOP))))
    for b in range(G.n):
        a, e = fi[b], max(fi[b + 1], fi[b] + 1)
        p = lambda arr: float(db(np.mean(10 ** (arr[a:e] / 10)))) if e > a else -120.0
        s0, s1 = int(max(G.t[b], 0) * sr), int(min(G.t[b] + G.bar_s, G.dur) * sr)
        sd = float(db(np.mean(side[s0:s1] ** 2) / (np.mean(m[s0:s1] ** 2) + 1e-12))) if s1 > s0 else -60.0
        n_on = int(((pk >= a) & (pk < e)).sum())
        rows.append(dict(bar=G.bar_no(b), t=round(float(G.t[b]), 3), total_db=p(tot), **{k: round(p(v), 1) for k, v in bands.items()},
                         centroid_hz=int(np.mean(cent[a:e])) if e > a else 0, side_mid_db=round(sd, 1), onsets_per_beat=round(n_on / G.bpb, 2)))
        energy.append(rows[-1]["total_db"]); opb.append(n_on / G.bpb)
    top = max(energy) if energy else 0.0
    for r in rows: r["energy_rel_db"] = round(r["total_db"] - top, 1)
    return rows


def chroma_per_bar(mono, G):
    C, ct = A.chroma(mono); out = np.zeros((G.n, 12))
    for b in range(G.n):
        sel = (ct >= G.t[b]) & (ct < G.t[b] + G.bar_s)
        if sel.any(): out[b] = C[:, sel].mean(1)
    return out, C, ct


def feature_matrix(rows, chroma):
    X = np.array([[r["total_db"]] + [r[k] for k in BAND_NAMES] + [r["onsets_per_beat"] * 6.0] for r in rows], float)
    X = np.hstack([X, chroma * 6.0])
    return (X - X.mean(0)) / (X.std(0) + 1e-6)


# ── sections, form, layers ───────────────────────────────────────────────────
def label_sections(bounds, rows, tail=None, dips=(), builds=()):
    """rev 2: the section's energy ignores the tail bars (a fade-out must not make a loud climax look like an outro); a section that starts at a detected
    breakdown / build / tail gets that label; 'outro' is only the tail (or, with no tail found, a quiet last section)."""
    en = np.array([r["energy_rel_db"] for r in rows]); secs = []; edges = [0] + bounds + [len(rows)]; tl = tail["bar_index"] if tail else len(rows)
    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        if b > a:
            body = en[a:min(b, tl)] if a < tl else en[a:b]
            secs.append(dict(a=a, b=b, e=float(np.mean(body))))
    for k, s in enumerate(secs):
        e = s["e"]; hot = e >= -3.0
        first_hot = next((j for j, q in enumerate(secs) if q["e"] >= -3.0), None); last = k == len(secs) - 1
        if hot:
            # If the previous section was already a drop and level did not jump meaningfully, this is a continuation/variation
            if k > 0 and secs[k - 1].get("label", "").startswith("drop") and abs(secs[k]["e"] - secs[k - 1]["e"]) < 1.5:
                s["label"] = "drop cont."
            else:
                s["label"] = "drop"
        elif first_hot is None:
            s["label"] = "intro" if k == 0 else "verse"
        elif k < first_hot:
            # If it's the opening section before the first hot drop, check if it's a ramp or steady groove
            if k == 0:
                s["label"] = "intro"
            else:
                s["label"] = "build"
        else: s["label"] = ("outro" if (last and not tail and e < -3) else "break")
        if tail and s["a"] >= tl: s["label"] = "outro"
        for q in dips:
            if s["a"] == q["a_index"]: s["label"] = "break"; s["kind"] = "breakdown"
        for q in builds:
            if s["a"] == q["a_index"]: s["label"] = "build"; s["kind"] = "build-up"
    for k in range(len(secs) - 1):                                  # a short rising section just before a drop is the build
        if secs[k]["label"] in ("verse", "break", "intro") and secs[k + 1]["label"] == "drop" and secs[k + 1]["e"] - secs[k]["e"] > 3 and (secs[k]["b"] - secs[k]["a"]) <= 8 and k > 0:
            secs[k]["label"] = "build"
    return secs


def form_letters(secs, X):
    reps = [X[s["a"]:s["b"]].mean(0) for s in secs]; letters = []; proto = []; used = {}
    for r in reps:
        best, bs = None, -1.0
        for j, q in enumerate(proto):
            c = float(r @ q / (np.linalg.norm(r) * np.linalg.norm(q) + 1e-9))
            if c > bs: best, bs = j, c
        if best is not None and bs >= 0.55:
            used[best] = used.get(best, 0) + 1; letters.append(chr(65 + best) + ("'" if bs < 0.85 else ""))
        else:
            proto.append(r); used[len(proto) - 1] = 0; letters.append(chr(65 + len(proto) - 1))
    return letters


def layer_moves(rows, secs):
    out = []
    for k in range(1, len(secs)):
        a = secs[k]["a"]; pre = rows[max(0, a - 2):a]; post = rows[a:a + 2]
        if not pre or not post: continue
        mv = []
        for band in BAND_NAMES:
            d = np.mean([r[band] for r in post]) - np.mean([r[band] for r in pre])
            if d >= 3.0: mv.append(f"+{band} {d:.0f}dB")
            elif d <= -3.0: mv.append(f"-{band} {abs(d):.0f}dB")
        out.append(dict(bar=rows[a]["bar"], section=secs[k]["label"], moves=mv))
    return out


def drop_candidates(rows, hits, stops, risers, G, fps):
    """a drop = bar-level energy/bass jump, PLUS credit for the classic anatomy (cut before, riser before, impact on the downbeat): a riser makes the 'before' loud, so energy alone under-rates a good drop"""
    en = np.array([10 ** (r["total_db"] / 10) for r in rows]); lo = np.array([10 ** (db(10 ** (r["sub"] / 10) + 10 ** (r["bass"] / 10)) / 10) for r in rows])
    n = len(rows); sc = np.zeros(n); dl = np.zeros(n); ll = np.zeros(n); bonus = np.zeros(n)
    for b in range(2, n - 1):
        t0 = float(G.t[b]); pre = db(en[max(0, b - 2):b].mean()); post = db(en[b:b + 2].mean()); dl[b] = post - pre
        ll[b] = db(lo[b:b + 2].mean()) - db(lo[max(0, b - 2):b].mean())
        if any(t0 - 0.15 * G.bar_s <= h["t"] <= t0 + 0.5 * G.bar_s and h["jump_db"] >= 8 for h in hits): bonus[b] += 3.0
        if any(t0 - G.bar_s <= q["end"] <= t0 + 0.25 for q in stops): bonus[b] += 2.0
        if any(abs(q["end"] - t0) <= 0.6 * G.bar_s for q in risers): bonus[b] += 1.5
        sc[b] = min(dl[b], 30.0) + 0.5 * max(min(ll[b], 30.0), 0) + bonus[b]
    pk, _ = signal.find_peaks(sc, height=3.0, distance=4); out = []
    for b in pk:
        t0 = float(G.t[b]); win = [h for h in hits if t0 - 0.6 * G.bar_s <= h["t"] <= t0 + 0.6 * G.bar_s]; hit = max(win, key=lambda h: h["jump_db"]) if win else None
        cut = [q for q in stops if t0 - G.bar_s <= q["end"] <= t0 + 0.25]; rise = [q for q in risers if abs(q["end"] - t0) <= 0.6 * G.bar_s]
        pre_rows, post_rows = rows[max(0, b - 2):b], rows[b:b + 2]
        brighter = int(np.mean([r["centroid_hz"] for r in post_rows]) - np.mean([r["centroid_hz"] for r in pre_rows])) if pre_rows and post_rows else 0
        parts = []
        if cut: parts.append(f"cut {cut[-1]['dur_s']} s")
        if rise: parts.append(f"riser +{rise[0]['rise_db']:.0f} dB over {rise[0]['dur_s']} s")
        if hit: parts.append(f"{hit['type']} (+{hit['jump_db']} dB" + (f", one-shot {hit['tail_s']} s)" if hit["tail_s"] is not None else ", level stays up)"))
        parts.append(f"bass {min(ll[b], 30):+.1f} dB, brightness {brighter:+d} Hz")
        out.append(dict(t=round(t0, 3), bar=rows[b]["bar"], pct=round(100 * t0 / G.dur, 1), score=round(float(sc[b]), 1), jump_db=round(float(min(dl[b], 30)), 1), bass_jump_db=round(float(min(ll[b], 30)), 1), brightness_hz=brighter,
                        has_cut=bool(cut), has_riser=bool(rise), impact=(hit["type"] if hit else None), impact_offset_ms=(round((hit["t"] - t0) * 1000) if hit else None), anatomy=" -> ".join(parts)))
    out.sort(key=lambda d: -d["score"]); return sorted(out[:6], key=lambda d: d["t"])


# ── key per section, tempo map, loop-readiness, tempo feel ───────────────────
def section_keys(secs, rows, C, ct, global_key):
    """returns [(key string, margin over the global key)]: a section only gets its own key when it beats the global key by >= 0.08 correlation; otherwise it shows the global key"""
    g = f"{global_key['key']} {global_key['mode']}"; gi = A.NOTE.index(global_key["key"]); gp = np.roll(A.KS_MAJ if global_key["mode"] == "major" else A.KS_MIN, gi); out = []
    for s in secs:
        t0 = rows[s["a"]]["t"]; t1 = rows[min(s["b"], len(rows) - 1)]["t"] + (0.0 if s["b"] < len(rows) else 2.0); sel = (ct >= t0) & (ct < max(t1, t0 + 1.0))
        if sel.sum() < 4: out.append((g, 0.0)); continue
        v = C[:, sel].mean(1); best = A.estimate_key(C[:, sel])[0][0]
        gc = float(np.corrcoef(v, gp)[0, 1]) if v.std() > 1e-9 else 0.0; margin = float(best["score"] - gc)
        out.append((f"{best['key']} {best['mode']}", round(margin, 2)) if margin >= 0.08 and f"{best['key']} {best['mode']}" != g else (g, round(margin, 2)))
    return out


def tempo_map(flux, fps, bpm):
    p = fps * 60.0 / bpm; w = int(12 * fps); hop = int(6 * fps); out = []
    for s in range(0, max(1, len(flux) - w), hop):
        x = flux[s:s + w] - flux[s:s + w].mean()
        if len(x) < w or x.std() < 1e-6: continue
        ac = np.correlate(x, x, "full")[w - 1:]; ac /= ac[0] + 1e-9
        lo, hi = int(p * 0.9), int(p * 1.1) + 1
        if hi >= len(ac): continue
        j = lo + int(np.argmax(ac[lo:hi]))
        if 1 <= j < len(ac) - 1:
            y0, y1, y2 = ac[j - 1], ac[j], ac[j + 1]; den = (y0 - 2 * y1 + y2); j = j + (0.5 * (y0 - y2) / den if abs(den) > 1e-9 else 0)
        out.append(dict(t=round(s / fps, 1), bpm=round(fps * 60.0 / j, 2), conf=round(float(ac[int(round(j))]), 2)))
    chg = []; ok = [o for o in out if o["conf"] >= 0.15]
    for a_, b_ in zip(ok, ok[1:]):
        if abs(a_["bpm"] - bpm) / bpm > 0.03 and abs(b_["bpm"] - bpm) / bpm > 0.03: chg.append(a_["t"])
    return dict(windows=out[:60], changes_at_s=chg[:8], max_drift_pct=round(max([abs(o["bpm"] - bpm) / bpm * 100 for o in ok] or [0.0]), 1))


def tempo_feel(bpm, onsets_per_sec):
    opb = onsets_per_sec * 60.0 / bpm; cands = []
    for mult in (0.5, 1.0, 2.0):
        b = bpm * mult; o = opb / mult
        if b < 60 or b > 230: continue
        cands.append((-abs(math.log2(max(o, 1e-3) / 2.2)) - (0.0 if 70 <= b <= 200 else 1.0), b, o))
    cands.sort(reverse=True)
    rec = cands[0]; gap = (rec[0] - cands[1][0]) if len(cands) > 1 else 1.0
    return dict(analyzer_bpm=round(bpm, 1), feel_bpm=round(rec[1], 1), attacks_per_beat_at_feel=round(rec[2], 2), confidence=("high" if gap > 0.6 else "medium" if gap > 0.25 else "low"),
                other=[round(c[1], 1) for c in cands[1:]], note="attacks-per-beat heuristic (about 2 per beat feels 'normal'); half/double time is a human call: ask which tempo they tap")


def loop_check(m, sr, tot, t, G, fps):
    dur = G.dur; mean = float(db(np.mean(10 ** (tot / 10)))); loud = np.where(tot > mean - 6)[0]
    t_last = float(t[loud[-1]]) if len(loud) else dur; t_first = float(t[loud[0]]) if len(loud) else 0.0
    head = max(-90.0, float(20 * np.log10(np.sqrt(np.mean(m[:int(0.25 * sr)] ** 2)) + 1e-9))); tail = max(-90.0, float(20 * np.log10(np.sqrt(np.mean(m[-int(0.25 * sr):] ** 2)) + 1e-9)))
    bars_total = (dur - G.d0) / G.bar_s; off_bars = bars_total - round(bars_total); issues = []
    fade = max(0.0, dur - t_last); lead_sil = max(0.0, t_first)
    if fade > 0.4: issues.append(f"ends with {fade:.1f} s of fade/silence: a looping Sound would play that gap every cycle")
    if lead_sil > 0.25: issues.append(f"starts with {lead_sil:.1f} s of quiet before the music")
    if abs(tail - head) > 8: issues.append(f"level jump at the seam: last 0.25 s {tail:.0f} dB vs first 0.25 s {head:.0f} dB")
    if abs(off_bars * G.bar_s) > 0.06: issues.append(f"length is {bars_total:.2f} bars from the first downbeat ({off_bars * G.bar_s * 1000:+.0f} ms from a whole bar): a loop would drift off the grid")
    return dict(loop_ready=not issues, issues=issues, fade_out_s=round(fade, 2), lead_in_s=round(lead_sil, 2), head_db=round(head, 1), tail_db=round(tail, 1), bars_from_first_downbeat=round(bars_total, 2),
                note="a rip of a finished track is rarely loop-ready; your own render should pass this before you upload it")


# ── mid-range lead layer (honest replacement for a 'vocal detector') ────────
def lead_layer(Sx, f, t, fps, G, rows):
    """When does a pitched MID-RANGE layer (300-3400 Hz harmonic content: a vocal, a lead synth or a guitar) come and go?
    Relative to this track's own median, so it says 'lead enters at bar 17', never 'vocals'. Syllable-rate modulation was tried and rejected: at 170+ BPM the beat itself sits in that band."""
    mid = (f >= 300) & (f <= 3400)
    H = median_filter(Sx, size=(1, 15)); P = median_filter(Sx, size=(15, 1)); mask = H ** 2 / (H ** 2 + P ** 2 + 1e-12)
    share = ((Sx * mask)[mid] ** 2).sum(0) / ((Sx ** 2).sum(0) + 1e-12); per_bar = []
    for b in range(G.n):
        a = np.searchsorted(t, G.t[b]); e = max(np.searchsorted(t, G.t[b] + G.bar_s), a + 1); per_bar.append(float(share[a:e].mean()) if e > a else 0.0)
    v = np.array(per_bar); z = (v - np.median(v)) / (v.std() + 1e-9); on = z >= 0.5; segs = []; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j + 1 < len(on) and on[j + 1]: j += 1
            if j - i + 1 >= 2: segs.append(dict(bar=rows[i]["bar"], end_bar=rows[j]["bar"], t=rows[i]["t"], end=round(rows[j]["t"] + G.bar_s, 2)))
            i = j + 1
        else: i += 1
    return dict(share_of_bars=round(float(on.mean()), 2), segments=segs[:24], per_bar_share=[round(x_, 3) for x_ in per_bar], relative=True,
                note="a pitched mid-range layer (vocal, lead synth or guitar) is prominent here, relative to the rest of THIS track. It cannot tell which. For lyrics/vocals use `af.py lyrics` (Whisper, optional) or `af.py separate` (Demucs, optional)")


# ── Roblox role guess ────────────────────────────────────────────────────────
def role_guess(feel_bpm, opb, mean_energy_lufs, minor, sections, dur):
    r = []; role = "tension / mid-intensity round music"
    if feel_bpm >= 150 and opb >= 1.5: role = "chase / last-man-standing (fast, driving)"; r.append(f"feel {feel_bpm:.0f} BPM with {opb:.1f} attacks per beat")
    elif feel_bpm < 105 and opb < 1.3: role = "lobby / intermission / ambience (slow, sparse)"; r.append(f"feel {feel_bpm:.0f} BPM, {opb:.1f} attacks per beat")
    else: r.append(f"feel {feel_bpm:.0f} BPM, {opb:.1f} attacks per beat")
    if minor: r.append("minor mode")
    if mean_energy_lufs is not None and mean_energy_lufs > -11: r.append(f"loud master ({mean_energy_lufs} LUFS)")
    return dict(role=role, reasons=r, heuristic=True)


# ── main ─────────────────────────────────────────────────────────────────────
def deep(path, prof=None, bpm_range=None, decoded=None):
    wav, sr, x = decoded or S.load_wav(path)
    if len(x) > MAX_S * sr: x = x[:int(MAX_S * sr)]
    x = x.astype(np.float64); m = x.mean(1); side = (x[:, 0] - x[:, 1]) / 2; dur = len(m) / sr
    prof = prof or A.analyze(wav, quiet=True, bpm_range=bpm_range, max_s=MAX_S)
    G = Grid(prof, dur); fps = sr / HOP
    f, t, Sx = frames(m, sr); bands = band_energy(Sx, f); tot = db((Sx ** 2).sum(0))
    cent = (Sx * f[:, None]).sum(0) / (Sx.sum(0) + 1e-9); flux, flux_lo, flux_hi = flux_curves(Sx, f)
    hits = detect_hits(t, tot, bands, flux, G, fps); stops = detect_stops(t, tot, hits, G, fps); risers = detect_risers(t, bands, tot, G, fps)
    chroma_b, C, ct = chroma_per_bar(m, G); rows = bar_features(t, tot, bands, flux, cent, m, side, sr, G, chroma_b)
    X = feature_matrix(rows, chroma_b)
    bounds, _nov = A.novelty_boundaries(X, min_gap=6, k=max(2, min(4, G.n // 8)), thresh=0.8) if G.n >= 12 else ([], None)
    drops = drop_candidates(rows, hits, stops, risers, G, fps)
    for dp in drops:                                               # a detected drop is always a section boundary
        bi = G.at(dp["bar"])
        if bi is not None and 1 < bi < G.n - 1 and all(abs(bi - q) >= 3 for q in bounds): bounds.append(bi)
    bounds = sorted(set(bounds))
    tail = detect_tail(t, tot, rows, G, fps); dips, builds = detect_dips(rows, G, tail, drops)
    tone_shifts = detect_tone_shifts(rows, G, tail); fill_dips = detect_fill_dips(rows, G, tail); chroma_changes = detect_chroma_changes(rows, chroma_b, G, tail)
    # fills are a SNARE/tom event: look at flux in the 1.5-6 kHz band, not the full mix (hats and bass otherwise trigger it)
    _Ls = np.log1p(Sx * 50.0); _ds = np.maximum(np.diff(_Ls, axis=1, prepend=_Ls[:, :1]), 0)
    snare_flux = _ds[(f >= 1500) & (f < 6000)].sum(0)
    snare_peaks = signal.find_peaks(snare_flux, height=np.median(snare_flux) + 1.1 * snare_flux.std(), distance=max(1, int(0.045 * fps)))[0]
    snare_rolls = detect_snare_rolls(snare_peaks, fps, G, tail, min_onsets=6, max_gap_s=0.17)
    forced = [q["a_index"] for q in dips + builds] + ([tail["bar_index"]] if tail and tail["bar_index"] > 1 else [])
    # tone shifts inject section boundaries (spectral boundaries the energy slicer missed)
    for ts in tone_shifts:
        bi = ts["bar_index"]
        if bi is not None and 1 < bi < G.n - 1 and all(abs(bi - f) >= 3 for f in forced) and all(abs(bi - b) >= 3 for b in bounds):
            bounds.append(bi)
    bounds = sorted(set([b for b in bounds if all(abs(b - f) >= 2 for f in forced)] + [f for f in forced if 0 < f < G.n]))
    secs = label_sections(bounds, rows, tail, dips, builds); letters = form_letters(secs, X); layers = layer_moves(rows, secs)
    keys = section_keys(secs, rows, C, ct, prof["key"]["best"])
    # chord-loop length: bar chroma, mean-centred (otherwise every bar looks 0.99 similar), periodicity peaks
    cc = chroma_b - chroma_b.mean(0); cn = cc / (np.linalg.norm(cc, axis=1, keepdims=True) + 1e-9); loop_scores = {}
    for p_ in range(1, 17):
        if G.n > p_ + 2: loop_scores[p_] = round(float(np.mean((cn[:-p_] * cn[p_:]).sum(1))), 3)
    peaks_ = {}
    for p_ in (2, 4, 8, 16):
        if p_ in loop_scores:
            nb = [loop_scores[q] for q in (p_ - 1, p_ + 1) if q in loop_scores]; peaks_[p_] = loop_scores[p_] - float(np.mean(nb)) if nb else 0.0
    cand_ = {p_: v for p_, v in peaks_.items() if v >= 0.08}
    chord_loop = None
    if cand_:
        top = max(loop_scores[p_] for p_ in cand_); chord_loop = min(p_ for p_ in cand_ if loop_scores[p_] >= top - 0.08)     # a 4-bar cycle also repeats at 8 and 16: report the shortest
    peaks = signal.find_peaks(flux, height=np.median(flux) + 0.9 * flux.std(), distance=max(1, int(0.04 * fps)))[0]; ons_s = len(peaks) / dur
    feel = tempo_feel(G.bpm, ons_s); tm = tempo_map(flux, fps, G.bpm); loop = loop_check(m, sr, tot, t, G, fps); lead = lead_layer(Sx, f, t, fps, G, rows)
    en = np.array([r["energy_rel_db"] for r in rows]); starts_hot = bool(len(en) >= 3 and en[:2].mean() >= en.max() - 4.0 and not drops)
    on_grid = [abs(h["grid_off_ms"]) <= 30 for h in hits]; beat1 = [(h["beat"] - 1) % G.bpb < 0.15 or (h["beat"] - 1) % G.bpb > G.bpb - 0.15 for h in hits]
    sections = []
    for s, lt, (ky, kmargin) in zip(secs, letters, keys):
        a, b = s["a"], s["b"]; seg = rows[a:b]
        sections.append(dict(label=s["label"], form=lt, start_bar=rows[a]["bar"], bars=b - a, t0=rows[a]["t"], t1=round(rows[b - 1]["t"] + G.bar_s, 2) if b - 1 < len(rows) else round(dur, 2), pct=round(100 * (b - a) / max(G.n, 1), 1),
                             energy_rel_db=round(s["e"], 1), bands_db={k: round(float(np.mean([r[k] for r in seg])), 1) for k in BAND_NAMES}, onsets_per_beat=round(float(np.mean([r["onsets_per_beat"] for r in seg])), 2),
                             side_mid_db=round(float(np.mean([r["side_mid_db"] for r in seg])), 1), centroid_hz=int(np.mean([r["centroid_hz"] for r in seg])), key=ky, key_margin=kmargin))
    modul = [dict(section=s["label"], bar=s["start_bar"], key=s["key"], margin=s["key_margin"]) for s in sections if s["key"] != f"{prof['key']['best']['key']} {prof['key']['best']['mode']}"]
    out = dict(schema="audio-forge/deep@1", rev=3, file=os.path.basename(path), seconds=round(dur, 2),
               grid=dict(bpm=round(G.bpm, 2), beats_per_bar=G.bpb, bar_s=round(G.bar_s, 3), first_downbeat_s=round(G.d0, 3), bars=G.n, steady=bool(prof["tempo"]["steady"]),
                         downbeat_phase_confidence=round(G.phase_conf, 2), note="bar 1 = first detected downbeat; with low phase confidence the bar COUNT is right but 'beat 1' may really be beat 2-4"),
               tempo_feel=feel, tempo_map=tm,
               hard_points=dict(hits=hits, stops=stops, risers=risers, drops=drops, breakdowns=dips, builds=builds, tail=tail, tone_shifts=tone_shifts, fill_dips=fill_dips, chroma_changes=chroma_changes, snare_rolls=snare_rolls, starts_hot=starts_hot,
                                hits_per_min=round(len(hits) * 60.0 / dur, 1), stops_per_min=round(len(stops) * 60.0 / dur, 1),
                                hits_on_16th_grid_share=round(float(np.mean(on_grid)), 2) if hits else None, hits_on_beat1_share=round(float(np.mean(beat1)), 2) if hits else None,
                                hit_types={k: sum(1 for h in hits if h["type"] == k) for k in ("full impact", "sub/kick impact", "crash/high burst", "accent")}),
               sections=sections, form="".join(f"{l} " for l in letters).strip(), layer_moves=layers, key_modulations=modul,
               phrase=dict(chord_loop_bars=chord_loop, similarity_by_period=loop_scores, note="None = no repeating chord cycle found (long sections, slowly changing harmony)"), loop=loop, lead_layer=lead,
               bars=rows, role_guess=role_guess(feel["feel_bpm"], feel["attacks_per_beat_at_feel"], prof["loudness"].get("lufs"), prof["key"]["best"]["mode"] == "minor", sections, dur),
               loudness=prof["loudness"], key=prof["key"]["best"], analyzer_profile=dict(tempo=prof["tempo"]["bpm"], librosa_tempo=prof.get("librosa_tempo")))
    return clean(out)


# ── outputs ──────────────────────────────────────────────────────────────────
def timeline_md(d, name):
    g = d["grid"]; hp = d["hard_points"]; L = [f"# Deep analysis: {name}", "", f"{d['seconds']} s, grid {g['bpm']} BPM ({g['beats_per_bar']}/4, {'steady' if g['steady'] else 'NOT steady'}), first downbeat {g['first_downbeat_s']} s, {g['bars']} bars. {g['note']}.",
                                                 f"Tempo feel: analyzer {d['tempo_feel']['analyzer_bpm']} -> feels like **{d['tempo_feel']['feel_bpm']} BPM** ({d['tempo_feel']['confidence']} confidence; other readings {d['tempo_feel']['other']}). Ask the person which tempo they tap.",
                                                 f"Key {d['key']['key']} {d['key']['mode']}, {d['loudness']['lufs']} LUFS. Form: **{d['form']}**. Chord cycle: {str(d['phrase']['chord_loop_bars']) + ' bars' if d['phrase']['chord_loop_bars'] else 'no clear repeating cycle'}. Role guess (heuristic): {d['role_guess']['role']}.", "",
                                                 "Nobody has listened to this. Labels like drop/break are heuristics from energy; the person's ears decide.", "", "## Hard points (in time order)", "| time | bar:beat | % | kind | detail |", "|---|---|---|---|---|"]
    ev = []
    for h in hp["hits"]: ev.append((h["t"], f"{h['bar']}:{h['beat']}", h["pct"], "hit", f"{h['type']} +{h['jump_db']} dB (low {h['low_jump_db']:+}, high {h['high_jump_db']:+}), {('one-shot, level back in ' + str(h['tail_s']) + ' s') if h['tail_s'] is not None else 'level stays up (entrance)'}, {h['grid_off_ms']:+} ms off the 16th grid"))
    for s in hp["stops"]: ev.append((s["t"], f"{s['bar']}:{s['beat']}", s["pct"], "STOP", f"cut {s['dur_s']} s, -{s['depth_db']} dB" + (f", then {s['then']}" if s["then"] else "")))
    for r in hp["risers"]: ev.append((r["t"], f"{r['bar']}:{r['beat']}", r["pct"], "riser", f"+{r['rise_db']} dB over {r['dur_s']} s (linearity {r['linearity']})"))
    for p in hp["drops"]: ev.append((p["t"], f"{p['bar']}:1.0", p["pct"], "**DROP**", f"+{p['jump_db']} dB: {p['anatomy']}"))
    for q in hp.get("breakdowns", []): ev.append((q["t"], f"{q['bar']}:1.0", q["pct"], "BREAKDOWN", f"{q['bars']} bars (to bar {q['end_bar']}, {mmss(q['end'])}), {q['depth_db']} dB under its surroundings, bass {q['bass_drop_db']:+.1f} dB" + (", leads into a drop" if q["leads_into_drop"] else "")))
    for q in hp.get("builds", []): ev.append((q["t"], f"{q['bar']}:1.0", q["pct"], "BUILD", f"{q['bars']} bars (to bar {q['end_bar']}, {mmss(q['end'])}), onset density {q['onset_density_rise']:+}/beat, level {q['level_slope_db_per_bar']:+} dB/bar"))
    for q in hp.get("tone_shifts", []): ev.append((q["t"], f"{q['bar']}:1.0", q["pct"], "TONE SHIFT", q["detail"]))
    for q in hp.get("fill_dips", []): ev.append((q["t"], f"{q['bar']}:1.0", q["pct"], "FILL", q["detail"]))
    for q in hp.get("snare_rolls", []): ev.append((q["t"], f"{q['bar']}:3.0", q["pct"], "HALF-BAR FILL", q["detail"]))
    for q in hp.get("chroma_changes", []): ev.append((q["t"], f"{q['bar']}:1.0", q["pct"], "HARMONIC SHIFT", q["detail"]))
    if hp.get("tail"): q = hp["tail"]; ev.append((q["t_cut"], f"{q['bar']}:{q['beat']}", q["pct"], "END CUT" if q["kind"].startswith("hard") else "FADE", f"{q['kind']}: music last at normal level, then {q['tail_s']} s of tail ({q['fall_db_in_1s']} dB down within 1 s)"))
    for t_, bb, pc, k, dt in sorted(ev): L.append(f"| {mmss(t_)} | {bb} | {pc} | {k} | {dt} |")
    L += ["", f"Hits per minute {hp['hits_per_min']}, stops per minute {hp['stops_per_min']}, hits on the 16th grid {hp['hits_on_16th_grid_share']}, hits on beat 1 {hp['hits_on_beat1_share']}, types {hp['hit_types']}." + (" Track starts already at full energy (no drop to find)." if hp["starts_hot"] else ""),
          "", "## Sections", "| bar | time | len | label | form | energy | key | layers entering / leaving |", "|---|---|---|---|---|---|---|---|"]
    mv = {x["bar"]: x["moves"] for x in d["layer_moves"]}
    for s in d["sections"]: L.append(f"| {s['start_bar']} | {mmss(s['t0'])} | {s['bars']} bars | {s['label']} | {s['form']} | {s['energy_rel_db']} dB | {s['key']} | {', '.join(mv.get(s['start_bar'], [])) or '-'} |")
    L += ["", f"## Loop-readiness: {'READY' if d['loop']['loop_ready'] else 'NOT ready'}"] + [f"- {i}" for i in d["loop"]["issues"]] + [f"- {d['loop']['note']}", "",
          f"## Mid-range lead layer (vocal, lead synth or guitar; relative to this track): prominent in {int(d['lead_layer']['share_of_bars'] * 100)}% of bars", ", ".join(f"bars {s['bar']}-{s['end_bar']} ({mmss(s['t'])}-{mmss(s['end'])})" for s in d["lead_layer"]["segments"]) or "none stands out", "",
          f"Tempo drift max {d['tempo_map']['max_drift_pct']}%" + (f", changes near {d['tempo_map']['changes_at_s']} s" if d["tempo_map"]["changes_at_s"] else ", no tempo change found") + ".", "", "## Bar map (energy relative to the loudest bar; marks = events inside the bar)"]
    marks = {}
    for t_, bb, pc, k, dt in sorted(ev): marks.setdefault(int(bb.split(":")[0]), []).append(k)
    for r in d["bars"][:240]:
        bar = "#" * max(0, int(round((r["energy_rel_db"] + 30) / 30 * 28))) if r["energy_rel_db"] > -30 else ""
        L.append(f"{r['bar']:>4} {mmss(r['t']):>8}  {r['energy_rel_db']:>6.1f} dB  {bar:<28}  {' '.join(marks.get(r['bar'], []))}")
    return "\n".join(L) + "\n"


def write_labels(d, path):
    rows = [(s["t0"], s["t1"], f"{s['label']} {s['form']}") for s in d["sections"]]
    hp = d["hard_points"]
    rows += [(p["t"], p["t"], "DROP") for p in hp["drops"]] + [(s["t"], s["end"], "stop") for s in hp["stops"]] + [(r["t"], r["end"], "riser") for r in hp["risers"]] + [(q["t"], q["end"], "BREAKDOWN") for q in hp.get("breakdowns", [])] + [(q["t"], q["end"], "BUILD") for q in hp.get("builds", [])] + [(q["t"], q["t"], "TONE SHIFT") for q in hp.get("tone_shifts", [])] + [(q["t"], q["t"], "FILL") for q in hp.get("fill_dips", [])] + [(q["t"], q["t"] + 0.001, "HALF-BAR FILL") for q in hp.get("snare_rolls", [])] + [(q["t"], q["t"], "HARMONIC SHIFT") for q in hp.get("chroma_changes", [])] + ([(hp["tail"]["t_cut"], hp["tail"]["t_cut"], "END CUT")] if hp.get("tail") else []) + [(h["t"], h["t"], h["type"]) for h in hp["hits"]]
    with open(path, "w") as fh:
        for a, b, lab in sorted(rows): fh.write(f"{a:.4f}\t{b:.4f}\t{lab}\n")


def write_csv(d, path):
    hp = d["hard_points"]
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["kind", "time_s", "end_s", "bar", "beat", "pct", "strength_db", "detail"])
        for h in hp["hits"]: w.writerow(["hit", h["t"], "", h["bar"], h["beat"], h["pct"], h["jump_db"], h["type"]])
        for s in hp["stops"]: w.writerow(["stop", s["t"], s["end"], s["bar"], s["beat"], s["pct"], s["depth_db"], s["then"] or ""])
        for r in hp["risers"]: w.writerow(["riser", r["t"], r["end"], r["bar"], r["beat"], r["pct"], r["rise_db"], ""])
        for q in hp.get("breakdowns", []): w.writerow(["breakdown", q["t"], q["end"], q["bar"], 1, q["pct"], q["depth_db"], f"{q['bars']} bars, leads_into_drop={q['leads_into_drop']}"])
        for q in hp.get("builds", []): w.writerow(["build", q["t"], q["end"], q["bar"], 1, q["pct"], q["level_slope_db_per_bar"], f"{q['bars']} bars, onset_rise={q['onset_density_rise']}"])
        if hp.get("tail"): q = hp["tail"]; w.writerow(["end_cut", q["t_cut"], "", q["bar"], q["beat"], q["pct"], q["fall_db_in_1s"], f"{q['kind']}, tail {q['tail_s']} s"])
        for p in hp["drops"]: w.writerow(["drop", p["t"], "", p["bar"], 1, p["pct"], p["jump_db"], p["anatomy"]])
        for q in hp.get("tone_shifts", []): w.writerow(["tone_shift", q["t"], "", q["bar"], 1, q["pct"], q.get("centroid_shift_hz", 0), q["detail"]])
        for q in hp.get("fill_dips", []): w.writerow(["fill_dip", q["t"], "", q["bar"], 1, q["pct"], q["depth_db"], q["detail"]])
        for q in hp.get("snare_rolls", []): w.writerow(["snare_roll", q["t"], "", q["bar"], 3, q["pct"], q["onsets"], q["detail"]])
        for q in hp.get("chroma_changes", []): w.writerow(["chroma_change", q["t"], "", q["bar"], 1, q["pct"], q["chroma_distance"], q["detail"]])


def timeline_png(d, out):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False
    W, H = 1600, 560; im = Image.new("RGB", (W, H), (18, 18, 24)); dr = ImageDraw.Draw(im); dur = d["seconds"]; X = lambda t_: int(40 + (W - 60) * t_ / dur)
    col = {"intro": (60, 90, 140), "build": (150, 120, 40), "drop": (150, 50, 50), "break": (50, 120, 110), "outro": (80, 80, 110), "verse": (90, 90, 90)}
    for s in d["sections"]:
        dr.rectangle([X(s["t0"]), 20, X(min(s["t1"], dur)), 44], fill=col.get(s["label"], (90, 90, 90))); dr.text((X(s["t0"]) + 3, 26), f"{s['label']} {s['form']}", fill=(255, 255, 255))
    bars = d["bars"]; ys = lambda v, top, h: top + h - int(max(0, min(1, (v + 40) / 40)) * h)
    pts = [(X(r["t"] + d["grid"]["bar_s"] / 2), ys(r["energy_rel_db"], 60, 170)) for r in bars]
    if len(pts) > 1: dr.line(pts, fill=(240, 240, 240), width=2)
    for band, c in (("bass", (230, 90, 90)), ("mid", (90, 200, 120)), ("highmid", (90, 150, 240))):
        top_ = max(r[band] for r in bars); dr.line([(X(r["t"] + d["grid"]["bar_s"] / 2), ys(r[band] - top_, 250, 120)) for r in bars], fill=c, width=1)
    dr.text((40, 48), "total energy (white), bass (red), mid (green), high-mid (blue); dB relative to each curve's loudest bar", fill=(170, 170, 170))
    hp = d["hard_points"]
    for h in hp["hits"]: dr.line([X(h["t"]), 400, X(h["t"]), 400 - min(60, int(h["jump_db"] * 4))], fill=(255, 170, 60), width=1)
    for s in hp["stops"]: dr.rectangle([X(s["t"]), 410, max(X(s["end"]), X(s["t"]) + 2), 430], fill=(255, 255, 255))
    for r in hp["risers"]: dr.polygon([(X(r["t"]), 460), (X(r["end"]), 440), (X(r["end"]), 460)], fill=(90, 220, 130))
    for p in hp["drops"]: dr.line([X(p["t"]), 20, X(p["t"]), 470], fill=(255, 70, 70), width=2); dr.text((X(p["t"]) + 3, 474), f"DROP bar {p['bar']}", fill=(255, 120, 120))
    for sgm in d["lead_layer"]["segments"]: dr.rectangle([X(sgm["t"]), 500, X(sgm["end"]), 510], fill=(120, 170, 255))
    dr.text((40, 400), "hits (orange)", fill=(255, 170, 60)); dr.text((40, 432), "stops (white)", fill=(230, 230, 230)); dr.text((40, 500), "mid lead layer (relative)", fill=(120, 170, 255))
    im.save(out); return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio"); ap.add_argument("--out"); ap.add_argument("--name"); ap.add_argument("--bpm-range", nargs=2, type=float); ap.add_argument("--no-png", action="store_true"); ap.add_argument("--json", action="store_true", help="print deep.json to stdout")
    a = ap.parse_args(); name = a.name or os.path.splitext(os.path.basename(a.audio))[0]; name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name).strip("-").lower()
    out = a.out or os.path.join("deep", name); os.makedirs(out, exist_ok=True)
    d = deep(a.audio, bpm_range=tuple(a.bpm_range) if a.bpm_range else None)
    json.dump(d, open(os.path.join(out, "deep.json"), "w"), indent=1); md = timeline_md(d, name); open(os.path.join(out, "timeline.md"), "w").write(md)
    write_labels(d, os.path.join(out, "labels.txt")); write_csv(d, os.path.join(out, "hardpoints.csv")); png = False if a.no_png else timeline_png(d, os.path.join(out, "timeline.png"))
    print(json.dumps(d) if a.json else md); print(f"[wrote {out}/deep.json, timeline.md, labels.txt, hardpoints.csv" + (", timeline.png" if png else "") + "]", file=sys.stderr)


if __name__ == "__main__":
    main()

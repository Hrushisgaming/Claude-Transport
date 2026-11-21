#!/usr/bin/env python3
"""loop_doctor.py - diagnose and repair a music loop (Roblox Sound, game bed, video loop).

  af.py loop_doctor loop.wav                          # diagnose only
  af.py loop_doctor loop.wav --bpm 178                # diagnose with a known tempo
  af.py loop_doctor loop.wav --repair fixed.wav       # diagnose + repair
  af.py loop_doctor loop.wav --repair fixed.wav --json

WHAT IT CHECKS
  * seam click: distance between the last and the first sample vs the file's own largest normal step
  * head/tail silence: a loop that fades out pumps every cycle
  * whole-bar length: at the given BPM a loop must be a whole number of bars or the grid drifts
  * DC offset, clipping, true peak, sub-bass mono compatibility (a stereo sub cancels on phone speakers)
  * tail overlap: reverb/decay that spills past the loop point (it gets folded back onto the start)

REPAIRS (--repair)
  1. snap to a whole number of bars at the given BPM (or keep the length when --bars is not given)
  2. fold the tail back onto the start (so the decay plays on instead of being cut)
  3. optional micro-fade (--xfade MS, default 3 ms) at the very edges to kill a click
  4. remove DC, and peak-normalise to --target-peak (default -1.5 dBFS)

It measures; it does not judge. Whether the loop sounds good is the person's call.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audioutil as U


def seam_stats(x, sr):
    """seam click + edge silence + DC + clipping, measured on the file as it is"""
    x = U.to_stereo(x)
    mono = x.mean(1)
    n = len(mono)
    w = max(1, int(0.05 * sr))
    head = U.rms_db(mono[:w]); tail = U.rms_db(mono[-w:]); body = U.rms_db(mono)
    jump = float(np.max(np.abs(x[0] - x[-1]))) if n > 1 else 0.0
    steps = np.abs(np.diff(x, axis=0)).max(axis=1) if n > 2 else np.array([1e-9])
    step = float(np.percentile(steps, 99.5)) + 1e-9
    return dict(head_db=round(head, 1), tail_db=round(tail, 1), body_db=round(body, 1),
                seam_jump=round(jump, 6), normal_step=round(step, 6), seam_jump_vs_step=round(jump / step, 2),
                dc_offset=round(float(mono.mean()), 5), clipped_samples=int((np.abs(x) >= 0.999).sum()))


def diagnose(path, bpm=None, bars=None):
    x, sr = U.read_audio(path)
    m = U.to_stereo(x)
    res = U.measure(path)
    res.update(seam_stats(m, sr))
    issues = []
    if res["seam_jump_vs_step"] > 1.5:
        issues.append(f"seam click risk: the last sample is {res['seam_jump_vs_step']}x the file's largest normal step away from the first")
    if res["tail_db"] < res["body_db"] - 25:
        issues.append(f"ends in near-silence ({res['tail_db']} dB vs body {res['body_db']} dB): the loop pumps")
    if res["head_db"] < res["body_db"] - 25:
        issues.append(f"starts in near-silence ({res['head_db']} dB vs body {res['body_db']} dB)")
    if abs(res["dc_offset"]) > 0.002:
        issues.append(f"DC offset {res['dc_offset']}: high-pass the loop around 25-30 Hz")
    if res["clipped_samples"]:
        issues.append(f"{res['clipped_samples']} samples at/over full scale")
    if res["true_peak_db"] is not None and res["true_peak_db"] > -1.0:
        issues.append(f"true peak {res['true_peak_db']} dBFS: little headroom; aim for <= -1.5")
    if res["low_corr"] < 0.85:
        issues.append(f"sub-bass is not mono (corr {res['low_corr']}): it can cancel on phone speakers / in a club")
    if bpm:
        bar_s = 240.0 / bpm
        exact = len(m) / sr / bar_s
        res["bars_exact"] = round(exact, 4)
        res["bars_rounded"] = int(round(exact))
        if abs(exact - round(exact)) > 0.01:
            issues.append(f"{exact:.3f} bars at {bpm} BPM: not a whole number of bars, so the loop drifts off the grid")
        if bars is not None and bars != int(round(exact)):
            issues.append(f"file holds {exact:.3f} bars but --bars {bars} was requested")
    res["issues"] = issues
    res["ready"] = not issues
    return res, x, sr


def repair(x, sr, bpm=None, bars=None, xfade_ms=3.0, target_peak=-1.5, fold_tail=True):
    """snap to whole bars, fold the tail onto the head, micro-fade, DC clean, peak normalise"""
    x = U.to_stereo(np.asarray(x, dtype=np.float64))
    report = dict(input_seconds=round(len(x) / sr, 3))
    if bpm:
        bar_s = 240.0 / bpm
        want_bars = bars if bars else max(1, int(round(len(x) / sr / bar_s)))
        L = int(round(want_bars * bar_s * sr))
    else:
        want_bars = None; L = len(x)
    main = x[:L] if L <= len(x) else U.fit_length(x, L)
    tail = x[L:] if fold_tail and L < len(x) else np.zeros((0, x.shape[1]))
    if len(tail):
        n = min(len(tail), L)
        main[:n] += tail[:n]
    report["bars"] = want_bars
    report["output_seconds"] = round(len(main) / sr, 3)
    report["tail_folded_s"] = round(len(tail) / sr, 3)
    # DC removal (very low corner, keeps the low end)
    main = main - main.mean(axis=0, keepdims=True)
    # micro-fade at both edges so a click cannot survive
    n = int(max(0.0, xfade_ms) * 1e-3 * sr)
    if n > 1 and len(main) > 2 * n:
        ramp = np.linspace(0, 1, n) ** 1.5
        main[:n] *= ramp[:, None]
        main[-n:] *= ramp[::-1][:, None]
        report["micro_fade_ms"] = xfade_ms
    else:
        report["micro_fade_ms"] = 0
    pk = float(np.abs(main).max())
    if pk > 0:
        main *= (10 ** (target_peak / 20.0)) / pk
    report["peak_after_dbfs"] = round(U.peak_db(main), 2)
    return main, report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--bpm", type=float, help="tempo of the loop (needed for the whole-bar check)")
    ap.add_argument("--bars", type=int, help="how many bars the loop should hold")
    ap.add_argument("--repair", metavar="OUT", help="write a repaired loop here")
    ap.add_argument("--xfade", type=float, default=3.0, help="micro-fade at the edges in ms (default 3)")
    ap.add_argument("--target-peak", type=float, default=-1.5, help="peak of the repaired file in dBFS (default -1.5)")
    ap.add_argument("--no-fold", action="store_true", help="do not fold the tail back onto the start")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    a = ap.parse_args()
    if not os.path.exists(a.audio):
        raise SystemExit(f"loop_doctor: no such file: {a.audio}")
    bpm = a.bpm
    if bpm is None:
        try:
            bpm, _ = U.bpm_of(a.audio)
        except Exception:
            bpm = None
    res, x, sr = diagnose(a.audio, bpm, a.bars)
    if a.repair:
        fixed, rep = repair(x, sr, bpm, a.bars, a.xfade, a.target_peak, fold_tail=not a.no_fold)
        U.write_wav(a.repair, fixed, sr)
        res["repair"] = dict(out=os.path.abspath(a.repair), **rep)
        res2, _, _ = diagnose(a.repair, bpm, a.bars)
        res["after"] = res2
        res["issues_after"] = res2["issues"]
        res["ready_after"] = res2["ready"]
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        print(f"# loop doctor: {res['file']}")
        print(f"{res['seconds']} s, {res['sr']} Hz, {res['channels']} ch, peak {res['peak_dbfs']} dBFS, LUFS {res['lufs']}, sub corr {res['low_corr']}")
        if bpm:
            print(f"tempo {bpm:g} BPM -> {res.get('bars_exact')} bars (whole bars: {'yes' if res['ready'] else 'see issues'})")
        print(f"seam: {res['seam_jump_vs_step']}x the normal sample step | head {res['head_db']} dB | tail {res['tail_db']} dB | body {res['body_db']} dB")
        print("\nissues:" if res["issues"] else "\nno automatic issue found (that is not proof it loops cleanly: listen to it twice in a row)")
        for i in res["issues"]:
            print(f"- {i}")
        if a.repair:
            print(f"\nrepaired -> {res['repair']['out']}")
            for k, v in res["repair"].items():
                if k != "out":
                    print(f"  {k}: {v}")
            print("issues after repair:" if res["issues_after"] else "no automatic issue left after the repair")
            for i in res["issues_after"]:
                print(f"- {i}")
            print("Listen to the repaired loop twice in a row before shipping it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

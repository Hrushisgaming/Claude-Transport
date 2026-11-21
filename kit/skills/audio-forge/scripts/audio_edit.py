#!/usr/bin/env python3
"""audio_edit.py -- everyday audio editing on top of ffmpeg (nothing else to install).

  info FILE                                  duration, codec, channels, sample rate, loudness
  extract VIDEO OUT.wav                      pull the audio out of a video
  trim IN OUT --start 3.5 --end 12           cut a region (seconds)
  fade IN OUT --in 0.5 --out 2               fade in / out
  norm IN OUT [--lufs -14] [--tp -1.5]       two-pass loudness normalisation (streaming = -14, speech/podcast = -16)
  convert IN OUT [--bitrate 192k]            any format to any format (wav mp3 flac ogg m4a opus)
  concat A B C... --out OUT [--xfade 0.5]    join files, optional crossfade
  mix A.wav:gain_db:delay_s B.wav:... --out OUT [--dur 60]   layer files with per-file gain and start offset
  duck MUSIC VOICE OUT [--amount 0.35] [--delay 6]   music dips under the voice (sidechain); voice starts at --delay seconds
  stretch IN OUT --factor 1.25               speed up/slow down WITHOUT changing pitch (0.5-4)
  pitch IN OUT --semitones -3 [--keep-tempo] pitch shift (rubberband if present, else resample)
  eq IN OUT [--hp 80] [--lp 12000]           high-pass / low-pass
  loop IN OUT --dur 90 [--xfade 1.0]         loop a bed to a length with crossfaded seams
  silence IN OUT [--thresh -45]              trim leading/trailing silence
  mux VIDEO AUDIO OUT [--mode replace|mix] [--orig-db -18]   put audio on a video (never re-encodes video)
  beatcut IN OUT --beatmap map.json --every 1 [--bars]       re-cut audio on beat boundaries (loops/repeats a beat slice)
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile


def run(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-1500:])
    return r


def ff(*args):
    return run(["ffmpeg", "-y", "-nostdin", "-v", "error", *map(str, args)])


def duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", path])
    return float(r.stdout.strip())


def has_filter(name):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return re.search(r"\b" + name + r"\b", out) is not None


def atempo_chain(f):
    parts = []
    while f > 2.0:
        parts.append(2.0); f /= 2.0
    while f < 0.5:
        parts.append(0.5); f /= 0.5
    parts.append(f)
    return ",".join(f"atempo={p:.5f}" for p in parts)


def tempo_shift_file(inp, out, factor):
    ff("-i", inp, "-filter:a", atempo_chain(factor), out)


def info(a):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate:stream=codec_name,channels,sample_rate,codec_type",
             "-of", "json", a.files[0]])
    j = json.loads(r.stdout)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from analyze import loudness
        j["loudness"] = loudness(a.files[0], 600)
    except Exception:
        pass
    print(json.dumps(j, indent=1))


def norm(inp, out, lufs=-14.0, tp=-1.5, lra=11.0):
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", inp, "-af", f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        ff("-i", inp, "-af", f"loudnorm=I={lufs}:TP={tp}:LRA={lra}", out)
        return
    d = json.loads(m.group(0))
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA={lra}:measured_I={d['input_i']}:measured_LRA={d['input_lra']}:"
          f"measured_TP={d['input_tp']}:measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true")
    ff("-i", inp, "-af", af, "-ar", 44100, out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd")
    ap.add_argument("files", nargs="*")
    ap.add_argument("--out"); ap.add_argument("--start", type=float); ap.add_argument("--end", type=float)
    ap.add_argument("--in", dest="fin", type=float, default=0.0); ap.add_argument("--fade-out", "--out-fade", dest="fout", type=float, default=0.0)
    ap.add_argument("--lufs", type=float, default=-14.0); ap.add_argument("--tp", type=float, default=-1.5)
    ap.add_argument("--bitrate", default="192k"); ap.add_argument("--xfade", type=float, default=0.0)
    ap.add_argument("--dur", type=float); ap.add_argument("--amount", type=float, default=0.35)
    ap.add_argument("--factor", type=float, default=1.0); ap.add_argument("--semitones", type=float, default=0.0)
    ap.add_argument("--keep-tempo", action="store_true"); ap.add_argument("--hp", type=float); ap.add_argument("--lp", type=float)
    ap.add_argument("--thresh", type=float, default=-45.0); ap.add_argument("--mode", default="replace"); ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--orig-db", type=float, default=-18.0); ap.add_argument("--beatmap"); ap.add_argument("--every", type=float, default=1.0)
    a = ap.parse_args()
    f = a.files
    c = a.cmd
    if c == "info":
        return info(a)
    if c == "extract":
        ff("-i", f[0], "-vn", "-ac", 2, "-ar", 44100, f[1])
    elif c == "trim":
        args = ["-i", f[0]]
        if a.start is not None: args = ["-ss", a.start] + args
        if a.end is not None: args += ["-to", a.end - (a.start or 0)]
        ff(*args, f[1])
    elif c == "fade":
        d = duration(f[0]); fl = []
        if a.fin: fl.append(f"afade=t=in:d={a.fin}")
        if a.fout: fl.append(f"afade=t=out:st={max(d - a.fout, 0)}:d={a.fout}")
        ff("-i", f[0], "-af", ",".join(fl) or "anull", f[1])
    elif c == "norm":
        norm(f[0], f[1], a.lufs, a.tp)
    elif c == "convert":
        ext = os.path.splitext(f[1])[1].lower()
        extra = ["-b:a", a.bitrate] if ext in (".mp3", ".m4a", ".ogg", ".opus", ".aac") else []
        ff("-i", f[0], *extra, f[1])
    elif c == "concat":
        out = a.out or f[-1]
        ins = f if a.out else f[:-1]
        if a.xfade > 0 and len(ins) > 1:
            args, fl, last = [], [], "0:a"
            for i, p in enumerate(ins):
                args += ["-i", p]
            for i in range(1, len(ins)):
                fl.append(f"[{last}][{i}:a]acrossfade=d={a.xfade}:c1=tri:c2=tri[x{i}]")
                last = f"x{i}"
            ff(*args, "-filter_complex", ";".join(fl), "-map", f"[{last}]", out)
        else:
            args = []
            for p in ins: args += ["-i", p]
            ff(*args, "-filter_complex", f"concat=n={len(ins)}:v=0:a=1[o]", "-map", "[o]", out)
    elif c == "mix":
        args, fl, labels = [], [], []
        for i, spec in enumerate(f):
            parts = spec.split(":")
            path = parts[0]; g = float(parts[1]) if len(parts) > 1 else 0.0; d = float(parts[2]) if len(parts) > 2 else 0.0
            args += ["-i", path]
            fl.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,volume={g}dB,adelay={int(d*1000)}|{int(d*1000)}[a{i}]")
            labels.append(f"[a{i}]")
        fl.append("".join(labels) + f"amix=inputs={len(f)}:normalize=0:duration=longest[o]")
        extra = ["-t", a.dur] if a.dur else []
        ff(*args, "-filter_complex", ";".join(fl), "-map", "[o]", *extra, a.out)
    elif c == "duck":
        music, voice, out = f
        ratio = 3 + 9 * a.amount
        d_music = duration(music)
        dl = int(a.delay * 1000)
        # pad the voice with silence so the sidechain runs for the whole music length (otherwise ffmpeg stops at the shorter input)
        fc = (f"[1:a]adelay={dl}|{dl},apad=whole_dur={d_music:.3f},aformat=channel_layouts=stereo,asplit=2[sc][v];"
              f"[0:a]aformat=channel_layouts=stereo[mu];[mu][sc]sidechaincompress=threshold=0.03:ratio={ratio:.1f}:attack=15:release=350:makeup=1[m];"
              f"[m][v]amix=inputs=2:normalize=0:duration=first[o]")
        ff("-i", music, "-i", voice, "-filter_complex", fc, "-map", "[o]", "-t", f"{d_music:.3f}", out)
    elif c == "stretch":
        tempo_shift_file(f[0], f[1], a.factor)
    elif c == "pitch":
        r = 2 ** (a.semitones / 12.0)
        if has_filter("rubberband"):
            ff("-i", f[0], "-af", f"rubberband=pitch={r}" + ("" if a.keep_tempo or True else ""), f[1])
        else:
            sr = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "default=nk=1:nw=1", f[0]],
                                    capture_output=True, text=True).stdout.strip() or 44100)
            ff("-i", f[0], "-af", f"asetrate={sr*r:.1f},aresample={sr}," + atempo_chain(1 / r) if a.keep_tempo else f"asetrate={sr*r:.1f},aresample={sr}", f[1])
    elif c == "eq":
        fl = []
        if a.hp: fl.append(f"highpass=f={a.hp}")
        if a.lp: fl.append(f"lowpass=f={a.lp}")
        ff("-i", f[0], "-af", ",".join(fl) or "anull", f[1])
    elif c == "loop":
        d = duration(f[0]); n = int(a.dur / max(d - a.xfade, 0.1)) + 2
        tmp = tempfile.mkdtemp(); lst = os.path.join(tmp, "l.txt")
        if a.xfade > 0:
            args = []
            for _ in range(n): args += ["-i", f[0]]
            fl, last = [], "0:a"
            for i in range(1, n):
                fl.append(f"[{last}][{i}:a]acrossfade=d={a.xfade}:c1=tri:c2=tri[x{i}]"); last = f"x{i}"
            ff(*args, "-filter_complex", ";".join(fl), "-map", f"[{last}]", "-t", a.dur, f[1])
        else:
            open(lst, "w").write("".join(f"file '{os.path.abspath(f[0])}'\n" for _ in range(n)))
            ff("-f", "concat", "-safe", 0, "-i", lst, "-t", a.dur, f[1])
        shutil.rmtree(tmp, ignore_errors=True)
    elif c == "silence":
        t = a.thresh
        ff("-i", f[0], "-af", f"silenceremove=start_periods=1:start_threshold={t}dB:stop_periods=1:stop_threshold={t}dB:stop_duration=0.4", f[1])
    elif c == "voice":
        # speech clean-up for talking heads / tutorials: rumble cut, gentle denoise, even-out, loudness
        fl = ["highpass=f=80", "afftdn=nr=12:nf=-45" if has_filter("afftdn") else "anull",
              "acompressor=threshold=-21dB:ratio=3:attack=8:release=120:makeup=3", "loudnorm=I=%s:TP=-1.5:LRA=9" % (a.lufs if a.lufs != -14.0 else -16)]
        ff("-i", f[0], "-af", ",".join(fl), f[1])
    elif c == "mux":
        video, audio, out = f
        if a.mode == "replace":
            ff("-i", video, "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", out)
        else:  # mix: keep original audio quietly underneath the new track
            fc = f"[0:a]volume={a.orig_db}dB[o];[o][1:a]amix=inputs=2:normalize=0:duration=longest[m]"
            ff("-i", video, "-i", audio, "-filter_complex", fc, "-map", "0:v:0", "-map", "[m]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out)
    elif c == "beatcut":
        bm = json.load(open(a.beatmap)); beats = bm["beats"]
        step = max(1, int(round(a.every)))
        segs = [(beats[i], beats[i + step]) for i in range(0, len(beats) - step, step)]
        tmp = tempfile.mkdtemp(); parts = []
        for i, (s, e) in enumerate(segs):
            p = os.path.join(tmp, f"s{i:04d}.wav"); ff("-ss", s, "-to", e, "-i", f[0], "-af", "afade=t=in:d=0.004,afade=t=out:st=%f:d=0.004" % max(e - s - 0.004, 0), p); parts.append(p)
        args = []
        for p in parts: args += ["-i", p]
        ff(*args, "-filter_complex", f"concat=n={len(parts)}:v=0:a=1[o]", "-map", "[o]", f[1])
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        ap.error("unknown command " + c)
    print("ok ->", a.out or (f[-1] if f else ""))


if __name__ == "__main__":
    main()

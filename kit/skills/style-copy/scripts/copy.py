#!/usr/bin/env python3
"""copy.py - one entry point for style copying (audio genre, video editing style, animation style). Works with any model: it only needs a shell.

  copy.py doctor                         which skills are installed and ready
  copy.py list                           prebuilt styles (library) and your own installed styles
  copy.py show NAME                      print a style's brief (library or ./styles)
  copy.py study REF [REF2 ...] [--name N]  measure reference(s). One audio file -> ./styles/N/ ; SEVERAL audio files -> each studied, then BLENDED into a family
                                         (shared habits + ranges) in ./styles/N/  - one reference teaches a sound, several teach a style
  copy.py blend STYLE_DIR... --name N    blend already-studied audio styles into a family
  copy.py deep REF                       hard points (impacts, cuts, risers, drops + anatomy), sections, layers, loop-readiness, bar map, labels for Audacity
  copy.py lyrics REF [--words W|--text T]  lyric statistics against the bars/drops (Whisper optional; asked first)
  copy.py plan NAME                      turn a studied style into a bar-by-bar build plan (sections, hard points, layers) to follow while composing
  copy.py install NAME                   make a studied/library style usable: audio genre -> ~/.config/audio-forge/genres/, video preset -> ~/.config/cinematic-edit/styles/
  copy.py compare CANDIDATE REF_DNA      numbers: how close is your build to the reference (audio file or video file vs dna.json)
  copy.py adapt REF --out CANDIDATE      compose -> compare -> adjust (up to 5 rounds) towards a reference (audio-forge)
  copy.py audition [--out DIR]           timestamped instrument showcase + a mini-mix (audio-forge)
  copy.py stem-mix STEMS_DIR --out WAV   mix a folder of stems into a finished mix (audio-forge)
  copy.py loop-doctor FILE [--repair OUT] diagnose and repair a music loop (audio-forge)

Only measurements of STYLE are stored. Never the reference's notes, melody, lyrics, footage, characters, text or logos.
"""
import argparse, glob, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.path.join(os.path.dirname(HERE), "library")
SEARCH = ["./.opencode/skills", "./.claude/skills", "~/.config/opencode/skills", "~/.claude/skills", "~/.agents/skills", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))]   # last = the kit's own skills/ folder, so it also works straight from an unzipped kit
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".aiff", ".aif", ".wma", ".mp2", ".mpga")


def is_audio(path):
    """by extension, else by asking ffprobe: no video stream + an audio stream = audio (so odd names like .mpeg that hold mp3 work)"""
    if path.lower().endswith(AUDIO_EXT): return True
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", path], capture_output=True, text=True, timeout=30)
        kinds = set(r.stdout.split()); return "audio" in kinds and "video" not in kinds
    except Exception:
        return False


def as_audio(path, workdir):
    """give odd extensions a proper one (a copy) so every downstream tool treats them as audio"""
    if path.lower().endswith(AUDIO_EXT): return path
    os.makedirs(workdir, exist_ok=True); dst = os.path.join(workdir, os.path.splitext(os.path.basename(path))[0] + ".mp3"); shutil.copy(path, dst); return dst


def find(name, marker):
    for s in SEARCH:
        d = os.path.join(os.path.expanduser(s), name)
        if os.path.isfile(os.path.join(d, "SKILL.md")) and os.path.isfile(os.path.join(d, marker)): return os.path.abspath(d)


def video_python():
    home = os.environ.get("CE_HOME", os.path.expanduser("~/.cache/cinematic-edit")); v = os.path.join(home, "venv", "bin", "python")
    return v if os.path.exists(v) else sys.executable


def style_dirs():
    out = {}
    for base in (LIB, os.path.join(os.getcwd(), "styles")):
        for d in sorted(glob.glob(os.path.join(base, "*", "dna.json"))): out[os.path.basename(os.path.dirname(d))] = os.path.dirname(d)
    return out


def run(cmd):
    r = subprocess.run(cmd, text=True); return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); ap.add_argument("cmd", choices=["doctor", "list", "show", "study", "install", "compare", "blend", "deep", "lyrics", "plan", "adapt", "audition", "stem-mix", "loop-doctor"]); ap.add_argument("args", nargs="*"); ap.add_argument("--name"); ap.add_argument("--kind", choices=["edit", "animation"]); ap.add_argument("--words"); ap.add_argument("--text"); ap.add_argument("--deep"); ap.add_argument("--bars", type=int, default=64); ap.add_argument("--bpm", type=float)
    a = ap.parse_args(); af = find("audio-forge", "scripts/af.py"); ce = find("cinematic-edit", "scripts/study_video.py")
    if a.cmd == "doctor":
        print(json.dumps(dict(audio_forge=af, cinematic_edit=ce, library=sorted(os.listdir(LIB)), note="audio styles need audio-forge; video/animation styles need cinematic-edit (python with opencv: " + video_python() + ")"), indent=1)); return 0 if (af or ce) else 1
    if a.cmd == "list":
        print("PREBUILT:"); [print(f"  {n:28s} {json.load(open(os.path.join(d, 'dna.json'))).get('kind')}") for n, d in style_dirs().items() if d.startswith(LIB)]
        mine = [n for n, d in style_dirs().items() if not d.startswith(LIB)]; print("YOURS (./styles):", ", ".join(mine) or "none"); return 0
    if a.cmd == "show":
        d = style_dirs().get(a.args[0]) if a.args else None
        if not d: sys.exit("no such style; try: copy.py list")
        print(open(os.path.join(d, "brief.md")).read()); return 0
    AF = lambda *x: [sys.executable, os.path.join(af, "scripts", "af.py")] + list(x)
    if a.cmd in ("blend", "deep", "lyrics", "plan", "adapt", "audition", "stem-mix", "loop-doctor") and not af: sys.exit("this needs the audio-forge skill (not found). Install the kit: python3 install.py")
    if a.cmd == "adapt":
        if len(a.args) < 2: sys.exit("copy.py adapt REFERENCE --out CANDIDATE [--genre G] [--rounds N]")
        return run(AF("adapt", *( [as_audio(a.args[0], os.path.join("styles", ".audio"))] if not a.args[0].endswith(".json") else [a.args[0]] ), *a.args[1:]))
    if a.cmd == "audition":
        return run(AF("audition", *a.args))
    if a.cmd == "stem-mix":
        return run(AF("stem_mix", *a.args))
    if a.cmd == "loop-doctor":
        return run(AF("loop_doctor", *a.args))
    if a.cmd == "blend":
        if len(a.args) < 2 or not a.name: sys.exit("copy.py blend STYLE_DIR STYLE_DIR ... --name NAME")
        return run(AF("blend", *a.args, "--name", a.name, "--out", os.path.join("styles", a.name)))
    if a.cmd == "deep":
        if not a.args: sys.exit("give an audio file"); 
        ref = as_audio(a.args[0], os.path.join("styles", ".audio")); name = a.name or os.path.splitext(os.path.basename(a.args[0]))[0]
        return run(AF("deep", ref, "--name", name, "--out", os.path.join("deep", "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name).strip("-").lower())))
    if a.cmd == "lyrics":
        extra = (["--words", a.words] if a.words else []) + (["--text", a.text] if a.text else []) + (["--deep", a.deep] if a.deep else []) + (["--name", a.name] if a.name else [])
        return run(AF("lyrics", *( [as_audio(a.args[0], os.path.join("styles", ".audio"))] if a.args else []), *extra))
    if a.cmd == "plan":
        d = style_dirs().get(a.args[0]) if a.args else None
        if not d: sys.exit("no such style; try: copy.py list")
        return run([sys.executable, os.path.join(HERE, "plan.py"), d, "--bars", str(a.bars)] + (["--bpm", str(a.bpm)] if a.bpm else []))
    if a.cmd == "study":
        refs = a.args or sys.exit("give the reference file(s)"); name = a.name or os.path.splitext(os.path.basename(refs[0]))[0]; name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in name).strip("-").lower(); out = os.path.join("styles", name)
        if all(is_audio(r) for r in refs):
            if not af: sys.exit("audio styles need the audio-forge skill (not found). Install the kit: python3 install.py")
            work = os.path.join("styles", ".audio")
            if len(refs) == 1: return run(AF("study", as_audio(refs[0], work), "--name", name, "--out", out))
            members = []
            for r in refs:
                rn = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in os.path.splitext(os.path.basename(r))[0]).strip("-").lower(); mo = os.path.join("styles", name + "-members", rn)
                print(f"== studying {rn}", flush=True)
                if run(AF("study", as_audio(r, work), "--name", rn, "--out", mo)) != 0: print(f"   (skipped {rn}: study failed)"); continue
                members.append(mo)
            if len(members) < 2: sys.exit("need at least two studied tracks to blend")
            return run(AF("blend", *members, "--name", name, "--out", out))
        if len(refs) > 1: sys.exit("several references are blended for audio only; study video/animation references one at a time")
        ref = refs[0]
        if not ce: sys.exit("video styles need the cinematic-edit skill (not found). Install the kit: python3 install.py")
        return run([video_python(), os.path.join(ce, "scripts", "study_video.py"), ref, "--name", name, "--out", out] + (["--kind", a.kind] if a.kind else []))
    if a.cmd == "install":
        d = style_dirs().get(a.args[0]) if a.args else None
        if not d: sys.exit("no such style; try: copy.py list"); 
        name = os.path.basename(d); did = []
        g = os.path.join(d, "genre.json")
        if os.path.exists(g):
            j = json.load(open(g)); j["name"] = j.get("name") or name.replace("-", "_"); j.setdefault("aliases", []).append(name); dst = os.path.expanduser("~/.config/audio-forge/genres"); os.makedirs(dst, exist_ok=True)
            json.dump(j, open(os.path.join(dst, j["name"] + ".json"), "w"), indent=1); did.append(f"audio genre '{j['name']}' -> {dst}  (use: af.py compose --genre {j['name']})")
        p = os.path.join(d, "preset.json")
        if os.path.exists(p):
            dst = os.path.expanduser("~/.config/cinematic-edit/styles"); os.makedirs(dst, exist_ok=True); shutil.copy(p, os.path.join(dst, name + ".json")); did.append(f"video style '{name}' -> {dst}  (use: analyze.py video.mp4 --style {name})")
        print("\n".join(did) or "nothing to install (this style has no genre.json or preset.json)"); return 0
    if a.cmd == "compare":
        if len(a.args) < 2: sys.exit("copy.py compare CANDIDATE REFERENCE_DNA.json")
        kind = json.load(open(a.args[1])).get("kind")
        if kind == "audio":
            if not af: sys.exit("audio-forge not found")
            return run([sys.executable, os.path.join(af, "scripts", "af.py"), "compare", a.args[0], a.args[1]])
        if not ce: sys.exit("cinematic-edit not found")
        return run([video_python(), os.path.join(ce, "scripts", "study_video.py"), "--compare", a.args[0], a.args[1]])


if __name__ == "__main__":
    sys.exit(main())

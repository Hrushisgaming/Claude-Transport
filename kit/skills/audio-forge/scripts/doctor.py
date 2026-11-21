#!/usr/bin/env python3
"""doctor.py -- check the machine, install the tiny core, and install OPTIONAL parts only when asked.

  python3 doctor.py                         status of every part (nothing is installed)
  python3 doctor.py --install core          numpy + scipy into a private venv (~60 MB). Required. Safe to run without asking.
  python3 doctor.py --list-optional --json  optional parts with size, description and the exact question to ask the user
  python3 doctor.py --install kokoro        one optional part (ids: kokoro piper espeak librosa demucs whisper)
  python3 doctor.py --install whisper --whisper-model base
  python3 doctor.py --capabilities          JSON a host skill (e.g. a video editor) reads to detect audio-forge + what is installed
  python3 doctor.py --selftest              synthesis + analysis + tts + bridge smoke tests

Everything is free and local: no accounts, no API keys. Files go to ~/.cache/audio-forge (override: AUDIO_FORGE_HOME).
The agent MUST ask the user before installing any optional part (the parts list carries the wording).
"""
import argparse, json, os, platform, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser(os.environ.get("AUDIO_FORGE_HOME", "~/.cache/audio-forge"))
VENV = os.path.join(HOME, "venv")
WIN = platform.system() == "Windows"
MAC = platform.system() == "Darwin"


def vpy():
    p = os.path.join(VENV, "Scripts", "python.exe") if WIN else os.path.join(VENV, "bin", "python")
    return p if os.path.exists(p) else None


def has_mod(mod, py=None):
    py = py or vpy() or sys.executable
    return subprocess.run([py, "-c", f"import {mod}"], capture_output=True).returncode == 0


def sh(cmd, **kw):
    print("  $", " ".join(cmd), flush=True)
    return subprocess.run(cmd, **kw).returncode == 0


def ensure_venv():
    if vpy():
        return True
    os.makedirs(HOME, exist_ok=True)
    if not sh([sys.executable, "-m", "venv", VENV]):
        print("  venv creation failed. On Debian/Ubuntu: sudo apt install python3-venv   (then re-run)")
        return False
    sh([vpy(), "-m", "pip", "install", "-q", "--upgrade", "pip"])
    return True


def pip(*pkgs, extra=()):
    return sh([vpy(), "-m", "pip", "install", "-q", *extra, *pkgs])


def run_py(code):
    return subprocess.run([vpy(), "-c", code], cwd=HERE, env=dict(os.environ, AUDIO_FORGE_HOME=HOME)).returncode == 0


def sysinstall_hint(pkg_apt, pkg_brew, pkg_winget):
    if MAC and shutil.which("brew"):
        return ["brew", "install", pkg_brew]
    if WIN and shutil.which("winget"):
        return ["winget", "install", "--id", pkg_winget, "-e"]
    if shutil.which("apt-get"):
        return ["sudo", "apt-get", "install", "-y", pkg_apt]
    return None


# ── parts ───────────────────────────────────────────────────────────────────
def i_core():
    return ensure_venv() and pip("numpy", "scipy")


def i_kokoro():
    return ensure_venv() and pip("kokoro-onnx") and run_py("import tts; tts.download(tts.KOKORO_URLS[0], tts.VOICES+'/kokoro-v1.0.onnx'); tts.download(tts.KOKORO_URLS[1], tts.VOICES+'/voices-v1.0.bin')")


def i_piper():
    return ensure_venv() and pip("piper-tts") and run_py("import tts; tts.piper_voice_files(tts.PIPER_DEFAULT)")


def i_espeak():
    cmd = sysinstall_hint("espeak-ng", "espeak-ng", "eSpeak-NG.eSpeak-NG")
    if not cmd:
        print("  install espeak-ng with your package manager"); return False
    if cmd[0] == "sudo":
        print("  This needs administrator rights. Run it yourself (the agent must not type your password):\n    " + " ".join(cmd))
        return False
    return sh(cmd)


def i_librosa():
    return ensure_venv() and pip("librosa")


def i_demucs():
    if not ensure_venv():
        return False
    extra = ["--index-url", "https://download.pytorch.org/whl/cpu", "--extra-index-url", "https://pypi.org/simple"] if not MAC else []
    ok = pip("torch", "torchaudio", extra=extra) or pip("torch", "torchaudio")
    return ok and pip("demucs", "soundfile") and run_py("from demucs.pretrained import get_model; get_model('htdemucs'); print('model cached')")


def i_whisper(model="small"):
    return ensure_venv() and pip("faster-whisper") and run_py(f"from faster_whisper import WhisperModel; WhisperModel('{model}', device='cpu', compute_type='int8'); print('model cached')")


PARTS = [
    dict(id="kokoro", name="the natural voice pack (Kokoro)", size="about 400 MB", fn=i_kokoro,
         desc="reads text or subtitles aloud in a natural human-sounding voice, 13+ voices, English/British and more",
         check=lambda: has_mod("kokoro_onnx") and os.path.exists(os.path.join(HOME, "voices", "kokoro-v1.0.onnx"))),
    dict(id="piper", name="the compact voice pack (Piper)", size="about 100 MB", fn=i_piper,
         desc="reads text aloud in a good-quality voice with many languages; smaller and faster than the natural pack",
         check=lambda: has_mod("piper")),
    dict(id="espeak", name="the tiny robotic voice (eSpeak NG)", size="about 5 MB", fn=i_espeak,
         desc="a very small robotic voice that speaks 100+ languages; needs your system package manager (may ask for your password)",
         check=lambda: shutil.which("espeak-ng") is not None or shutil.which("espeak") is not None),
    dict(id="librosa", name="the extra analysis toolkit (librosa)", size="about 250 MB", fn=i_librosa,
         desc="a second opinion on tempo and beats when analysing your reference audio (built-in analysis already works without it)",
         check=lambda: has_mod("librosa")),
    dict(id="demucs", name="the stem splitter (Demucs)", size="about 1 GB", fn=i_demucs,
         desc="splits a song into drums, bass, vocals and other so the drum pattern, bassline and melody can be measured cleanly; also lets you remix or mute a part",
         check=lambda: has_mod("demucs")),
    dict(id="whisper", name="the speech-to-text engine (Whisper)", size="about 500 MB (small model)", fn=i_whisper,
         desc="makes subtitles and word timings from a video's speech, for when you have no subtitle file but want a voice-over or dub",
         check=lambda: has_mod("faster_whisper")),
]


def status():
    out = {}
    out["python"] = sys.version.split()[0]
    out["ffmpeg"] = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    out["venv"] = bool(vpy())
    out["core"] = has_mod("numpy") and has_mod("scipy")
    for p in PARTS:
        out[p["id"]] = bool(p["check"]())
    return out


def ffmpeg_help():
    if MAC:
        return "brew install ffmpeg"
    if WIN:
        return "winget install Gyan.FFmpeg   (then open a new terminal)"
    return "sudo apt install ffmpeg   (or your distro's package manager)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--install"); ap.add_argument("--list-optional", action="store_true"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--capabilities", action="store_true", help="machine-readable JSON for a host skill (video editor) to detect audio-forge")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--whisper-model", default="small")
    a = ap.parse_args()

    if a.capabilities:
        st = status()
        styles = []
        try:
            sys.path.insert(0, HERE)
            from forge import styles as _S
            styles = sorted(_S.STYLES)
        except Exception:
            pass
        genres, tools = [], ("compose analyze remake tts subs2speech audio_edit bridge sfx separate listen selftest score hear "
                             "study compare deep lyrics blend ost survey aicheck at adapt audition stem_mix loop_doctor doctor").split()
        try:
            sys.path.insert(0, HERE)
            from forge import genres as G
            genres = sorted(G.GENRES)
        except Exception:
            pass
        ver = open(os.path.join(HERE, "..", "VERSION")).read().strip() if os.path.exists(os.path.join(HERE, "..", "VERSION")) else "unknown"
        print(json.dumps(dict(
            name="audio-forge", version=ver, entry=os.path.join(HERE, "af.py"), skill_dir=os.path.abspath(os.path.join(HERE, "..")),
            ready=bool(st["core"] and st["ffmpeg"]), core_installed=st["core"], ffmpeg=st["ffmpeg"],
            schemas=dict(beatmap="audio-forge/beatmap@1", profile="audio-forge/profile@1", scorebrief="audio-forge/scorebrief@1", score="audio-forge/score@1"),
            styles=styles,
            provides=["music", "tts", "subtitle_dub", "sfx", "audio_edit", "reference_analysis", "beat_sync", "midi", "stems_export", "video_score", "voice_cleanup",
                      "offline_feedback", "adaptive_composition", "instrument_audition", "stem_mixing", "loop_repair"],
            tools=tools, genres=genres,
            optional={p["id"]: dict(installed=bool(st[p["id"]]), size=p["size"], name=p["name"]) for p in PARTS},
            voice_engines_ready=[k for k in ("kokoro", "piper", "espeak") if st.get(k)] + ["formant (placeholder)"],
            ask_before=["any optional part", "subtitle-to-speech (confirm dub/voice-over/track)", "applying bridge output to the host's files"],
        ), indent=1))
        return 0 if (st["core"] and st["ffmpeg"]) else 1
    if a.list_optional:
        st = status()
        rows = [dict(id=p["id"], name=p["name"], size=p["size"], description=p["desc"], installed=st[p["id"]],
                     question=f"Do you want {p['name']}? It {p['desc']}. One-time download, {p['size']}.") for p in PARTS]
        print(json.dumps(rows, indent=1) if a.json else "\n".join(f"{r['id']:8s} {'[installed]' if r['installed'] else '[not installed]':15s} {r['size']:26s} {r['name']}" for r in rows))
        return 0
    if a.install:
        if a.install == "core":
            ok = i_core()
        else:
            part = next((p for p in PARTS if p["id"] == a.install), None)
            if not part:
                print("unknown part; choices: core " + " ".join(p["id"] for p in PARTS)); return 2
            if not (has_mod("numpy") and has_mod("scipy")) and not i_core():
                return 1
            ok = i_whisper(a.whisper_model) if a.install == "whisper" else part["fn"]()
        print("OK" if ok else "FAILED", a.install)
        return 0 if ok else 1
    if a.selftest:
        return subprocess.call([vpy() or sys.executable, os.path.join(HERE, "selftest.py")])

    st = status()
    print(f"python {st['python']}  |  ffmpeg: {'ok' if st['ffmpeg'] else 'MISSING -> ' + ffmpeg_help()}  |  private env: {'yes' if st['venv'] else 'no'}")
    print(f"core engine (numpy+scipy): {'ok' if st['core'] else 'MISSING -> python3 doctor.py --install core  (about 60 MB, required)'}")
    print("optional parts (never installed without asking the user):")
    for p in PARTS:
        print(f"  {p['id']:8s} {'installed' if st[p['id']] else 'not installed':14s} {p['size']:26s} {p['name']}")
    if st["core"] and st["ffmpeg"]:
        print("\nAll set for composing, analysing, editing and the built-in placeholder voice. Add a voice pack for real speech.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

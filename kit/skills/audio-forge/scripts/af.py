#!/usr/bin/env python3
"""af.py -- single entry point. Always runs a tool with the right Python (private venv if doctor.py made one).

  python3 af.py doctor [--list-optional --json | --install ID | --selftest]
  python3 af.py compose --genre house --out song.wav
  python3 af.py analyze ref.mp3 --out profile.json
  python3 af.py tts --text "hello" --out hello.wav
  tools: compose analyze remake tts subs2speech audio_edit bridge sfx separate listen selftest score hear
         study compare deep lyrics blend ost survey aicheck at adapt audition stem_mix loop_doctor hopefight ostfight huntfight feedback instrument_showcase instrument_demo doctor

Works the same in opencode, Claude Code, macOS, Linux, WSL and native Windows (no bash needed).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser(os.environ.get("AUDIO_FORGE_HOME", "~/.cache/audio-forge"))
TOOLS = ("compose analyze remake tts subs2speech audio_edit bridge sfx separate listen selftest score hear "
         "study compare deep lyrics blend ost survey aicheck at adapt audition stem_mix loop_doctor hopefight ostfight huntfight feedback instrument_showcase instrument_demo doctor").split()


def venv_python():
    for rel in ("venv/bin/python", "venv/Scripts/python.exe"):
        p = os.path.join(HOME, rel)
        if os.path.exists(p):
            return p
    return None


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__); return 0
    tool = sys.argv[1].replace("-", "_")
    if tool not in TOOLS:
        print("unknown tool:", sys.argv[1], "\nchoices:", " ".join(TOOLS)); return 2
    py = sys.executable if tool == "doctor" else (venv_python() or sys.executable)
    env = dict(os.environ, AUDIO_FORGE_HOME=HOME, PYTHONUNBUFFERED="1")
    return subprocess.call([py, os.path.join(HERE, tool + ".py")] + sys.argv[2:], env=env)


if __name__ == "__main__":
    sys.exit(main())

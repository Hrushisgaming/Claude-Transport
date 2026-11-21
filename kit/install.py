#!/usr/bin/env python3
"""Install the video studio kit (cinematic-edit, audio-forge, style-copy, roblox-ost, video-studio + companions) for opencode and/or Claude Code (copies the skill folders and the slash commands; changes nothing else).

  python3 install.py                 # opencode (~/.config/opencode/skills) AND Claude Code (~/.claude/skills)
  python3 install.py --opencode      # only opencode
  python3 install.py --claude        # only Claude Code
  python3 install.py --project       # into ./.opencode/skills and ./.claude/skills for this project only

An existing install is moved to ../video-studio-backups/<name>.YYYYMMDD first (outside the skills folder, so it is never loaded twice). Then run:  python3 <skills>/audio-forge/scripts/af.py doctor
"""
import argparse, datetime, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "skills")
ap = argparse.ArgumentParser()
ap.add_argument("--opencode", action="store_true"); ap.add_argument("--claude", action="store_true"); ap.add_argument("--project", action="store_true")
a = ap.parse_args()
home = os.path.expanduser("~")
targets = []
if a.project:
    targets = [os.path.join(os.getcwd(), ".opencode", "skills"), os.path.join(os.getcwd(), ".claude", "skills")]
    if a.opencode and not a.claude: targets = targets[:1]
    if a.claude and not a.opencode: targets = targets[1:]
else:
    if a.opencode or not a.claude: targets.append(os.path.join(home, ".config", "opencode", "skills"))
    if a.claude or not a.opencode: targets.append(os.path.join(home, ".claude", "skills"))
today = datetime.date.today().strftime("%Y%m%d")
for t in targets:
    backups = os.path.join(os.path.dirname(t), "video-studio-backups")  # OUTSIDE the skills folder: a backup SKILL.md there would register as a duplicate skill
    os.makedirs(t, exist_ok=True)
    for name in sorted(os.listdir(SRC)):
        dst = os.path.join(t, name)
        if os.path.exists(dst):
            os.makedirs(backups, exist_ok=True)
            bk = os.path.join(backups, f"{name}.{today}")
            n = 1
            while os.path.exists(bk):
                n += 1; bk = os.path.join(backups, f"{name}.{today}-{n}")
            shutil.move(dst, bk)
            print("  backed up old", name, "->", bk)
        shutil.copytree(os.path.join(SRC, name), dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for root, _, files in os.walk(dst):
            for f in files:
                if f.endswith((".py", ".sh")):
                    os.chmod(os.path.join(root, f), 0o755)
    print("installed into", t, ":", ", ".join(sorted(os.listdir(SRC))))
# slash commands for BOTH agents (opencode: commands/ and command/ both documented; Claude Code: commands/). Never overwrite a different file silently: keep a .bak.
cmd_src = os.path.join(HERE, "commands"); installed_cmds = []
def put_commands(base_dirs):
    for d in base_dirs:
        os.makedirs(d, exist_ok=True)
        for f in sorted(os.listdir(cmd_src)):
            dst = os.path.join(d, f)
            if os.path.exists(dst) and open(dst, encoding="utf-8").read() != open(os.path.join(cmd_src, f), encoding="utf-8").read(): shutil.copy(dst, dst + ".bak")
            shutil.copy(os.path.join(cmd_src, f), dst)
if os.path.isdir(cmd_src):
    names = ["/" + os.path.splitext(f)[0] for f in sorted(os.listdir(cmd_src))]
    if a.project:
        if any(".opencode" in t for t in targets): put_commands([os.path.join(os.getcwd(), ".opencode", "commands"), os.path.join(os.getcwd(), ".opencode", "command")]); installed_cmds.append("opencode (project)")
        if any(".claude" in t for t in targets): put_commands([os.path.join(os.getcwd(), ".claude", "commands")]); installed_cmds.append("Claude Code (project)")
    else:
        if any("opencode" in t for t in targets): put_commands([os.path.join(home, ".config", "opencode", "commands"), os.path.join(home, ".config", "opencode", "command")]); installed_cmds.append("opencode")
        if any(os.sep + ".claude" + os.sep in t + os.sep for t in targets): put_commands([os.path.join(home, ".claude", "commands")]); installed_cmds.append("Claude Code")
    if installed_cmds: print("slash commands installed for", " and ".join(installed_cmds) + ":", "  ".join(names), "  (restart the app)")
af = os.path.join(targets[0], "audio-forge", "scripts", "af.py")
ce = os.path.join(targets[0], "cinematic-edit", "scripts", "doctor.sh")
print("\nNext:")
print(f'  bash "{ce}"          (picture engine; re-run until it says All set)')
print(f'  python3 "{af}" doctor   (audio engine, optional)')
print("Then start a NEW opencode / Claude Code session so the skills load. cinematic-edit replaces editor-v1 (see README.md).")

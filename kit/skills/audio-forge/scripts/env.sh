# source this (bash/zsh) to get $AF_PY and $AF; af.py does the same job on every platform without sourcing.
AF_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
export AUDIO_FORGE_HOME="${AUDIO_FORGE_HOME:-$HOME/.cache/audio-forge}"
if   [ -x "$AUDIO_FORGE_HOME/venv/bin/python" ];        then AF_PY="$AUDIO_FORGE_HOME/venv/bin/python"
elif [ -x "$AUDIO_FORGE_HOME/venv/Scripts/python.exe" ]; then AF_PY="$AUDIO_FORGE_HOME/venv/Scripts/python.exe"
else AF_PY="$(command -v python3 || command -v python)"; fi
export AF_PY AF_SCRIPTS
AF() { "$AF_PY" "$AF_SCRIPTS/af.py" "$@"; }

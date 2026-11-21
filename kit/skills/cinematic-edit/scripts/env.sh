#!/usr/bin/env bash
# env.sh - source at the top of every step:  source <skill>/scripts/env.sh
# Puts common install dirs on PATH (non-interactive shells skip your profile) and sets $CE_PY.
_ce_add(){ case ":$PATH:" in *":$1:"*) ;; *) [ -d "$1" ] && PATH="$1:$PATH";; esac; return 0; }
_ce_add /usr/local/bin; _ce_add /opt/homebrew/bin; _ce_add "$HOME/.local/bin"
export PATH
export CE_HOME="${CE_HOME:-$HOME/.cache/cinematic-edit}"
if [ -x "$CE_HOME/venv/bin/python" ]; then CE_PY="$CE_HOME/venv/bin/python"; else CE_PY="$(command -v python3)"; fi
export CE_PY
true

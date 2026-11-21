#!/usr/bin/env bash
# ce.sh - one-shot helper:  ce.sh <video> [music] [format]   -> work/ plan.json draft + half-size preview in ./out
set -euo pipefail
SK="$(cd "$(dirname "$0")/.." && pwd)"; source "$SK/scripts/env.sh"
V="${1:?usage: ce.sh <video> [music] [format]}"; M="${2:-}"; F="${3:-9:16}"
"$CE_PY" "$SK/scripts/analyze.py" "$V" --out work --plan plan.json --format "$F" ${M:+--music "$M"}
"$CE_PY" "$SK/scripts/render.py" plan.json out --preview
echo "edit plan.json (events, acts, overlays), re-run render.py, then render without --preview for the final."

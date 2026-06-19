#!/usr/bin/env bash
# run.sh — start ComfyUI
# Usage: bash run.sh [--lowvram] [--cpu]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFY_DIR="$SCRIPT_DIR/ComfyUI"

if [ ! -d "$COMFY_DIR" ]; then
    echo "ComfyUI not found. Run setup.sh first."
    exit 1
fi

source "$COMFY_DIR/.venv/bin/activate"

# Pass any extra flags straight through (e.g. --lowvram, --cpu, --port 8189)
echo "==> Starting ComfyUI at http://127.0.0.1:8188"
echo "    Extra flags: $*"
echo "    Output images save to: ComfyUI/output/"
echo "    Stop with Ctrl+C"
echo ""

python "$COMFY_DIR/main.py" \
    --output-directory "$SCRIPT_DIR/output" \
    "$@"

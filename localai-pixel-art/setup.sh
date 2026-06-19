#!/usr/bin/env bash
# setup.sh — clone ComfyUI and install dependencies
# Run once from this directory: bash setup.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMFY_DIR="$SCRIPT_DIR/ComfyUI"

echo "==> Setting up ComfyUI in $COMFY_DIR"

# --- Clone ComfyUI ---
if [ -d "$COMFY_DIR" ]; then
    echo "    ComfyUI already exists, pulling latest..."
    git -C "$COMFY_DIR" pull
else
    git clone https://github.com/comfyanonymous/ComfyUI "$COMFY_DIR"
fi

# --- Python venv ---
if [ ! -d "$COMFY_DIR/.venv" ]; then
    echo "==> Creating venv..."
    python3 -m venv "$COMFY_DIR/.venv"
fi

source "$COMFY_DIR/.venv/bin/activate"

echo "==> Installing ComfyUI dependencies..."
pip install --upgrade pip
pip install -r "$COMFY_DIR/requirements.txt"

# --- Quantize script deps ---
echo "==> Installing quantize_sprite.py dependencies..."
pip install Pillow numpy

echo ""
echo "==> Done. Directory layout:"
echo "    ComfyUI/models/checkpoints/  — place SD 1.5 / SDXL .safetensors here"
echo "    ComfyUI/models/loras/        — place pixel art LoRA .safetensors here"
echo "    ComfyUI/models/unet/         — place FLUX unet here (if using FLUX)"
echo ""
echo "See LOCAL-AI-FOR-PIXEL-ART.md for model download links and LoRA recommendations."
echo "Then run: bash run.sh"

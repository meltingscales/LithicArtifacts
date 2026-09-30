#!/usr/bin/env python3
"""
quantize_sprite.py — downscale an AI-generated PNG to target size and
snap every pixel to the nearest Pyxel 16-color palette entry.

Usage:
    python quantize_sprite.py input.png output.png [--size 8x8]
    python quantize_sprite.py input.png output.png --size 16x8
    python quantize_sprite.py output/ComfyUI_00001_.png ../assets/img/crawler.png --size 8x8

Batch (all PNGs in a directory → assets/img/):
    for f in output/*.png; do
        python quantize_sprite.py "$f" "../assets/img/$(basename $f)" --size 8x8
    done
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("Missing deps. Run: pip install Pillow numpy")
    sys.exit(1)

# fmt: off
# PICO-8 16-color palette (Pyxel palette is set to this in main.py) (RGB)
PYXEL_PALETTE = [
    (  0,   0,   0),  #  0 black
    ( 29,  43,  83),  #  1 dark blue
    (126,  37,  83),  #  2 dark purple
    (  0, 135,  81),  #  3 dark green
    (171,  82,  54),  #  4 brown
    ( 95,  87,  79),  #  5 dark gray
    (194, 195, 199),  #  6 light gray
    (255, 241, 232),  #  7 white
    (255,   0,  77),  #  8 red
    (255, 163,   0),  #  9 orange
    (255, 236,  39),  # 10 yellow
    (  0, 228,  54),  # 11 green
    ( 41, 173, 255),  # 12 blue
    (131, 118, 156),  # 13 indigo
    (255, 119, 168),  # 14 pink
    (255, 204, 170),  # 15 peach
]
# fmt: on

_PAL_ARRAY = np.array(PYXEL_PALETTE, dtype=np.int32)  # (16, 3)


def quantize(img: "Image.Image", target_w: int, target_h: int) -> "Image.Image":
    # Nearest-neighbor downscale — preserves hard pixel edges
    img = img.convert("RGB").resize((target_w, target_h), Image.NEAREST)
    arr = np.array(img, dtype=np.int32)  # (H, W, 3)
    flat = arr.reshape(-1, 3)  # (N, 3)
    # Squared Euclidean distance to each palette entry
    diffs = flat[:, None, :] - _PAL_ARRAY[None, :, :]  # (N, 16, 3)
    dists = (diffs**2).sum(axis=2)  # (N, 16)
    nearest = dists.argmin(axis=1)  # (N,)
    quantized = _PAL_ARRAY[nearest].reshape(target_h, target_w, 3)
    return Image.fromarray(quantized.astype(np.uint8), "RGB")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=Path, help="Source PNG (AI-generated)")
    parser.add_argument("output", type=Path, help="Destination PNG")
    parser.add_argument(
        "--size",
        default="8x8",
        help="Target WxH in pixels (default: 8x8). Examples: 8x8, 16x8, 8x16",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input not found: {args.input}")
        sys.exit(1)

    try:
        w, h = (int(v) for v in args.size.lower().split("x"))
    except ValueError:
        print(f"Bad --size format '{args.size}'. Use WxH, e.g. 8x8 or 16x8.")
        sys.exit(1)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(args.input)
    result = quantize(img, w, h)
    result.save(args.output)
    print(f"{args.input.name} -> {args.output}  ({w}x{h}, Pyxel palette)")


if __name__ == "__main__":
    main()

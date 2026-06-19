# Local AI for Pixel Art Sprites

Guide to generating 8×8 and 16×8 sprites locally for Lithic Artifacts using
ComfyUI + a pixel art LoRA, then quantizing to the Pyxel 16-color palette.

---

## Why not vanilla Stable Diffusion?

Base SD/SDXL doesn't understand "8×8 pixel art". It understands pixel art as a
style, but generates at high resolution with anti-aliased edges. To get clean
sprite-sheet output you need:

1. A pixel-art-specific LoRA or checkpoint to lock in the aesthetic
2. Generate at 8× (64×64 or 128×64) — models can't generate at 8 pixels
3. Downscale with **nearest-neighbor** (no bicubic/bilinear blur)
4. Palette-quantize to Pyxel's 16 colors

---

## Recommended stack

| Component | Choice | Notes |
|---|---|---|
| UI | ComfyUI | Most flexible node graph; good for batch |
| Base model | FLUX.1-dev or SD 1.5 | FLUX: better quality, needs 12GB VRAM; SD 1.5: runs on 4–6GB |
| LoRA | Pixel Art XL / pixelspritesheet-lora | Search Civitai; add to `models/loras/` |
| Quantize | `localai-pixel-art/quantize_sprite.py` (see below) | Snaps to Pyxel palette |

---

## Setup

### 1. Install ComfyUI

```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py
# Opens at http://127.0.0.1:8188
```

### 2. Download a model

For **SD 1.5** (low VRAM):
- Download `v1-5-pruned-emaonly.safetensors` from Hugging Face
- Place in `ComfyUI/models/checkpoints/`

For **FLUX.1-dev** (better results, 12GB+):
- Download from `black-forest-labs/FLUX.1-dev` on Hugging Face
- Place in `ComfyUI/models/unet/`

### 3. Download a pixel art LoRA

Recommended: search Civitai for:
- `pixel art sprite` — filter to SD 1.5 or SDXL
- `pixelspritesheet` — good for game sprite sheets
- `Pixel Art XL` — SDXL/FLUX variant

Place `.safetensors` in `ComfyUI/models/loras/`.

---

## Generation settings

### For 8×8 sprites (generate at 64×64)

```
Prompt:   pixel art, 8x8 sprite, [subject], dark background, Pyxel palette,
          biomechanical, body horror, GBA game sprite, no anti-aliasing,
          limited color palette, <lora:pixel_art:0.8>

Negative: blurry, gradient, photorealistic, smooth, 3D, noise, text,
          watermark, high resolution details, anti-aliasing

Width:    64
Height:   64
Steps:    25–30
CFG:      7.0
Sampler:  DPM++ 2M Karras (SD 1.5) or Euler (FLUX)
```

### For 16×8 sprites (enemies like ShootyFlier)

```
Width:    128
Height:   64
```

Same prompt/settings. Wide format forces horizontal composition.

### Batch tip

Use ComfyUI's "Batch size" node set to 16–32. Most will be garbage — you're
mining for 2–3 usable outputs per batch.

---

## Palette quantization script

After generating, run `localai-pixel-art/quantize_sprite.py` to downscale
and snap to Pyxel's 16 colors. Script source for reference:

```python
#!/usr/bin/env python3
"""
Downscale an AI-generated PNG to 8x8 or 16x8 and quantize to Pyxel's palette.

Usage:
    python localai-pixel-art/quantize_sprite.py input.png output.png [--size 8x8]
    python localai-pixel-art/quantize_sprite.py input.png output.png --size 16x8
"""
import argparse
import sys
from pathlib import Path
from PIL import Image
import numpy as np

# Pyxel default 16-color palette (RGB)
PYXEL_PALETTE = [
    (  0,   0,   0),  #  0 black
    ( 43,  51,  95),  #  1 dark navy
    (126,  32, 114),  #  2 dark purple
    ( 25, 149, 156),  #  3 teal
    (139,  72,  82),  #  4 dark red-brown
    ( 57,  92, 152),  #  5 dark blue-gray
    (169, 193, 255),  #  6 light blue
    (238, 238, 238),  #  7 white
    (212,  24, 108),  #  8 red/pink
    (211, 132,  65),  #  9 orange
    (233, 195,  91),  # 10 yellow
    (112, 198, 169),  # 11 mint green
    (118, 150, 222),  # 12 sky blue
    (163, 163, 163),  # 13 gray
    (255, 151, 152),  # 14 light pink
    (237, 199, 176),  # 15 peach
]


def nearest_palette_color(pixel):
    r, g, b = pixel[:3]
    best, best_dist = 0, float("inf")
    for i, (pr, pg, pb) in enumerate(PYXEL_PALETTE):
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_dist:
            best_dist = d
            best = i
    return PYXEL_PALETTE[best]


def quantize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    # Downscale with nearest-neighbor to preserve hard pixel edges
    img = img.convert("RGB").resize((target_w, target_h), Image.NEAREST)
    arr = np.array(img)
    out = np.zeros_like(arr)
    for y in range(target_h):
        for x in range(target_w):
            out[y, x] = nearest_palette_color(arr[y, x])
    return Image.fromarray(out.astype(np.uint8), "RGB")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--size", default="8x8",
                        help="Target size: 8x8, 16x8, 8x16, etc.")
    args = parser.parse_args()

    w, h = (int(v) for v in args.size.split("x"))
    img = Image.open(args.input)
    result = quantize(img, w, h)
    result.save(args.output)
    print(f"Saved {w}×{h} palette-quantized sprite → {args.output}")


if __name__ == "__main__":
    main()
```

Install deps: `uv add Pillow numpy` (or `pip install Pillow numpy`).

---

## Workflow end-to-end

```
ComfyUI (64×64 batch)
    → save_image node → assets/candidates/ai/
    → python localai-pixel-art/quantize_sprite.py candidate_01.png assets/img/sprite.png --size 8x8
    → inspect result in any image viewer (1px = 1px, zoom 8× in viewer)
    → if good: add pyxel.images[0].load(x, y, "assets/img/sprite.png") in main.py
```

---

## Prompt templates for this project

### 8×8 wall tile (Biomechanical Dungeon)

```
pixel art 8x8 tile, biomechanical wall, metal rivets over wet muscle,
bioluminescent cracks, dark purple-gray fill, cold metallic border,
GBA sprite, no anti-aliasing, Pyxel palette, <lora:pixel_art:0.8>
```

### 8×8 enemy (Crawler)

```
pixel art 8x8 sprite, chitinous ground creature, wide flat silhouette,
multi-legged, dark purple body, red eyes, side-view, transparent background,
GBA game sprite, no anti-aliasing, <lora:pixel_art:0.8>
```

### 16×8 enemy (ShootyFlier)

```
pixel art 16x8 sprite, asymmetric flying creature, gun-arm protrusion,
dark teal wings, red weapon accent, side-view, transparent background,
GBA game sprite, <lora:pixel_art:0.8>
```

### 8×16 player (standing)

```
pixel art 8x16 sprite, armored humanoid explorer, yellow armor, orange trim,
helmet, GBA Metroid style, standing pose, transparent background,
no anti-aliasing, <lora:pixel_art:0.8>
```

---

## Tips

- **Black background beats transparency** during generation. Remove it in post
  if needed, or use Pyxel's `colkey=0` (black = transparent on `blt`).
- **More steps ≠ better** for pixel art. 20–25 is usually enough; more adds
  detail that disappears on downscale anyway.
- **LoRA weight 0.6–0.85** is the sweet spot. Above 0.9 it over-pixelates and
  loses coherence.
- **Generate 4–8× the sprite size**, not more. 64×64 → 8×8 is ideal. 512×512
  → 8×8 loses all structure.
- **Iterate on prompts, not seeds.** Lock the seed once you find a composition
  that works, then refine the prompt.
- **Upscale for inspection** using nearest-neighbor (`image-rendering: pixelated`
  in browser, or `magick sprite.png -scale 800% preview.png`).

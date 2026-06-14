"""
Generate 8x8 sprite candidates for Lithic Artifacts.

Two modes (choose with --mode):

  sample   Sample random 8x8 patches from reference art in ../art-direction/,
           snap every pixel to the Pyxel 16-color palette, and save candidates.
           Good for: entity sprites, palette-accurate tiles from reference images.

  noise    Generate 8x8 textures from Perlin/Simplex noise, quantize to palette.
           Good for: wall tiles, floor tiles, organic/biomechanical surfaces.

Usage
-----
  python generate-8x8-datamosh.py --mode sample [--count 64] [--seed 42]
  python generate-8x8-datamosh.py --mode noise  [--count 64] [--seed 42]
                                                 [--scale 4.0] [--octaves 4]
  python generate-8x8-datamosh.py --mode both   [--count 32]  [--seed 42]

Output: ./candidates/img/<NNN>.png  (8x8 RGBA PNGs, scaled 8x for preview)
"""

import argparse
import random
import sys
from pathlib import Path

import noise as noise_lib
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Pyxel default 16-color palette (RGB)
# ---------------------------------------------------------------------------
PYXEL_PALETTE = [
    (0,   0,   0),    # 0  black
    (43,  51,  95),   # 1  dark navy
    (126, 32,  114),  # 2  dark purple
    (25,  149, 156),  # 3  teal
    (139, 72,  82),   # 4  dark rose
    (57,  48,  65),   # 5  dark gray
    (100, 100, 100),  # 6  light gray  (approx)
    (139, 139, 139),  # 7  silver      (approx)
    (255, 0,   77),   # 8  red
    (255, 163, 0),    # 9  orange
    (255, 236, 39),   # 10 yellow
    (0,   228, 54),   # 11 green
    (41,  173, 255),  # 12 light blue
    (131, 118, 156),  # 13 lavender
    (255, 119, 168),  # 14 pink
    (255, 204, 170),  # 15 peach
]

# Build a Pillow palette image for quantization (768 bytes: 256 * RGB, padded)
def _build_palette_image() -> Image.Image:
    pal_flat = []
    for r, g, b in PYXEL_PALETTE:
        pal_flat += [r, g, b]
    # Pad to 256 colors
    pal_flat += [0, 0, 0] * (256 - len(PYXEL_PALETTE))
    pal_img = Image.new("P", (1, 1))
    pal_img.putpalette(pal_flat)
    return pal_img

PAL_IMG = _build_palette_image()


def snap_to_palette(patch: np.ndarray) -> np.ndarray:
    """
    Snap every pixel in an HxWx3 uint8 array to the nearest Pyxel palette color.
    Returns HxWx3 uint8.
    """
    pal = np.array(PYXEL_PALETTE, dtype=np.float32)   # (16, 3)
    flat = patch.reshape(-1, 3).astype(np.float32)     # (N, 3)
    # Squared Euclidean distance to each palette entry
    dists = np.sum((flat[:, None, :] - pal[None, :, :]) ** 2, axis=2)  # (N, 16)
    indices = np.argmin(dists, axis=1)                  # (N,)
    return pal[indices].reshape(patch.shape).astype(np.uint8)


def save_candidate(patch: np.ndarray, path: Path, preview_scale: int = 8):
    """Save an 8x8 patch as a PNG, with an upscaled preview beside it."""
    assert patch.shape == (8, 8, 3), f"Expected (8,8,3), got {patch.shape}"
    img = Image.fromarray(patch, "RGB")
    img.save(path)
    # Also save an upscaled preview so it's easy to eyeball
    preview = img.resize((8 * preview_scale, 8 * preview_scale),
                          resample=Image.NEAREST)
    preview.save(path.with_stem(path.stem + "_preview"))


# ---------------------------------------------------------------------------
# Mode 1: sample — crop patches from reference images
# ---------------------------------------------------------------------------

REFERENCE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

def load_reference_images(art_dir: Path) -> list[np.ndarray]:
    imgs = []
    for p in sorted(art_dir.iterdir()):
        if p.suffix.lower() in REFERENCE_EXTS:
            try:
                img = Image.open(p).convert("RGB")
                imgs.append(np.array(img))
                print(f"  loaded reference: {p.name} ({img.width}x{img.height})")
            except Exception as e:
                print(f"  skipping {p.name}: {e}", file=sys.stderr)
    return imgs


def generate_sample(refs: list[np.ndarray], rng: random.Random) -> np.ndarray | None:
    """
    Pick a random reference image, crop a random 8x8 patch, snap to palette.
    Returns None if no valid patch could be found.
    """
    if not refs:
        return None
    img = rng.choice(refs)
    h, w = img.shape[:2]
    if h < 8 or w < 8:
        return None
    y = rng.randint(0, h - 8)
    x = rng.randint(0, w - 8)
    patch = img[y:y + 8, x:x + 8, :3]
    return snap_to_palette(patch)


def run_sample(count: int, seed: int, art_dir: Path, out_dir: Path):
    print(f"[sample] Loading reference images from {art_dir} …")
    refs = load_reference_images(art_dir)
    if not refs:
        print("ERROR: no reference images found. Add .png/.webp files to "
              f"{art_dir}", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(seed)
    existing = max((int(p.stem.split("_")[0]) for p in out_dir.glob("*.png")
                    if p.stem.split("_")[0].isdigit()), default=-1) + 1
    saved = 0
    attempts = 0
    while saved < count and attempts < count * 20:
        attempts += 1
        patch = generate_sample(refs, rng)
        if patch is None:
            continue
        idx = existing + saved
        save_candidate(patch, out_dir / f"{idx:04d}.png")
        saved += 1

    print(f"[sample] saved {saved} candidates to {out_dir}")


# ---------------------------------------------------------------------------
# Mode 2: noise — Perlin/Simplex noise → palette
# ---------------------------------------------------------------------------

def generate_noise_patch(rng: random.Random, scale: float,
                         octaves: int, offset_x: float,
                         offset_y: float) -> np.ndarray:
    """
    Build an 8x8 RGB patch using layered Perlin noise, one layer per channel.
    Channel offsets are staggered so R/G/B carry different information.
    """
    patch = np.zeros((8, 8, 3), dtype=np.float32)
    channel_seeds = [rng.uniform(0, 1000) for _ in range(3)]
    for c, cs in enumerate(channel_seeds):
        for py in range(8):
            for px in range(8):
                nx = (offset_x + px) / scale
                ny = (offset_y + py) / scale
                v = noise_lib.pnoise2(
                    nx + cs, ny + cs,
                    octaves=octaves,
                    persistence=0.5,
                    lacunarity=2.0,
                    repeatx=1024, repeaty=1024,
                )
                patch[py, px, c] = v  # in roughly [-1, 1]

    # Normalize each channel independently to [0, 255]
    for c in range(3):
        lo, hi = patch[:, :, c].min(), patch[:, :, c].max()
        if hi > lo:
            patch[:, :, c] = (patch[:, :, c] - lo) / (hi - lo) * 255
        else:
            patch[:, :, c] = 127
    return patch.astype(np.uint8)


def run_noise(count: int, seed: int, scale: float,
              octaves: int, out_dir: Path):
    rng = random.Random(seed)
    existing = max((int(p.stem.split("_")[0]) for p in out_dir.glob("*.png")
                    if p.stem.split("_")[0].isdigit()), default=-1) + 1
    print(f"[noise] generating {count} patches  scale={scale} octaves={octaves}")
    for i in range(count):
        ox = rng.uniform(0, 500)
        oy = rng.uniform(0, 500)
        raw   = generate_noise_patch(rng, scale, octaves, ox, oy)
        patch = snap_to_palette(raw)
        save_candidate(patch, out_dir / f"{existing + i:04d}.png")
    print(f"[noise] saved {count} candidates to {out_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate 8x8 sprite candidates for Lithic Artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--mode", choices=["sample", "noise", "both"],
                   default="both",
                   help="Generation mode (default: both)")
    p.add_argument("--count", type=int, default=32,
                   help="Candidates to generate per mode (default: 32)")
    p.add_argument("--seed", type=int, default=42,
                   help="Random seed (default: 42)")
    # Noise-specific
    p.add_argument("--scale", type=float, default=4.0,
                   help="[noise] Perlin zoom level — larger = broader features (default: 4.0)")
    p.add_argument("--octaves", type=int, default=4,
                   help="[noise] Perlin octave count (default: 4)")
    return p.parse_args()


def main():
    args = parse_args()

    here     = Path(__file__).parent
    art_dir  = here.parent / "art-direction"
    out_dir  = here / "candidates" / "img"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in ("sample", "both"):
        run_sample(args.count, args.seed, art_dir, out_dir)

    if args.mode in ("noise", "both"):
        run_noise(args.count, args.seed, args.scale, args.octaves, out_dir)

    print(f"\nDone. Candidates in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

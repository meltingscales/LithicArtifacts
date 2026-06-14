"""
Generate audio candidates for Lithic Artifacts.

Two modes (choose with --mode):

  wavetable  Sample 8×8 patches from reference art, treat each pixel row as
             one cycle of a waveform (cubic-interpolated to 512 samples),
             and morph through all 8 rows across the clip.  Falls back to a
             Perlin noise patch when no reference images are available.
             Good for: tonal SFX, pickup sounds, weird instrument patches.

  noise      FM synthesis driven by Perlin noise: carrier frequency, FM ratio,
             FM index, and amplitude envelope all vary continuously over time.
             Good for: drones, ambient loops, environmental texture.

Sample rate: 32768 Hz  (GBA native, 2^15)
Channels:    Mono
Bit depth:   16-bit PCM WAV

Usage
-----
  python generate-audio-datamosh.py --mode wavetable [--count 32] [--seed 42]
                                                     [--duration 1.0]
                                                     [--pitch 220]
  python generate-audio-datamosh.py --mode noise     [--count 32] [--seed 42]
                                                     [--duration 1.0]
                                                     [--base-freq 110]
                                                     [--fm-ratio 2.0]
                                                     [--fm-index 3.0]
  python generate-audio-datamosh.py --mode both      [--count 32] [--seed 42]
                                                     [--duration 1.0]

Output: ./candidates/audio/<NNN>.wav
"""

import argparse
import random
import sys
from pathlib import Path

import noise as noise_lib
import numpy as np
import scipy.io.wavfile as wavfile
from PIL import Image
from scipy.interpolate import interp1d

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAMPLE_RATE    = 32768   # GBA native (2^15 Hz)
WAVETABLE_SIZE = 512     # samples per single-cycle wavetable
REFERENCE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _save_wav(samples: np.ndarray, path: Path):
    """Write a float32 [-1, 1] mono array to a 16-bit PCM WAV file."""
    peak = np.abs(samples).max()
    if peak > 0:
        samples = samples / peak          # normalise to full scale
    s16 = (samples * 32767).clip(-32768, 32767).astype(np.int16)
    wavfile.write(str(path), SAMPLE_RATE, s16)


def _next_index(out_dir: Path) -> int:
    """Return the next free sequential index in out_dir."""
    used = [
        int(p.stem) for p in out_dir.glob("*.wav")
        if p.stem.isdigit()
    ]
    return max(used, default=-1) + 1


def _amplitude_envelope(n: int, attack_s: float = 0.02,
                         release_s: float = 0.08) -> np.ndarray:
    env     = np.ones(n, dtype=np.float32)
    attack  = min(int(attack_s  * SAMPLE_RATE), n // 4)
    release = min(int(release_s * SAMPLE_RATE), n // 4)
    if attack  > 0: env[:attack]   = np.linspace(0.0, 1.0, attack)
    if release > 0: env[-release:] = np.linspace(1.0, 0.0, release)
    return env


# ---------------------------------------------------------------------------
# Mode 1: wavetable — image patch → morphing single-cycle waveform
# ---------------------------------------------------------------------------

def _load_refs(art_dir: Path) -> list[np.ndarray]:
    imgs = []
    for p in sorted(art_dir.iterdir()):
        if p.suffix.lower() in REFERENCE_EXTS:
            try:
                img = Image.open(p).convert("RGB")
                imgs.append(np.array(img, dtype=np.float32))
                print(f"  loaded: {p.name} ({img.width}×{img.height})")
            except Exception as e:
                print(f"  skip {p.name}: {e}", file=sys.stderr)
    return imgs


def _noise_patch_8x8(rng: random.Random) -> np.ndarray:
    """Generate an 8×8 luminance patch from Perlin noise (fallback)."""
    base = rng.uniform(0, 500)
    patch = np.array([
        [noise_lib.pnoise2(base + r * 0.4, base + c * 0.4, octaves=3)
         for c in range(8)]
        for r in range(8)
    ], dtype=np.float32)
    # Normalise to [-1, 1]
    lo, hi = patch.min(), patch.max()
    return (patch - lo) / (hi - lo) * 2 - 1 if hi > lo else patch


def _image_patch_8x8(imgs: list[np.ndarray], rng: random.Random) -> np.ndarray:
    """Sample a random 8×8 patch from a reference image, normalise to [-1, 1]."""
    img = rng.choice(imgs)
    h, w = img.shape[:2]
    y = rng.randint(0, h - 8)
    x = rng.randint(0, w - 8)
    patch_rgb = img[y:y + 8, x:x + 8]          # (8, 8, 3)
    lum = patch_rgb.mean(axis=2)                 # (8, 8) luminance
    return (lum - 127.5) / 127.5                 # → [-1, 1]


def _row_to_wavetable(row: np.ndarray) -> np.ndarray:
    """
    Cubic-interpolate 8 amplitude values to WAVETABLE_SIZE samples.
    The waveform wraps seamlessly (first value appended at the end for interp).
    """
    assert len(row) == 8
    x_in  = np.linspace(0.0, 1.0, 8, endpoint=False)
    x_wrap = np.append(x_in, [1.0])
    y_wrap = np.append(row, row[0])
    f      = interp1d(x_wrap, y_wrap, kind="cubic")
    return f(np.linspace(0.0, 1.0, WAVETABLE_SIZE, endpoint=False)).astype(np.float32)


def _synthesize_wavetable(tables: list[np.ndarray], pitch: float,
                           duration: float) -> np.ndarray:
    """
    Morph linearly through `tables` over the clip and read at `pitch` Hz.
    tables: list of WAVETABLE_SIZE float32 arrays in [-1, 1]
    """
    n        = int(SAMPLE_RATE * duration)
    output   = np.zeros(n, dtype=np.float32)
    phase    = 0.0
    phase_inc = pitch * WAVETABLE_SIZE / SAMPLE_RATE   # wavetable-frames per sample
    n_t      = len(tables)

    for i in range(n):
        morph  = (i / n) * (n_t - 1)
        ti     = int(morph)
        tf     = morph - ti
        t1     = tables[min(ti,     n_t - 1)]
        t2     = tables[min(ti + 1, n_t - 1)]

        pi = int(phase) % WAVETABLE_SIZE
        pf = phase - int(phase)
        pi2 = (pi + 1) % WAVETABLE_SIZE

        s1 = t1[pi] + pf * (t1[pi2] - t1[pi])
        s2 = t2[pi] + pf * (t2[pi2] - t2[pi])
        output[i] = (1.0 - tf) * s1 + tf * s2

        phase = (phase + phase_inc) % WAVETABLE_SIZE

    return output * _amplitude_envelope(n)


def run_wavetable(count: int, seed: int, duration: float,
                  pitch: float, art_dir: Path, out_dir: Path):
    print(f"[wavetable] loading reference images from {art_dir} …")
    refs = _load_refs(art_dir)
    if not refs:
        print("  no reference images found — using Perlin noise patches instead")

    rng   = random.Random(seed)
    idx   = _next_index(out_dir)
    print(f"[wavetable] generating {count} clips  pitch={pitch} Hz  duration={duration}s")

    for i in range(count):
        patch = (_image_patch_8x8(refs, rng) if refs
                 else _noise_patch_8x8(rng))
        # Build one wavetable per row; morph through them
        tables = [_row_to_wavetable(patch[r]) for r in range(8)]
        # Randomise pitch slightly (±8%) for variety
        p = pitch * rng.uniform(0.92, 1.08)
        samples = _synthesize_wavetable(tables, p, duration)
        _save_wav(samples, out_dir / f"{idx + i:04d}.wav")

    print(f"[wavetable] saved {count} clips to {out_dir}")


# ---------------------------------------------------------------------------
# Mode 2: noise — FM synthesis driven by Perlin noise
# ---------------------------------------------------------------------------

def _perlin_envelope(duration: float, base: float, scale: float,
                     octaves: int = 3, lo: float = 0.0,
                     hi: float = 1.0) -> np.ndarray:
    """
    Sample pnoise1 at audio rate via a coarse grid + linear interpolation.
    base: noise seed offset; scale: rate of change (higher = faster modulation).
    Returns float32 array of length SAMPLE_RATE * duration, mapped to [lo, hi].
    """
    n         = int(SAMPLE_RATE * duration)
    n_coarse  = max(int(duration * 200), 4)    # 200 control-rate samples/sec
    coarse_x  = np.linspace(0.0, duration * scale, n_coarse)
    coarse_v  = np.array([
        noise_lib.pnoise1(base + x, octaves=octaves) for x in coarse_x
    ], dtype=np.float32)
    fine_x    = np.linspace(0.0, duration * scale, n)
    raw       = np.interp(fine_x, coarse_x, coarse_v).astype(np.float32)
    # Normalise pnoise output (roughly in [-0.9, 0.9]) to [lo, hi]
    raw_n     = (raw + 0.9) / 1.8           # → [0, 1]
    return lo + raw_n * (hi - lo)


def _synthesize_fm(base_freq: float, fm_ratio: float, fm_index: float,
                   duration: float, rng: random.Random) -> np.ndarray:
    """
    FM synthesis: out(t) = sin(φ_c(t) + I(t) · sin(φ_m(t)))
    All parameters are slowly modulated by independent Perlin noise tracks.
    """
    n    = int(SAMPLE_RATE * duration)
    b    = rng.uniform(0.0, 1000.0)          # unique noise seed for this clip

    # Carrier frequency: base_freq ± 30 %
    f_c  = _perlin_envelope(duration, b,       scale=0.8, octaves=3,
                             lo=base_freq * 0.70, hi=base_freq * 1.30)
    # FM ratio: fm_ratio ± 25 %
    ratio = _perlin_envelope(duration, b + 100, scale=0.5, octaves=2,
                              lo=fm_ratio * 0.75, hi=fm_ratio * 1.25)
    # FM index: fm_index ± 40 %
    index = _perlin_envelope(duration, b + 200, scale=1.2, octaves=3,
                              lo=fm_index * 0.60, hi=fm_index * 1.40)
    # Amplitude envelope from noise [0.4, 1.0]
    amp   = _perlin_envelope(duration, b + 300, scale=0.6, octaves=2,
                              lo=0.40, hi=1.00)

    # Integrate phase sample-by-sample to avoid discontinuities
    phi_c = np.cumsum(2.0 * np.pi * f_c      / SAMPLE_RATE).astype(np.float32)
    phi_m = np.cumsum(2.0 * np.pi * f_c * ratio / SAMPLE_RATE).astype(np.float32)

    output = np.sin(phi_c + index * np.sin(phi_m)) * amp
    return output * _amplitude_envelope(n, attack_s=0.03, release_s=0.12)


def run_noise(count: int, seed: int, duration: float, base_freq: float,
              fm_ratio: float, fm_index: float, out_dir: Path):
    rng = random.Random(seed)
    idx = _next_index(out_dir)
    print(f"[noise] generating {count} clips  base_freq={base_freq} Hz  "
          f"ratio={fm_ratio}  index={fm_index}  duration={duration}s")
    for i in range(count):
        samples = _synthesize_fm(base_freq, fm_ratio, fm_index, duration, rng)
        _save_wav(samples, out_dir / f"{idx + i:04d}.wav")
    print(f"[noise] saved {count} clips to {out_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate audio candidates for Lithic Artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--mode", choices=["wavetable", "noise", "both"],
                   default="both",
                   help="Generation mode (default: both)")
    p.add_argument("--count",    type=int,   default=32,
                   help="Clips per mode (default: 32)")
    p.add_argument("--seed",     type=int,   default=42,
                   help="Random seed (default: 42)")
    p.add_argument("--duration", type=float, default=1.0,
                   help="Clip length in seconds (default: 1.0)")
    # Wavetable
    p.add_argument("--pitch",    type=float, default=220.0,
                   help="[wavetable] Fundamental pitch in Hz (default: 220)")
    # Noise / FM
    p.add_argument("--base-freq", type=float, default=110.0,
                   help="[noise] FM carrier base frequency in Hz (default: 110)")
    p.add_argument("--fm-ratio",  type=float, default=2.0,
                   help="[noise] FM modulator-to-carrier ratio (default: 2.0)")
    p.add_argument("--fm-index",  type=float, default=3.0,
                   help="[noise] FM modulation index / depth (default: 3.0)")
    return p.parse_args()


def main():
    args    = parse_args()
    here    = Path(__file__).parent
    art_dir = here.parent / "art-direction"
    out_dir = here / "candidates" / "audio"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in ("wavetable", "both"):
        run_wavetable(args.count, args.seed, args.duration,
                      args.pitch, art_dir, out_dir)

    if args.mode in ("noise", "both"):
        run_noise(args.count, args.seed, args.duration,
                  args.base_freq, args.fm_ratio, args.fm_index, out_dir)

    print(f"\nDone. Candidates in: {out_dir.resolve()}")


if __name__ == "__main__":
    main()

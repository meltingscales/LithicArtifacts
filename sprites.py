"""
Sprite pipeline: text PPMs in assets/sprites/ -> palette PNGs -> Pyxel image bank 0.

PPMs are the source of truth (see assets/sprites/README.md). At startup every
PPM is converted to an indexed PNG under assets/img/ (gitignored, regenerated
each run) and loaded into bank 0 at the slot given in SHEET. Code looks sprites
up by name through SPR, never by raw coordinates.
"""

import os
import struct
import tempfile
import zlib

import pyxel

# fmt: off
# PICO-8 palette. Every doc, palette-index constant and sprite in this repo is
# authored against it; Pyxel's own default palette differs, so main.py applies
# this one at init.
PALETTE = [
    0x000000, 0x1D2B53, 0x7E2553, 0x008751, 0xAB5236, 0x5F574F, 0xC2C3C7, 0xFFF1E8,
    0xFF004D, 0xFFA300, 0xFFEC27, 0x00E436, 0x29ADFF, 0x83769C, 0xFF77A8, 0xFFCCAA,
]
_RGB = [((c >> 16) & 255, (c >> 8) & 255, c & 255) for c in PALETTE]

SPRITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sprites")
PNG_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "img")

# name -> (u, v) destination in image bank 0. Sizes come from the PPM header.
#   y=0   : enemies, pickups, tiles
#   y=8   : player head row (8x16 PPMs cover y=8..23), x = anim frame * 8
#   y=24  : player aim bodies, x = direction * 8; hang-aim from x=64
#   y=32  : player crouch / climb / burrow bodies
#   y=40  : artifact icons
SHEET = {
    "flyer-a":            (  0,  0),
    "flyer-b":            ( 16,  0),
    "shooty-flier-a":     ( 32,  0),
    "shooty-flier-b":     ( 48,  0),
    "crawler-a":          ( 64,  0),
    "crawler-b":          ( 72,  0),
    "missile-canister":   ( 80,  0),
    "tile-fill":          ( 88,  0),
    "tile-top":           ( 96,  0),
    "tile-rock":          (104,  0),

    "player-c":               (  0,  8),
    "player-c-walk-a":        (  8,  8),
    "player-c-walk-b":        ( 16,  8),
    "player-c-jump":          ( 24,  8),
    "player-c-jump-straight": ( 32,  8),
    "player-c-jump-spin":     ( 40,  8),
    "player-c-jump-spin-1":   ( 48,  8),
    "player-c-jump-spin-2":   ( 56,  8),
    "player-c-jump-spin-3":   ( 64,  8),
    "player-c-wallhang":      ( 72,  8),

    "player-c-aim-r":             (  0, 24),
    "player-c-aim-ur":            (  8, 24),
    "player-c-aim-u":             ( 16, 24),
    "player-c-aim-ul":            ( 24, 24),
    "player-c-aim-l":             ( 32, 24),
    "player-c-aim-dl":            ( 40, 24),
    "player-c-aim-d":             ( 48, 24),
    "player-c-aim-dr":            ( 56, 24),
    "player-c-hangaim-away":      ( 64, 24),
    "player-c-hangaim-up":        ( 72, 24),
    "player-c-hangaim-down":      ( 80, 24),
    "player-c-hangaim-diag-up":   ( 88, 24),
    "player-c-hangaim-diag-down": ( 96, 24),

    "player-c-crouch":        (  0, 32),
    "player-c-climb-body":    (  8, 32),
    "player-c-burrow-body":   ( 16, 32),

    "art-wallbreaker":        (  0, 40),
    "art-spiral-borer":       (  8, 40),
    "art-ice-missile":        ( 16, 40),
    "art-rocket-fin":         ( 24, 40),
    "art-vampiric-cape":      ( 32, 40),
    "art-mechaspider-legs":   ( 40, 40),
    "art-fractal-blaster":    ( 48, 40),
}
# fmt: on

SPR = {}  # name -> (u, v, w, h), filled by load_all()


def _nearest(rgb):
    r, g, b = rgb
    return min(
        range(16),
        key=lambda i: (
            (r - _RGB[i][0]) ** 2 + (g - _RGB[i][1]) ** 2 + (b - _RGB[i][2]) ** 2
        ),
    )


def read_ppm(path):
    """Parse a P3 PPM into (w, h, [palette index per pixel, row-major])."""
    with open(path) as f:
        tokens = []
        for line in f:
            line = line.split("#", 1)[0]
            tokens.extend(line.split())
    if not tokens or tokens[0] != "P3":
        raise ValueError(f"not a P3 PPM: {path}")
    w, h = int(tokens[1]), int(tokens[2])
    vals = list(map(int, tokens[4 : 4 + w * h * 3]))
    if len(vals) != w * h * 3:
        raise ValueError(f"{path}: expected {w * h * 3} values, got {len(vals)}")
    return w, h, [_nearest(tuple(vals[i : i + 3])) for i in range(0, len(vals), 3)]


def write_png(path, w, h, idx):
    """Write an 8-bit indexed PNG with the PICO-8 palette (no Pillow needed)."""

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + bytes(idx[y * w : (y + 1) * w]) for y in range(h))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
        + chunk(b"PLTE", bytes(c for rgb in _RGB for c in rgb))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(png)


def _png_dir():
    try:
        os.makedirs(PNG_DIR, exist_ok=True)
        return PNG_DIR
    except OSError:  # read-only install (PyInstaller bundle)
        d = os.path.join(tempfile.gettempdir(), "lithic-artifacts-img")
        os.makedirs(d, exist_ok=True)
        return d


def load_all(bank=0):
    """Convert every PPM named in SHEET to PNG and load it into the image bank."""
    out = _png_dir()
    for name, (u, v) in SHEET.items():
        w, h, idx = read_ppm(os.path.join(SPRITE_DIR, name + ".ppm"))
        png = os.path.join(out, name + ".png")
        write_png(png, w, h, idx)
        pyxel.images[bank].load(u, v, png)
        SPR[name] = (u, v, w, h)

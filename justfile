default:
    @just --list

run:
    uv run python main.py

build:
    uv run pyinstaller lithic_artifacts.spec

install:
    uv sync

fmt:
    uv run ruff format .

lint:
    uv run ruff check .

# Extended help for `sprites`:
#   MODE (positional): sample | noise | both  (default: both)
#     sample  — crop 8×8 patches from art-direction/ refs, snap to Pyxel palette
#     noise   — Perlin noise synthesis, then quantize to palette
#   Flags: --count N (per mode, default 32)  --seed N (default 42)
#          --scale F (noise zoom, default 4.0)  --octaves N (default 4)
#   Examples:
#     just sprites sample --count 64
#     just sprites noise --scale 8.0 --octaves 6
#     just sprites both --seed 7 --count 128

# Generate 8×8 palette-exact sprite candidates → assets/candidates/img/
sprites MODE="both" *ARGS="":
    uv run python assets/generate-8x8-datamosh.py --mode {{MODE}} {{ARGS}}

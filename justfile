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

# Extended help for `audio`:
#   MODE (positional): wavetable | noise | both  (default: both)
#     wavetable  — 8×8 image patches → cubic-interpolated wavetables, morphed per clip
#     noise      — FM synthesis with Perlin-noise-driven carrier, ratio, index, amp
#   Flags: --count N (per mode, default 32)  --seed N (default 42)
#          --duration F (seconds, default 1.0)
#   Wavetable-only:  --pitch F (Hz, default 220)
#   Noise-only:      --base-freq F (carrier Hz, default 110)
#                    --fm-ratio F (mod/carrier ratio, default 2.0)
#                    --fm-index F (modulation depth, default 3.0)
#   Examples:
#     just audio
#     just audio wavetable --pitch 440 --duration 0.5
#     just audio noise --base-freq 55 --fm-ratio 3.5 --fm-index 6.0 --count 64

# Generate audio candidates (32768 Hz mono WAV) → assets/candidates/audio/. For more help, see contents of `justfile`.
audio MODE="both" *ARGS="":
    uv run python assets/generate-audio-datamosh.py --mode {{MODE}} {{ARGS}}

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

# Generate 8×8 palette-exact sprite candidates → assets/candidates/img/. For more help, see contents of `justfile`.
sprites MODE="both" *ARGS="":
    uv run python assets/generate-8x8-datamosh.py --mode {{MODE}} {{ARGS}}

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

# Generate 8x8 sprite candidates from reference art and/or Perlin noise.
# MODE: sample | noise | both  (default: both)
# Extra flags are passed through, e.g.: just sprites noise --scale 6.0 --octaves 3
sprites MODE="both" *ARGS="":
    uv run python assets/generate-8x8-datamosh.py --mode {{MODE}} {{ARGS}}

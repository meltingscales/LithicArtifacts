default:
    @just --list

run:
    uv run python main.py

# Run a self-contained demo from demos/ (e.g. `just demo mechaspider`)
demo NAME *ARGS="":
    uv run python demos/{{NAME}}.py {{ARGS}}

build:
    uv run pyinstaller lithic_artifacts.spec

# Remove PyInstaller build artefacts
clean:
    rm -rf build/ dist/ __pycache__/

# Clean then build
rebuild: clean build

install:
    uv sync

fmt:
    uvx ruff format .

lint:
    uvx ruff check .

# Cyclomatic complexity report (A=1-5 B=6-10 C=11-15 D=16-20 E=21-25 F=26+)
radon:
    uvx radon cc main.py artifacts.py worldgen.py world.py player.py bullets.py pickups.py synergies.py enemies.py constants.py -s -a

# Pylint static analysis report
pylint:
    uvx pylint main.py artifacts.py worldgen.py world.py player.py bullets.py pickups.py synergies.py enemies.py constants.py --output-format=colorized

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

# Generate audio candidates (32768 Hz mono WAV) → assets/candidates/audio/ (gitignored). For more help, see contents of `justfile`.
audio MODE="both" *ARGS="":
    uv run python assets/generate-audio-datamosh.py --mode {{MODE}} {{ARGS}}

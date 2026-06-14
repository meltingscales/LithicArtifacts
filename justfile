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

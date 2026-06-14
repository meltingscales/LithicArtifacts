run:
    uv run python main.py

install:
    uv sync

fmt:
    uv run ruff format .

lint:
    uv run ruff check .

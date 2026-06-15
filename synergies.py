"""
Synergy detection for Lithic Artifacts.

A synergy is active when two artifact classes occupy specific spatial
relationships in the 5×5 body grid.  Functions here are pure — they
take body_grid and return data; side-effects live in main.py.

Public API
----------
fractal_wallbreaker_pairs(body_grid)
    -> list of (r, c, nr, nc) for every adjacent FractalBlaster↔Wallbreaker pair

fractal_wallbreaker_active(body_grid)
    -> bool  (True if at least one adjacent pair exists)
"""

from artifacts import FractalBlaster, Wallbreaker

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def fractal_wallbreaker_pairs(body_grid):
    """
    Return every (r, c, nr, nc) where body_grid[r][c] is FractalBlaster
    and body_grid[nr][nc] is Wallbreaker (4-directional adjacency).
    """
    pairs = []
    for r in range(5):
        for c in range(5):
            if not isinstance(body_grid[r][c], FractalBlaster):
                continue
            for dr, dc in _DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 5 and 0 <= nc < 5:
                    if isinstance(body_grid[nr][nc], Wallbreaker):
                        pairs.append((r, c, nr, nc))
    return pairs


def fractal_wallbreaker_active(body_grid):
    """True if FractalBlaster and Wallbreaker are 4-dir adjacent."""
    return bool(fractal_wallbreaker_pairs(body_grid))

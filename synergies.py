"""
Synergy detection for Lithic Artifacts.

A synergy is active when two artifact classes occupy specific spatial
relationships in the 5×5 body grid.  Functions here are pure — they
take body_grid and return data; side-effects live in main.py.

Public API
----------
all_synergy_pairs(body_grid)
    -> list of (r, c, nr, nc, color) for every active synergy link

fractal_wallbreaker_active(body_grid)  -> bool
rocketfin_ice_active(body_grid)        -> bool

Adding a new synergy
--------------------
1. Write a _xxx_pairs(body_grid) -> list[(r,c,nr,nc)] function.
2. Register it in _SYNERGY_REGISTRY with a unique Pyxel color index.
3. Export an _active helper if game logic needs it.
"""

from artifacts import FractalBlaster, IceMissile, RocketFin, Wallbreaker

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


# ---------------------------------------------------------------------------
# Pair detectors (pure, no side-effects)
# ---------------------------------------------------------------------------

def _adj_pairs(body_grid, cls_a, cls_b):
    """Generic 4-dir adjacency: every (r,c,nr,nc) where [r][c] is cls_a and [nr][nc] is cls_b."""
    pairs = []
    for r in range(5):
        for c in range(5):
            if not isinstance(body_grid[r][c], cls_a):
                continue
            for dr, dc in _DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 5 and 0 <= nc < 5:
                    if isinstance(body_grid[nr][nc], cls_b):
                        pairs.append((r, c, nr, nc))
    return pairs


def fractal_wallbreaker_pairs(body_grid):
    """FractalBlaster ↔ Wallbreaker adjacent pairs."""
    return _adj_pairs(body_grid, FractalBlaster, Wallbreaker)


def rocketfin_ice_pairs(body_grid):
    """RocketFin ↔ IceMissile adjacent pairs."""
    return _adj_pairs(body_grid, RocketFin, IceMissile)


# ---------------------------------------------------------------------------
# Active checks
# ---------------------------------------------------------------------------

def fractal_wallbreaker_active(body_grid):
    """True if FractalBlaster and Wallbreaker are 4-dir adjacent."""
    return bool(fractal_wallbreaker_pairs(body_grid))


def rocketfin_ice_active(body_grid):
    """True if RocketFin and IceMissile are 4-dir adjacent."""
    return bool(rocketfin_ice_pairs(body_grid))


# ---------------------------------------------------------------------------
# Registry — one entry per synergy: (pairs_fn, pyxel_color)
# Each synergy MUST use a distinct color so the player can tell them apart.
# fmt: off
_SYNERGY_REGISTRY = [
    (fractal_wallbreaker_pairs, 14),   # pink  — FractalBlaster + Wallbreaker
    (rocketfin_ice_pairs,       12),   # cyan  — RocketFin + IceMissile
]
# fmt: on


def all_synergy_pairs(body_grid):
    """
    Return (r, c, nr, nc, color) for every active synergy link.
    Drives the body-panel line renderer in main.py.
    """
    out = []
    for pairs_fn, color in _SYNERGY_REGISTRY:
        for r, c, nr, nc in pairs_fn(body_grid):
            out.append((r, c, nr, nc, color))
    return out

"""
Section-based dungeon generator for Lithic Artifacts.

The dungeon is divided into SECTION_H-row sections.  Each section
guarantees a clear vertical corridor (the "free range") so the player
can always descend.  Sections chain by handing the exit free range to
the next section as its entry free range.

Public API
----------
gen_section(rng, abs_start_row, entry_free_l, entry_free_r, artifact_cls)
    -> (tile_dict, spawn_list, pickup_spec_or_None, exit_free_l, exit_free_r)

pickup_spec_or_None: (col, row, artifact_cls) or None
tile_dict:           {(col, row): 1}  — absolute coords, walls included
spawn_list:          [(px_x, px_y, type_str)]
"""

import random
from collections import deque

import noise as _noise

# Mirrors of main.py constants (no import to avoid circular deps)
# fmt: off
_COLS             = 30
_SECTION_H        = 20
_MIN_FREE         = 4     # narrowest permitted corridor (must fit the player)
_JUMP_H           = 4     # max tiles the player can jump upward (for BFS)
_CAVE_MAX_RETRIES = 15    # retry budget for cave traversability check

SECTION_H = _SECTION_H   # exported for main.py
# fmt: on


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def gen_section(rng, abs_start_row, entry_free_l, entry_free_r, artifact_cls=None):
    """
    Generate one SECTION_H-row section of the dungeon.

    Parameters
    ----------
    rng             : random.Random
    abs_start_row   : absolute tile-row of the section's top edge
    entry_free_l/r  : inclusive open column range inherited from previous section
    artifact_cls    : ArtifactClass to place as a world pickup, or None

    Returns
    -------
    tiles        : {(col, row): 1}  absolute coords; includes side walls
    spawns       : [(px_x, px_y, type_str)]
    pickup_spec  : (col, row_above_pedestal, artifact_cls) or None
    free_l       : exit corridor left  (pass to next section as entry_free_l)
    free_r       : exit corridor right
    """
    stype = rng.choices(
        ("open", "platforms", "chamber", "cave"),
        weights=(0.20, 0.35, 0.15, 0.30),
    )[0]

    # Drift the corridor centre within ±4 cols, clamped to leave room for wings
    cx = (entry_free_l + entry_free_r) // 2
    cx = max(5, min(_COLS - 6, cx + rng.randint(-4, 4)))

    # fmt: off
    free_w = max(_MIN_FREE, {
        'open':      rng.randint(10, 16),
        'platforms': rng.randint(5,  9),
        'chamber':   rng.randint(12, 18),
        'cave':      rng.randint(6,  10),
    }[stype])
    # fmt: on

    free_l = max(1, cx - free_w // 2)
    free_r = min(_COLS - 2, free_l + free_w - 1)
    free_l = max(1, free_r - free_w + 1)  # re-clamp after right side clamped

    tiles = {}
    pickup = None

    # Side walls for every row in the section
    for r in range(_SECTION_H):
        row = abs_start_row + r
        # fmt: off
        tiles[(0, row)]          = 1
        tiles[(_COLS - 1, row)]  = 1
        # fmt: on

    if stype == "platforms":
        _gen_platforms(rng, tiles, abs_start_row, free_l, free_r, density=0.32)
    elif stype == "open":
        _gen_platforms(rng, tiles, abs_start_row, free_l, free_r, density=0.14)
    elif stype == "cave":
        for attempt in range(_CAVE_MAX_RETRIES):
            cave_tiles = {}
            _gen_cave(rng, cave_tiles, abs_start_row, free_l, free_r)
            if _is_traversable(cave_tiles, abs_start_row, free_l, free_r):
                tiles.update(cave_tiles)
                break
        else:
            # All retries failed — fall back to an open section
            _gen_platforms(rng, tiles, abs_start_row, free_l, free_r, density=0.08)
    else:  # chamber
        _gen_chamber(rng, tiles, abs_start_row, free_l, free_r)

    spawns = _gen_spawns(rng, tiles, abs_start_row, stype)

    if artifact_cls is not None:
        pickup = _place_pickup(tiles, abs_start_row, free_l, free_r, artifact_cls)

    return tiles, spawns, pickup, free_l, free_r


# ---------------------------------------------------------------------------
# Section sub-generators
# ---------------------------------------------------------------------------


def _gen_platforms(rng, tiles, abs_start, free_l, free_r, density):
    """
    Scatter wing platforms.  The free corridor [free_l..free_r] stays clear.
    Left wing: columns 1 to free_l-1.
    Right wing: columns free_r+1 to COLS-2.
    """
    for r in range(2, _SECTION_H - 1):
        if rng.random() >= density:
            continue
        row = abs_start + r

        # Left wing
        if free_l > 3 and rng.random() < 0.65:
            pw = rng.randint(2, max(2, free_l - 2))
            pl = rng.randint(1, max(1, free_l - pw - 1))
            for c in range(pl, min(pl + pw, free_l)):
                tiles[(c, row)] = 1

        # Right wing
        if free_r < _COLS - 4 and rng.random() < 0.65:
            pw = rng.randint(2, max(2, _COLS - 2 - free_r - 1))
            pr = rng.randint(free_r + 1, max(free_r + 1, _COLS - 2 - pw))
            for c in range(pr, min(pr + pw, _COLS - 1)):
                tiles[(c, row)] = 1


def _gen_chamber(rng, tiles, abs_start, free_l, free_r):
    """
    A walled room: horizontal ceiling + floor rows with openings at the
    free corridor.  Optional wing platform inside the room.
    """
    top = abs_start + 1
    bot = abs_start + _SECTION_H - 2
    for c in range(1, _COLS - 1):
        if not (free_l <= c <= free_r):
            tiles[(c, top)] = 1
            tiles[(c, bot)] = 1

    # Optional interior wing platform
    if rng.random() < 0.55:
        mid = abs_start + _SECTION_H // 2
        side = rng.choice(("left", "right"))
        if side == "left" and free_l > 4:
            pw = rng.randint(2, max(2, free_l - 2))
            pl = rng.randint(1, max(1, free_l - pw - 1))
            for c in range(pl, min(pl + pw, free_l)):
                tiles[(c, mid)] = 1
        elif side == "right" and free_r < _COLS - 5:
            pw = rng.randint(2, max(2, _COLS - 2 - free_r - 1))
            pr = rng.randint(free_r + 1, max(free_r + 1, _COLS - 2 - pw))
            for c in range(pr, min(pr + pw, _COLS - 1)):
                tiles[(c, mid)] = 1


def _gen_cave(rng, tiles, abs_start, free_l, free_r):
    """
    Perlin-noise cave section.  Solid cells become tile type 2 (cave rock).
    The free corridor [free_l..free_r] is always cleared so the BFS always
    has a candidate path; the retry loop validates more complex routes too.
    Side walls (col 0 and _COLS-1) are added by the caller.
    """
    # Fresh random offsets per attempt so retries look different
    ox = rng.uniform(0, 1000)
    oy = rng.uniform(0, 1000)
    # fmt: off
    scale     = 0.18   # spatial frequency — higher = smaller features
    threshold = -0.05  # pnoise2 values above this → solid cave rock (~52% fill)
    # fmt: on
    for r in range(_SECTION_H):
        row = abs_start + r
        for c in range(1, _COLS - 1):
            if free_l <= c <= free_r:
                continue  # always keep the corridor open
            n = _noise.pnoise2(ox + c * scale, oy + r * scale, octaves=2)
            if n > threshold:
                tiles[(c, row)] = 2


def _is_traversable(tiles, abs_start, free_l, free_r):
    """
    BFS reachability check.  Returns True if a 1×2 player can get from
    the top entry corridor to within two rows of the section bottom.

    State: (col, foot_row) where foot_row is the lower of the two body rows.
    Player fits at state (c, f) when neither (c, f) nor (c, f-1) is solid.
    """
    bot = abs_start + _SECTION_H

    def solid(c, r):
        return (c, r) in tiles

    def fits(c, f):
        """1×2 player fits at foot_row=f (head row = f-1)."""
        return (
            1 <= c <= _COLS - 2
            and abs_start <= f < bot
            and not solid(c, f)
            and not solid(c, f - 1)
        )

    def fall_to(c, f):
        """Let the player fall from foot_row=f; return landed foot_row."""
        while f + 1 < bot and not solid(c, f + 1):
            f += 1
        return f

    # Seed: drop from every entry-corridor column at the section top
    visited = set()
    queue = deque()
    for c in range(free_l, free_r + 1):
        if fits(c, abs_start):
            lf = fall_to(c, abs_start)
            if fits(c, lf) and (c, lf) not in visited:
                visited.add((c, lf))
                queue.append((c, lf))

    while queue:
        col, foot = queue.popleft()
        if foot >= bot - 2:
            return True

        grounded = solid(col, foot + 1) or foot + 1 >= bot
        nexts = []

        if not grounded:
            nf = foot + 1
            if fits(col, nf):
                nexts.append((col, nf))
        else:
            # Walk one step left or right, then fall to landing
            for dc in (-1, 1):
                nc = col + dc
                if fits(nc, foot):
                    lf = fall_to(nc, foot)
                    if fits(nc, lf):
                        nexts.append((nc, lf))

            # Jump: rise up to _JUMP_H rows, then drift left/right and fall
            for dh in range(1, _JUMP_H + 1):
                pf = foot - dh  # foot row at jump apex
                if pf < abs_start:
                    break
                # Abort if any upward cell is blocked (ceiling collision)
                if any(solid(col, foot - k) for k in range(1, dh + 1)):
                    break
                if not fits(col, pf):
                    break
                for dc in range(-dh, dh + 1):
                    nc = col + dc
                    if not fits(nc, pf):
                        continue
                    lf = fall_to(nc, pf)
                    if fits(nc, lf):
                        nexts.append((nc, lf))

        for st in nexts:
            if st not in visited:
                visited.add(st)
                queue.append(st)

    return False


def _gen_spawns(rng, tiles, abs_start, stype):
    """Place enemy spawns on top of solid tiles that have open space above."""
    spawns = []
    density = 0.28 if stype == "platforms" else 0.12
    for r in range(1, _SECTION_H - 1):
        row = abs_start + r
        if rng.random() >= density:
            continue
        candidates = [
            c
            for c in range(1, _COLS - 1)
            if (c, row) in tiles and (c, row - 1) not in tiles
        ]
        if not candidates:
            continue
        col = rng.choice(candidates)
        px = col * 8
        py = (row - 1) * 8  # open cell above the solid tile
        roll = rng.random()
        if roll < 0.50:
            spawns.append((px, py, "crawler"))
        elif roll < 0.80:
            spawns.append((px, max(0, py - 24), "flyer"))
        else:
            spawns.append((px, max(0, py - 24), "shooty_flier"))
    return spawns


def _place_pickup(tiles, abs_start, free_l, free_r, artifact_cls):
    """
    Place an artifact pickup on a pedestal in the middle of the free corridor.
    Adds one pedestal tile; returns (pedestal_col, row_above, artifact_cls).
    """
    mid_c = (free_l + free_r) // 2
    ped_r = abs_start + _SECTION_H // 2
    tiles[(mid_c, ped_r)] = 1  # pedestal tile
    return (mid_c, ped_r - 1, artifact_cls)  # pickup sits one row above pedestal

import random
# fmt: off
from artifacts import (
    FractalBlaster, IceMissile, MechaspiderLegs, RocketFin,
    SpiralBorer, VampiricCape, Wallbreaker,
)
from pickups  import WorldPickup
from worldgen import gen_section
from constants import (
    TILE, COLS, PREAMBLE_ROWS, SECTION_H,
    DEFAULT_SEED, SEED_WALLS, SEED_EMPTY, SEED_GAUNTLET,
)
# fmt: on

_ARTIFACT_POOL = [
    SpiralBorer,
    VampiricCape,
    Wallbreaker,
    IceMissile,
    RocketFin,
    FractalBlaster,
    MechaspiderLegs,
]  # artifact classes that can appear as world pickups


class World:
    def __init__(self, seed=DEFAULT_SEED):
        # fmt: off
        self.seed           = seed
        self.tiles          = {}
        self.rng            = random.Random(seed)
        self.pending_spawns = []   # [(px_x, px_y, type_str)] drained by Game each frame
        self.pickups        = []   # [WorldPickup] persistent world items
        self._gen_sections  = 0    # number of sections generated so far
        self._free_l        = COLS // 4        # initial corridor bounds
        self._free_r        = 3 * COLS // 4
        self._next_art_sec  = self.rng.randint(1, 3)   # section index for first artifact
        # fmt: on

        # Hardcoded entrance (rows 0 – PREAMBLE_ROWS-1)
        for x in range(COLS):  # solid ceiling
            self.tiles[(x, 0)] = 1
        for y in range(1, PREAMBLE_ROWS):  # boundary walls only
            # fmt: off
            self.tiles[(0, y)]          = 1
            self.tiles[(COLS - 1, y)]   = 1
            # fmt: on

        if seed == SEED_WALLS:
            # Wall playground: 4 vertical walls with 2-tile-high gaps at
            # different heights — tests gap traversal and SpiralBorer phasing.
            # fmt: off
            for wall_x, gap_top in ((6, 3), (12, 5), (18, 2), (24, 4)):
                for r in range(1, PREAMBLE_ROWS):
                    if not (gap_top <= r < gap_top + 2):
                        self.tiles[(wall_x, r)] = 1
            # Floor at row 12 with a centre gap to fall through to section below
            for c in range(1, COLS - 1):
                if not (13 <= c <= 16):
                    self.tiles[(c, 12)] = 1
            # fmt: on
        else:
            gap = self.rng.randint(5, COLS - 10)
            for x in range(1, COLS - 1):  # first platform at row 8
                if not (gap <= x < gap + 5):
                    self.tiles[(x, 8)] = 1

        # Pre-generate several sections so the player never hits a blank wall
        self._gen_up_to(4)

    # ---- section generation ----

    def _pick_artifact_cls(self):
        if self._gen_sections < self._next_art_sec:
            return None
        cls = self.rng.choice(_ARTIFACT_POOL)
        self._next_art_sec = self._gen_sections + self.rng.randint(3, 6)
        return cls

    def _gen_up_to(self, n_sections):
        """Generate sections until at least n_sections exist."""
        while self._gen_sections < n_sections:
            abs_start = PREAMBLE_ROWS + self._gen_sections * SECTION_H
            art_cls   = self._pick_artifact_cls()  # fmt: skip

            if self.seed == SEED_WALLS and self._gen_sections == 0:
                # Hand-crafted 1-block step test: solid floor + pillars every 3 cols.
                # Verifies gap_snap doesn't auto-climb 1-tile obstacles.
                floor_r = abs_start + SECTION_H - 3
                tiles = {}
                for r in range(SECTION_H):
                    tiles[(0, abs_start + r)]        = 1
                    tiles[(COLS - 1, abs_start + r)] = 1
                for c in range(1, COLS - 1):
                    tiles[(c, floor_r)] = 1          # solid floor
                for c in range(3, COLS - 2, 3):
                    tiles[(c, floor_r - 1)] = 1      # 1-block pillar on floor
                spawns, pickup_spec = [], None
                fl, fr = self._free_l, self._free_r
            else:
                tiles, spawns, pickup_spec, fl, fr = gen_section(
                    self.rng, abs_start, self._free_l, self._free_r, art_cls
                )

            # Special-seed overrides (see SPECIAL-SEEDS.md)
            if self.seed == SEED_EMPTY:   # empty world — strip interior tiles + spawns
                tiles  = {k: v for k, v in tiles.items() if k[0] in (0, COLS - 1)}
                spawns = []
            elif self.seed == SEED_GAUNTLET:  # gauntlet — guarantee all enemy types per section
                mid_r = abs_start + SECTION_H // 2
                cx    = (fl + fr) // 2  # fmt: skip
                spawns += [
                    (cx * TILE,                          (mid_r - 5) * TILE, "flyer"),
                    (min(COLS - 2, cx + 5) * TILE,      (mid_r - 5) * TILE, "shooty_flier"),
                    (max(1,        cx - 5) * TILE,       (mid_r - 1) * TILE, "crawler"),
                ]
            self.tiles.update(tiles)
            self.pending_spawns.extend(spawns)
            if pickup_spec is not None:
                col, row, cls = pickup_spec
                self.pickups.append(WorldPickup(col * TILE, row * TILE, cls))
            # fmt: off
            self._free_l       = fl
            self._free_r       = fr
            # fmt: on
            self._gen_sections += 1

    def ensure_gen(self, row):
        """Ensure the dungeon is generated at least two full sections beyond row."""
        if row <= PREAMBLE_ROWS:
            return
        needed = (row - PREAMBLE_ROWS) // SECTION_H + 2
        if needed > self._gen_sections:
            self._gen_up_to(needed)

    def solid(self, col, row):
        return self.tiles.get((int(col), int(row)), 0) != 0

    def destroy(self, col, row):
        self.tiles.pop((int(col), int(row)), None)

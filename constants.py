"""
Tunable game-wide constants for Lithic Artifacts.

Import this module wherever constants are needed instead of duplicating
values.  Only gameplay-relevant constants live here; UI layout, palette
indices, and per-class fractal/visual parameters stay in their modules.
"""

# ---- Screen / tile grid -----------------------------------------------
# fmt: off
SCREEN_W = 240
SCREEN_H = 160
TILE     = 8
COLS     = SCREEN_W // TILE   # 30
# fmt: on

# ---- Dungeon structure ------------------------------------------------
# fmt: off
PREAMBLE_ROWS     = 15   # hardcoded entrance rows above first generated section
SECTION_H         = 20   # height of one generated section (tile rows)
BIOME_SECTION_LEN = 6    # dungeon sections per biome
# fmt: on

# ---- Worldgen ---------------------------------------------------------
# fmt: off
CORRIDOR_MIN_FREE        = 4     # narrowest permitted free corridor (tiles)
BFS_JUMP_H               = 4     # max tiles player can jump upward (traversability BFS)
CAVE_MAX_RETRIES         = 15    # retries before cave falls back to open section

# Section-type RNG weights: (open, platforms, chamber, cave)
STYPE_WEIGHTS = (0.20, 0.35, 0.15, 0.30)

# Density of wing platforms spawned in each section type
PLAT_DENSITY_PLATFORMS     = 0.32
PLAT_DENSITY_OPEN          = 0.14
PLAT_DENSITY_CAVE_FALLBACK = 0.08   # used when all cave retries are exhausted

# Probability that a given row gets an enemy spawn candidate
SPAWN_DENSITY_PLATFORMS = 0.28
SPAWN_DENSITY_DEFAULT   = 0.12
# fmt: on

# ---- Player physics ---------------------------------------------------
# fmt: off
GRAVITY       = 0.25
MAX_FALL      = 4.0
MOVE_SPEED    = 1.5
JUMP_VEL      = -4.5
JUMP_VEL_MIN  = -1.5   # vy floor when jump button released early (variable jump height)
WALL_JUMP_VEL = -4.0
WALL_JUMP_HVX = 2.0
WALL_JUMP_CD  = 24     # frames before same-side wall jump is available again
P_HIT_INS     = 1      # horizontal inset for floor/ceiling checks
# fmt: on

# ---- Bullets / combat -------------------------------------------------
# fmt: off
BULLET_SPEED   = 5.0
SHOOT_COOLDOWN = 12    # frames between player shots
DEATH_HOLD     = 90    # frames of death screen before respawn prompt appears
# fmt: on

# ---- Enemies ----------------------------------------------------------
# fmt: off
CRAWLER_SPEED  = 0.5
FLYER_SPEED    = 0.6
FLYER_AMP      = 18    # vertical oscillation amplitude (px)
FLYER_FREQ     = 0.04  # radians per frame
SHOOT_INTERVAL = 120   # frames between ShootyFlier shots
SHOOT_RANGE    = 96    # px; ShootyFlier won't fire beyond this range
# fmt: on

# ---- Drop chances -----------------------------------------------------
# fmt: off
CANISTER_DROP_CHANCE      = 0.20   # probability per kill of dropping a missile canister
SYNERGY_WALL_BREAK_CHANCE = 0.10   # FractalBullet+Wallbreaker: chance to break tile on pierce
# fmt: on

# ---- Artifacts --------------------------------------------------------
ICE_MISSILE_MAX_AMMO = 30

# ---- Seeds ------------------------------------------------------------
# fmt: off
DEFAULT_SEED  = 314159   # default run seed; displayed in the pause menu
SEED_WALLS    = 0        # wall playground: gapped vertical walls in preamble
SEED_EMPTY    = 1        # empty world: no interior tiles or enemy spawns per section
SEED_GAUNTLET = 2        # gauntlet: all three enemy types added to every section
# fmt: on

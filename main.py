import math
import pyxel
import random

# fmt: off
from artifacts import FractalBlaster, IceMissile, MechaspiderLegs, MissileArtifact, SpiralBorer, VampiricCape, Wallbreaker
from enemies   import Crawler, Flyer, ShootyFlier, EnemyBullet
from worldgen  import gen_section
from synergies import fractal_wallbreaker_active, fractal_wallbreaker_pairs
from constants import (
    SCREEN_W, SCREEN_H, TILE, COLS,
    PREAMBLE_ROWS, SECTION_H, BIOME_SECTION_LEN,
    GRAVITY, MAX_FALL, MOVE_SPEED,
    JUMP_VEL, JUMP_VEL_MIN, WALL_JUMP_VEL, WALL_JUMP_HVX, WALL_JUMP_CD,
    BULLET_SPEED, SHOOT_COOLDOWN, DEATH_HOLD,
    P_HIT_INS, CANISTER_DROP_CHANCE, SYNERGY_WALL_BREAK_CHANCE,
    CLIMB_SPEED,
    DEFAULT_SEED, SEED_WALLS, SEED_EMPTY, SEED_GAUNTLET,
)
# fmt: on

# fmt: off
BLACK      = 0
DARK_GRAY  = 5
LIGHT_GRAY = 6
YELLOW     = 10
ORANGE     = 9
BROWN      = 4

P_W = TILE
P_H = TILE * 2

_BIOMES = [
    # name        bg  wall_fill  wall_brd  cave_fill  cave_brd
    ("Dungeon",    0,     5,        6,        4,          5),
    ("Caverns",    1,     5,        6,       13,          1),
    ("Abyss",      2,    13,        6,        1,         13),
    ("Depths",     3,     3,       11,        3,          6),
    ("Inferno",    0,     8,        9,        4,          8),
]
# fmt: on


def biome_for_row(abs_row):
    if abs_row < PREAMBLE_ROWS:
        return 0
    section_idx = (abs_row - PREAMBLE_ROWS) // SECTION_H
    return (section_idx // BIOME_SECTION_LEN) % len(_BIOMES)


# Pause / body-panel layout (UI-only; not in constants.py)
# fmt: off
_CELL = 13   # body-grid cell pitch (12 px visible + 1 px gap)
_GX   = 8    # body grid left edge
_GY   = 18   # body grid top edge
_IX   = 82   # inventory list left edge
_IY   = 18   # inventory list top edge
_IRH  = 10   # inventory row height
_TIPY = 131  # tooltip divider y
_HOVER = 180 # frames of hover before description appears (3 s @ 60 fps)
# fmt: on
_ARTIFACT_POOL = [
    SpiralBorer,
    VampiricCape,
    Wallbreaker,
    IceMissile,
    FractalBlaster,
    MechaspiderLegs,
]  # artifact classes that can appear as world pickups
# fmt: on


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


class Bullet:
    LIFETIME = 90

    def __init__(self, x, y, dx, dy):
        mag = math.sqrt(dx * dx + dy * dy)
        # fmt: off
        self.x               = float(x)
        self.y               = float(y)
        self.vx              = dx / mag * BULLET_SPEED
        self.vy              = dy / mag * BULLET_SPEED
        self.life            = self.LIFETIME
        self.alive           = True
        self.can_break_walls = False  # set True by Wallbreaker artifact
        # fmt: on

    def update(self, world):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        if world.solid(int(self.x // TILE), int(self.y // TILE)):
            if self.can_break_walls:
                world.destroy(int(self.x // TILE), int(self.y // TILE))
            self.alive = False

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < SCREEN_H:
            pyxel.rect(int(self.x), sy, 2, 2, ORANGE)


class MissileBullet:
    LIFETIME = 120
    SPEED = 3.0
    DAMAGE = 2
    FREEZE_FRAMES = 300  # 5 s at 60 fps

    def __init__(self, x, y, dx, dy):
        mag = math.sqrt(dx * dx + dy * dy) or 1.0
        # fmt: off
        self.x               = float(x)
        self.y               = float(y)
        self.vx              = dx / mag * self.SPEED
        self.vy              = dy / mag * self.SPEED
        self.life            = self.LIFETIME
        self.alive           = True
        self.can_break_walls = False
        # fmt: on

    def update(self, world):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        col, row = int(self.x // TILE), int(self.y // TILE)
        if world.solid(col, row):
            if self.can_break_walls:
                world.destroy(col, row)
            self.alive = False

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < SCREEN_H:
            x = int(self.x)
            pyxel.rect(x, sy, 3, 3, 12)  # cyan body
            pyxel.pset(x + 1, sy + 1, 7)  # white center pixel


class FractalBullet:
    """Piercing bullet that traces the Julia set boundary; pierces terrain and enemies."""

    # fmt: off
    LIFETIME = 150
    SPEED    = 4.0
    DAMAGE   = 1
    # fmt: on

    def __init__(self, x, y, dx, dy, julia_cache, cam):
        mag = math.sqrt(dx * dx + dy * dy) or 1.0
        nx, ny = dx / mag, dy / mag
        # fmt: off
        self.x               = float(x)
        self.y               = float(y)
        self._nx             = nx
        self._ny             = ny
        self.life            = self.LIFETIME
        self.alive           = True
        self.piercing        = True
        self.hit_enemies: set = set()
        # fmt: on
        self._waypoints = self._build_waypoints(x, y, nx, ny, julia_cache, cam)
        self._wp_idx           = 0  # fmt: skip
        self._jitter           = random.uniform(-0.2, 0.2)  # fmt: skip
        self._splinter_events  = 0  # fmt: skip
        self.pending_splinters: list = []
        self.synergy_wall_break = (
            False  # set True by FractalBlaster+Wallbreaker adjacency
        )

    @staticmethod
    def _build_waypoints(gx, gy, nx, ny, cache, cam):
        if cache is None:
            return []
        H, W = cache.shape
        MAX_ITER = int(cache.max())
        boundary = []
        for ry in range(H):
            for rx in range(W):
                in_set = int(cache[ry, rx]) == MAX_ITER
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = ry + dr, rx + dc
                    if 0 <= nr < H and 0 <= nc < W:
                        if (int(cache[nr, nc]) == MAX_ITER) != in_set:
                            boundary.append((rx * 8 + 4, ry * 8 + 4))
                            break
                    else:
                        break
        # Convert screen → world, sort by projection along firing direction,
        # keep only points ahead of the gun
        pts = []
        for sx, sy in boundary:
            wy = sy + cam
            proj = (sx - gx) * nx + (wy - gy) * ny
            if proj > 0:
                pts.append((proj, sx, wy))
        pts.sort()
        return [(sx, wy) for _, sx, wy in pts]

    def update(self, world):
        if self._wp_idx < len(self._waypoints):
            wx, wy = self._waypoints[self._wp_idx]
            ddx, ddy = wx - self.x, wy - self.y
            dist = math.sqrt(ddx * ddx + ddy * ddy)
            if dist <= self.SPEED:
                self.x, self.y = wx, wy
                self._wp_idx += 1
                self._jitter = random.uniform(-0.2, 0.2)
                if self._wp_idx % 3 == 0 and self._splinter_events < 5:
                    self._splinter_events += 1
                    base = random.uniform(0, math.tau)
                    for i in range(2):
                        angle = base + i * math.pi + random.uniform(-0.5, 0.5)
                        self.pending_splinters.append(
                            FractalBulletSmall(self.x, self.y, angle)
                        )
            else:
                c, s = math.cos(self._jitter), math.sin(self._jitter)
                jx = (ddx * c - ddy * s) / dist * self.SPEED
                jy = (ddx * s + ddy * c) / dist * self.SPEED
                self.x += jx
                self.y += jy
        else:
            self.x += self._nx * self.SPEED
            self.y += self._ny * self.SPEED
        self.life -= 1
        if self.life <= 0:
            self.alive = False
        # Pierces terrain — passes through walls; synergy may destroy them
        if self.synergy_wall_break:
            col, row = int(self.x // TILE), int(self.y // TILE)
            if world.solid(col, row) and random.random() < SYNERGY_WALL_BREAK_CHANCE:
                world.destroy(col, row)

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < SCREEN_H:
            col = 12 if (pyxel.frame_count // 3) % 2 else 13  # cyan / indigo pulse
            pyxel.rect(int(self.x), sy, 3, 3, col)


class FractalBulletSmall:
    """Splinter fired by FractalBullet on boundary hits. Pierces terrain and enemies."""

    # fmt: off
    LIFETIME = 50
    SPEED    = 2.0
    DAMAGE   = 1
    # fmt: on

    def __init__(self, x, y, angle):
        # fmt: off
        self.x           = float(x)
        self.y           = float(y)
        self._vx         = math.cos(angle) * self.SPEED
        self._vy         = math.sin(angle) * self.SPEED
        self.life             = self.LIFETIME
        self.alive            = True
        self.piercing         = True
        self.hit_enemies: set = set()
        # fmt: on

    def update(self, world):
        self.x += self._vx
        self.y += self._vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False
        # Pierces terrain — never destroys walls

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < SCREEN_H:
            col = 14 if (pyxel.frame_count // 4) % 2 else 8  # pink / red pulse
            pyxel.rect(int(self.x), sy, 2, 2, col)


class WorldPickup:
    """An artifact resting in the world on a pedestal, waiting to be collected."""

    def __init__(self, x, y, artifact_cls):
        # fmt: off
        self.x            = float(x)
        self.y            = float(y)
        self.artifact_cls = artifact_cls
        self.collected    = False
        # fmt: on

    # fmt: off
    @property
    def right(self):  return self.x + TILE
    @property
    def bottom(self): return self.y + TILE
    # fmt: on

    def draw(self, cam):
        sy = int(self.y - cam)
        if not (-TILE <= sy < SCREEN_H):
            return
        col = YELLOW if (pyxel.frame_count // 8) % 2 else ORANGE
        pyxel.rectb(int(self.x), sy, TILE, TILE, col)
        pyxel.text(int(self.x) + 2, sy + 1, self.artifact_cls.glyph, YELLOW)


class MissileCanister:
    """Dropped by enemies (1/5 chance); refills 5 ammo to least-full missile artifact."""

    # fmt: off
    LIFETIME    = 600   # 10 s at 60 fps
    BLINK_START = 180   # blink during last 3 s
    BLINK_RATE  = 6     # frames per on/off half-cycle
    AMMO_AMOUNT = 5
    # fmt: on

    def __init__(self, x, y):
        # fmt: off
        self.x     = float(x)
        self.y     = float(y)
        self.timer = self.LIFETIME
        self.alive = True
        # fmt: on

    # fmt: off
    @property
    def right(self):  return self.x + TILE
    @property
    def bottom(self): return self.y + TILE
    # fmt: on

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False

    def draw(self, cam):
        sy = int(self.y - cam)
        if not (-TILE <= sy < SCREEN_H):
            return
        if self.timer < self.BLINK_START and (self.timer // self.BLINK_RATE) % 2 == 1:
            return
        col = 12 if (pyxel.frame_count // 8) % 2 else 7  # cyan / white pulse
        pyxel.rectb(int(self.x), sy, TILE, TILE, col)
        pyxel.text(int(self.x) + 2, sy + 1, "~", col)


class Player:
    def __init__(self):
        # fmt: off
        self.x  = float(SCREEN_W // 2 - P_W // 2)
        self.y  = float(TILE * 2)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground    = False
        self.facing       = 1        # 1=right, -1=left
        self.aim_dx       = 1
        self.aim_dy       = 0
        self.aim_locked   = False
        self.shoot_cd     = 0
        self.state        = "normal" # "normal" | "hanging"
        self.hang_wall    = 0        # 1=right, -1=left
        self.jump_type    = "none"   # "none" | "straight" | "spin"
        self.wall_contact = 0        # 1=right, -1=left, 0=none
        self.wj_cd_l      = 0
        self.wj_cd_r      = 0
        self.ledge_cd     = 0
        self.burrowing    = False
        self.crouching    = False
        self.climbing     = False
        self.artifacts    = []
        self.hp           = 10
        self.max_hp       = 10
        self.inv_cd       = 0    # invincibility frames after taking damage
        # fmt: on

    # fmt: off
    @property
    def right(self):  return self.x + P_W
    @property
    def bottom(self): return self.y + (TILE if self.crouching else P_H)
    @property
    def gun_x(self):  return self.x + P_W / 2
    @property
    def gun_y(self):  return self.y + (2 if self.crouching else P_H // 4)
    # fmt: on


class _Restart:
    """Sentinel for debug-menu entries that trigger a full game reset."""
    def __init__(self, seed): self.seed = seed


# fmt: off
DEBUG_ITEMS = [
    ("Spiral Borer",         SpiralBorer),
    ("Wallbreaker",          Wallbreaker),
    ("Vampiric Cape",        VampiricCape),
    ("Ice Missiles",         IceMissile),
    ("Fractal Blaster",      FractalBlaster),
    ("Mechaspider Legs",     MechaspiderLegs),
    ("Immortality?",         None),             # None  = boolean flag, not artifact
    # ---- seed restarts (see SPECIAL-SEEDS.md) ----
    ("Restart [0] walls",    _Restart(0)),
    ("Restart [1] empty",    _Restart(1)),
    ("Restart [2] gauntlet", _Restart(2)),
    ("Restart [default]",    _Restart(DEFAULT_SEED)),
]
# fmt: on


class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Lithic Artifacts", fps=60)
        # Sprites — bank 0, (0,0): 16×8 flyer
        pyxel.images[0].load(0, 0, "assets/img/flyer.png")
        # Sound 0: flyer spawn buzz (short descending triangle)
        pyxel.sounds[0].set("e3d3c3", "t", "543", "nnn", 10)
        # Sound 1: flyer shoot (noise burst with fadeout)
        pyxel.sounds[1].set("a4", "n", "7", "f", 5)
        # Declare attributes before _full_reset so they always exist
        self.seed = DEFAULT_SEED
        self.player = Player()
        self._full_reset(DEFAULT_SEED)
        pyxel.run(self.update, self.draw)

    def _full_reset(self, seed=DEFAULT_SEED):
        """Full game reset with a new seed: new world, fresh player, cleared state."""
        self.seed = seed
        random.seed(seed)
        # fmt: off
        self.world               = World(seed=seed)
        self.player              = Player()
        self.bullets             = []
        self.missile_bullets     = []
        self.canisters           = []
        self.cam_y               = 0.0
        # Pause / body-panel state
        self.body_grid           = [[None] * 5 for _ in range(5)]
        self.inventory           = []
        self.enemies             = []
        self.enemy_bullets       = []
        self.held                = None       # artifact being moved
        self.held_src            = None       # ("body", r, c) | ("inv", i)
        self.paused              = False
        self.pickup_dialogue     = None
        self.pause_panel         = 0          # 0 = body, 1 = inventory
        self.body_cursor         = [0, 0]
        self.inv_cursor          = 0
        self.hover_timer         = 0
        self.hover_key           = None
        # Missile subweapon state
        self.active_missile_idx  = 0
        # Debug menu state
        self.debug_open          = False
        self.debug_cursor        = 0
        # Death / respawn state
        self.dead                = False
        self.death_timer         = 0
        self.immortal            = False
        # Biome transition state
        self.current_biome_idx   = 0
        self.biome_banner_idx    = 0
        self.biome_banner_name   = ""
        self.biome_banner_timer  = 0
        self.biome_trigger_cd    = 0
        # fmt: on

    # ---- debug menu ----

    def _update_debug(self):
        n = len(DEBUG_ITEMS)
        if (
            pyxel.btnp(pyxel.KEY_UP)
            or pyxel.btnp(pyxel.KEY_K)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
        ):
            self.debug_cursor = (self.debug_cursor - 1) % n
        if (
            pyxel.btnp(pyxel.KEY_DOWN)
            or pyxel.btnp(pyxel.KEY_J)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
        ):
            self.debug_cursor = (self.debug_cursor + 1) % n
        if (
            pyxel.btnp(pyxel.KEY_Z)
            or pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)
        ):
            _, cls = DEBUG_ITEMS[self.debug_cursor]
            if isinstance(cls, _Restart):
                self._full_reset(cls.seed)
                return  # debug_open cleared by _full_reset
            elif cls is None:
                self.immortal = not self.immortal
            else:
                inv_hit = next((a for a in self.inventory if isinstance(a, cls)), None)
                bod_pos = next(
                    (
                        (r, c)
                        for r in range(5)
                        for c in range(5)
                        if isinstance(self.body_grid[r][c], cls)
                    ),
                    None,
                )
                if inv_hit:
                    self.inventory.remove(inv_hit)
                elif bod_pos:
                    r, c = bod_pos
                    self.body_grid[r][c] = None
                    self._sync_artifacts()
                else:
                    self.inventory.append(cls())
        if (
            pyxel.btnp(pyxel.KEY_ESCAPE)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START)
        ):
            self.debug_open = False

    def _draw_debug(self):
        p = self.player
        lines = len(DEBUG_ITEMS)
        pw = 150
        ph = 24 + lines * 10
        px0 = 4
        py0 = 4
        pyxel.rect(px0, py0, pw, ph, BLACK)
        pyxel.rectb(px0, py0, pw, ph, LIGHT_GRAY)
        pyxel.text(px0 + 4, py0 + 4, "-- DEBUG --", YELLOW)
        pyxel.text(px0 + 60, py0 + 4, "Z/A:toggle  Esc/B:close", DARK_GRAY)
        for i, (label, cls) in enumerate(DEBUG_ITEMS):
            cursor = ">" if i == self.debug_cursor else " "
            color  = YELLOW if i == self.debug_cursor else LIGHT_GRAY
            if isinstance(cls, _Restart):
                pyxel.text(px0 + 4, py0 + 14 + i * 10, f"{cursor} >>  {label}", color)
                continue
            if cls is None:
                has = self.immortal
            else:
                has = any(isinstance(a, cls) for a in self.inventory) or any(
                    isinstance(self.body_grid[r][c], cls)
                    for r in range(5)
                    for c in range(5)
                    if self.body_grid[r][c] is not None
                )
            marker = "[x]" if has else "[ ]"
            pyxel.text(px0 + 4, py0 + 14 + i * 10, f"{cursor} {marker} {label}", color)

    # ---- pause / body panel ----

    def _sync_artifacts(self):
        """Rebuild player.artifacts from body_grid; handle side-effects."""
        self.player.artifacts = [
            a for row in self.body_grid for a in row if a is not None
        ]
        if not any(isinstance(a, SpiralBorer) for a in self.player.artifacts):
            self.player.burrowing = False
            self.player.crouching = False

    # ---- pickup dialogue ----

    def _update_pickup_dialogue(self):
        if (
            pyxel.btnp(pyxel.KEY_Z)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)
            or pyxel.btnp(pyxel.KEY_RETURN)
        ):
            self.pickup_dialogue = None
            # Suppress the shoot that would fire next frame (btn vs btnp)
            self.player.shoot_cd = SHOOT_COOLDOWN
        elif pyxel.btnp(pyxel.KEY_TAB) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START):
            self.pickup_dialogue = None
            self.paused = True

    def _draw_pickup_dialogue(self, cls):
        pw, ph = 204, 92
        px0 = (SCREEN_W - pw) // 2
        py0 = (SCREEN_H - ph) // 2
        pyxel.rect(px0, py0, pw, ph, BLACK)
        pyxel.rectb(px0, py0, pw, ph, YELLOW)
        pyxel.text(px0 + 4, py0 + 5, "ARTIFACT FOUND", ORANGE)
        pyxel.line(px0 + 1, py0 + 14, px0 + pw - 2, py0 + 14, DARK_GRAY)
        pyxel.text(px0 + 4, py0 + 20, f"{cls.glyph}  {cls.name}", YELLOW)
        for i, ln in enumerate(self._wrap(cls.description, 46)[:3]):
            pyxel.text(px0 + 4, py0 + 34 + i * 10, ln, LIGHT_GRAY)
        pyxel.text(px0 + 4, py0 + ph - 19, "Z / X  dismiss", DARK_GRAY)
        pyxel.text(
            px0 + 4, py0 + ph - 10, "Tab / Start  open body to install", DARK_GRAY
        )

    # -- pick / place helpers --

    def _hovered_artifact(self):
        if self.held:
            return self.held
        if self.pause_panel == 0:
            r, c = self.body_cursor
            return self.body_grid[r][c]
        if self.inventory and self.inv_cursor < len(self.inventory):
            return self.inventory[self.inv_cursor]
        return None

    def _pickup_from_body(self, r, c):
        a = self.body_grid[r][c]
        if a is None:
            return
        self.body_grid[r][c] = None
        self.held = a
        self.held_src = ("body", r, c)
        self._sync_artifacts()

    def _pickup_from_inventory(self):
        if not self.inventory or self.inv_cursor >= len(self.inventory):
            return
        a = self.inventory.pop(self.inv_cursor)
        self.inv_cursor = min(self.inv_cursor, max(0, len(self.inventory) - 1))
        self.held = a
        self.held_src = ("inv", self.inv_cursor)

    def _place_on_body(self, r, c):
        other = self.body_grid[r][c]
        self.body_grid[r][c] = self.held
        if other is not None:
            self._return_to_src(other)
        self.held = None
        self.held_src = None
        self._sync_artifacts()

    def _place_in_inventory(self):
        idx = min(self.inv_cursor, len(self.inventory))
        self.inventory.insert(idx, self.held)
        self.held = None
        self.held_src = None

    def _cancel_hold(self):
        src, *pos = self.held_src
        if src == "body":
            r, c = pos
            self.body_grid[r][c] = self.held
            self._sync_artifacts()
        else:
            i = pos[0]
            self.inventory.insert(min(i, len(self.inventory)), self.held)
        self.held = None
        self.held_src = None

    def _return_to_src(self, artifact):
        """Send a displaced artifact back to where the held item came from."""
        src, *pos = self.held_src
        if src == "body":
            r, c = pos
            self.body_grid[r][c] = artifact
        else:
            i = pos[0]
            self.inventory.insert(min(i, len(self.inventory)), artifact)

    # -- update / draw --

    def _update_pause(self):
        # Tab / LB / RB: switch panels
        if (
            pyxel.btnp(pyxel.KEY_TAB)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_LEFTSHOULDER)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_RIGHTSHOULDER)
        ):
            self.pause_panel = 1 - self.pause_panel
            return

        # Escape / Start / B: cancel hold or close menu
        if (
            pyxel.btnp(pyxel.KEY_ESCAPE)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
        ):
            if self.held:
                self._cancel_hold()
            else:
                self.paused = False
            return

        up = (
            pyxel.btnp(pyxel.KEY_UP)
            or pyxel.btnp(pyxel.KEY_K)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
        )
        down = (
            pyxel.btnp(pyxel.KEY_DOWN)
            or pyxel.btnp(pyxel.KEY_J)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
        )
        left = (
            pyxel.btnp(pyxel.KEY_LEFT)
            or pyxel.btnp(pyxel.KEY_H)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
        )
        rght = (
            pyxel.btnp(pyxel.KEY_RIGHT)
            or pyxel.btnp(pyxel.KEY_L)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
        )
        act = (
            pyxel.btnp(pyxel.KEY_Z)
            or pyxel.btnp(pyxel.KEY_RETURN)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)
        )

        if self.pause_panel == 0:  # body grid
            r, c = self.body_cursor
            if up:
                r = max(0, r - 1)
            if down:
                r = min(4, r + 1)
            if left:
                c = max(0, c - 1)
            if rght:
                c = min(4, c + 1)
            self.body_cursor = [r, c]
            if act:
                if self.held:
                    self._place_on_body(r, c)
                else:
                    self._pickup_from_body(r, c)
        else:  # inventory list
            n = len(self.inventory)
            if up:
                self.inv_cursor = max(0, self.inv_cursor - 1)
            if down:
                self.inv_cursor = min(max(0, n - 1), self.inv_cursor + 1)
            if act:
                if self.held:
                    self._place_in_inventory()
                else:
                    self._pickup_from_inventory()

        # Hover-timer: reset whenever cursor lands on a different artifact
        hov = self._hovered_artifact()
        if hov is not self.hover_key:
            self.hover_key = hov
            self.hover_timer = 0
        else:
            self.hover_timer += 1

    def _draw_pause(self):
        pyxel.cls(BLACK)

        # Panel headers
        bc = YELLOW if self.pause_panel == 0 else LIGHT_GRAY
        ic = YELLOW if self.pause_panel == 1 else LIGHT_GRAY
        pyxel.text(_GX, 4, "BODY", bc)
        pyxel.text(_IX, 4, "INVENTORY", ic)
        pyxel.text(170, 4, "TAB:switch Esc:close", DARK_GRAY)
        pyxel.text(4, SCREEN_H - 8, f"seed:{self.seed}", DARK_GRAY)

        # Body grid
        for r in range(5):
            for c in range(5):
                x0 = _GX + c * _CELL
                y0 = _GY + r * _CELL
                is_cur = self.pause_panel == 0 and self.body_cursor == [r, c]
                a = self.body_grid[r][c]
                pyxel.rectb(
                    x0, y0, _CELL - 1, _CELL - 1, YELLOW if is_cur else DARK_GRAY
                )
                if is_cur and self.held:
                    pyxel.text(x0 + 3, y0 + 3, self.held.glyph, ORANGE)
                elif a:
                    pyxel.text(x0 + 3, y0 + 3, a.glyph, LIGHT_GRAY)

        # Synergy link: pulsing line between adjacent FractalBlaster ↔ Wallbreaker
        half = (_CELL - 1) // 2
        pulse = 0.4 + 0.6 * ((pyxel.frame_count // 8) % 2)
        for r, c, nr, nc in fractal_wallbreaker_pairs(self.body_grid):
            ax = _GX + c  * _CELL + half
            ay = _GY + r  * _CELL + half
            bx = _GX + nc * _CELL + half
            by = _GY + nr * _CELL + half
            pyxel.dither(pulse)
            pyxel.line(ax, ay, bx, by, 14)
            pyxel.dither(1.0)

        # "HOLDING" indicator below the grid
        if self.held:
            hy = _GY + 5 * _CELL + 3
            pyxel.text(_GX, hy, f"HOLD:{self.held.glyph} {self.held.name}", ORANGE)
            pyxel.text(_GX, hy + 9, "Z:place  Esc:cancel", DARK_GRAY)

        # Inventory list (scrolling)
        max_vis = (_TIPY - _IY - 2) // _IRH
        scroll = max(0, self.inv_cursor - max_vis + 1)
        if not self.inventory:
            pyxel.text(_IX, _IY, "(empty)", DARK_GRAY)
        for i, a in enumerate(self.inventory):
            vi = i - scroll
            if vi < 0 or vi >= max_vis:
                continue
            is_cur = self.pause_panel == 1 and self.inv_cursor == i
            col = YELLOW if is_cur else LIGHT_GRAY
            pre = ">" if is_cur else " "
            pyxel.text(_IX, _IY + vi * _IRH, f"{pre}{a.glyph} {a.name}", col)

        # Tooltip
        pyxel.line(0, _TIPY - 1, SCREEN_W - 1, _TIPY - 1, DARK_GRAY)
        hov = self._hovered_artifact()
        if hov:
            if self.held:
                pyxel.text(4, _TIPY + 2, f"HOLDING: {hov.name}", ORANGE)
            else:
                pyxel.text(4, _TIPY + 2, hov.name, YELLOW)
                if self.hover_timer >= _HOVER:
                    for i, ln in enumerate(self._wrap(hov.description, 55)[:2]):
                        pyxel.text(4, _TIPY + 12 + i * 10, ln, LIGHT_GRAY)
                else:
                    pyxel.text(4, _TIPY + 12, "...", DARK_GRAY)

    @staticmethod
    def _wrap(text, width):
        words, lines, line = text.split(), [], ""
        for w in words:
            candidate = (line + " " + w) if line else w
            if len(candidate) <= width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines

    # ---- input ----

    def _left(self):
        return (
            pyxel.btn(pyxel.KEY_LEFT)
            or pyxel.btn(pyxel.KEY_H)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
        )

    def _right(self):
        return (
            pyxel.btn(pyxel.KEY_RIGHT)
            or pyxel.btn(pyxel.KEY_L)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
        )

    def _up(self):
        return (
            pyxel.btn(pyxel.KEY_UP)
            or pyxel.btn(pyxel.KEY_K)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
        )

    def _down(self):
        return (
            pyxel.btn(pyxel.KEY_DOWN)
            or pyxel.btn(pyxel.KEY_J)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
        )

    def _jump(self):
        return (
            pyxel.btnp(pyxel.KEY_SPACE)
            or pyxel.btnp(pyxel.KEY_UP)
            or pyxel.btnp(pyxel.KEY_K)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)
        )

    def _jump_held(self):
        return (
            pyxel.btn(pyxel.KEY_SPACE)
            or pyxel.btn(pyxel.KEY_UP)
            or pyxel.btn(pyxel.KEY_K)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_A)
            or pyxel.btn(pyxel.GAMEPAD1_BUTTON_B)
        )

    def _shoot(self):
        return pyxel.btn(pyxel.KEY_Z) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_X)

    def _aim_lock(self):
        return pyxel.btn(pyxel.KEY_X) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_LEFTSHOULDER)

    def _missile_mode(self):
        return pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_RIGHTSHOULDER)

    def _select_btnp(self):
        return pyxel.btnp(pyxel.GAMEPAD1_BUTTON_BACK)

    def _maybe_drop_canister(self, e):
        if random.random() < CANISTER_DROP_CHANCE:
            self.canisters.append(MissileCanister(e.x, e.y))

    def _active_missile(self):
        missiles = [a for a in self.player.artifacts if isinstance(a, MissileArtifact)]
        if not missiles:
            return None
        return missiles[self.active_missile_idx % len(missiles)]

    # ---- physics ----

    def _occupied_rows(self, p):
        # Use tile-row arithmetic instead of float bottom so that a 2-tile-high
        # gap is always passable regardless of sub-pixel y drift during free fall.
        tr = int(p.y // TILE)
        ph_rows = 1 if p.crouching else P_H // TILE
        return range(tr, tr + ph_rows)

    def _try_ledge_grab(self, p, wall_col, blocking_row, wall_dir):
        """Grab when bottom tile hits wall but top tile is open."""
        if p.on_ground or p.state == "hanging" or p.ledge_cd > 0 or p.burrowing:
            return False
        top_row = int(p.y // TILE)
        if blocking_row == top_row + 1 and not self.world.solid(wall_col, top_row):
            # Don't grab a single-block obstacle sitting on solid ground.
            # If the floor exists at blocking_row+1 under the player's column,
            # this ledge is only 1 tile tall and the player can just walk past it.
            lc = int((p.x + P_HIT_INS) // TILE)
            rc = int((p.right - 1 - P_HIT_INS) // TILE)
            if self.world.solid(lc, blocking_row + 1) or self.world.solid(  # fmt: skip
                rc, blocking_row + 1
            ):
                return False
            p.state = "hanging"
            p.hang_wall = wall_dir
            p.y = float(top_row * TILE)
            p.x = float(
                (wall_col * TILE - P_W) if wall_dir == 1 else (wall_col + 1) * TILE
            )
            p.vx = 0.0
            p.vy = 0.0
            p.aim_dx = -wall_dir  # default: aim away from wall
            p.aim_dy = 0
            return True
        return False

    def _gap_snap(self, p, wall_col):
        """
        Nudge p.y by up to GAP_SNAP pixels (upward first) so the player aligns
        with a gap in wall_col that fits their full height.  Only snaps when the
        gap is framed by solid tiles above and below (rules out 1-tile steps).
        """
        if p.on_ground:
            return False  # walking on flat ground — don't auto-align
        GAP_SNAP = 6
        ph_rows = 1 if p.crouching else P_H // TILE
        for dy in range(1, GAP_SNAP + 1):
            for sign in (-1, 1):  # try up first (player usually falls below gap)
                tr = int((p.y + sign * dy) // TILE)
                if any(self.world.solid(wall_col, tr + i) for i in range(ph_rows)):
                    continue  # gap not clear at this offset
                # Require solid wall tiles framing the gap above and below
                if (self.world.solid(wall_col, tr - 1)
                        and self.world.solid(wall_col, tr + ph_rows)):
                    p.y += sign * dy
                    return True
        return False

    def _move_x(self, p):
        p.x += p.vx
        p.wall_contact = 0
        if p.vx < 0:
            lc = int(p.x // TILE)
            for row in self._occupied_rows(p):
                if self.world.solid(lc, row):
                    if self._try_ledge_grab(p, lc, row, -1):
                        return
                    if self._gap_snap(p, lc):
                        return
                    p.x = float((lc + 1) * TILE)
                    p.vx = 0.0
                    p.wall_contact = -1
                    break
        elif p.vx > 0:
            rc = int((p.right - 1) // TILE)
            for row in self._occupied_rows(p):
                if self.world.solid(rc, row):
                    if self._try_ledge_grab(p, rc, row, 1):
                        return
                    if self._gap_snap(p, rc):
                        return
                    p.x = float(rc * TILE - P_W)
                    p.vx = 0.0
                    p.wall_contact = 1
                    break
        # Hard clamp to world horizontal bounds
        if p.x < 0:
            p.x = 0.0
            p.vx = 0.0
            p.wall_contact = -1
        elif p.right > SCREEN_W:
            p.x = float(SCREEN_W - P_W)
            p.vx = 0.0
            p.wall_contact = 1

    def _move_y(self, p):
        p.y += p.vy
        p.on_ground = False
        if p.burrowing:
            return
        lc = int((p.x + P_HIT_INS) // TILE)
        rc = int((p.right - 1 - P_HIT_INS) // TILE)
        if p.vy < 0:
            tr = int(p.y // TILE)
            if self.world.solid(lc, tr) or self.world.solid(rc, tr):
                p.y = float((tr + 1) * TILE)
                p.vy = 0.0
        else:
            br = int(p.bottom // TILE)
            ph = TILE if p.crouching else P_H
            if self.world.solid(lc, br) or self.world.solid(rc, br):
                p.y = float(br * TILE - ph)
                p.vy = 0.0
                p.on_ground = True
                p.jump_type = "none"
            else:
                # Frozen enemies act as platforms
                pl = p.x + P_HIT_INS
                pr = p.right - P_HIT_INS
                for e in self.enemies:
                    if (
                        e.alive
                        and e.frozen_timer > 0
                        and pl < e.right
                        and pr > e.x
                        and e.y <= p.bottom < e.y + TILE
                    ):
                        p.y = e.y - ph
                        p.vy = 0.0
                        p.on_ground = True
                        p.jump_type = "none"
                        break

    def _probe_walls(self, p):
        """Detect passive wall contact (for wall jump without pressing into wall)."""
        if p.on_ground:
            p.wall_contact = 0
            return
        tr = int(p.y // TILE)
        br = int((p.bottom - 1) // TILE)
        lc = int(p.x // TILE) - 1
        rc = int(p.right // TILE)
        for row in range(tr, br + 1):
            if lc >= 0 and self.world.solid(lc, row):
                p.wall_contact = -1
                return
            if rc < COLS and self.world.solid(rc, row):
                p.wall_contact = 1
                return
        p.wall_contact = 0

    # ---- death / respawn ----

    def _respawn(self):
        p = self.player
        # fmt: off
        p.x          = float(SCREEN_W // 2 - P_W // 2)
        p.y          = float(TILE * 2)
        p.vx         = 0.0
        p.vy         = 0.0
        p.hp         = p.max_hp
        p.inv_cd     = 0
        p.state      = "normal"
        p.crouching  = False
        p.burrowing  = False
        p.climbing   = False
        p.on_ground  = False
        # fmt: on
        # fmt: off
        self.enemies         = []
        self.enemy_bullets   = []
        self.bullets         = []
        self.missile_bullets = []
        self.canisters       = []
        self.cam_y           = 0.0
        self.dead            = False
        self.death_timer     = 0
        # fmt: on

    # ---- update / draw ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        # Death screen
        if self.dead:
            if self.death_timer > 0:
                self.death_timer -= 1
            if self.death_timer == 0 and (
                pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_X)
            ):
                self._respawn()
            return

        # Pickup dialogue takes highest priority (freezes all gameplay)
        if self.pickup_dialogue is not None:
            self._update_pickup_dialogue()
            return

        # Pause takes input priority; Tab/Start opens it from gameplay
        if self.paused:
            self._update_pause()
            return

        # F1 debug menu (only when not paused)
        if pyxel.btnp(pyxel.KEY_F1):
            self.debug_open = not self.debug_open
            self.debug_cursor = 0
        if self.debug_open:
            self._update_debug()
            return

        # Tab / Start opens pause menu from gameplay
        if pyxel.btnp(pyxel.KEY_TAB) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START):
            self.paused = True
            return

        p = self.player
        adx = (-1 if self._left() else 0) + (1 if self._right() else 0)
        jump = self._jump()
        down_p = (
            pyxel.btnp(pyxel.KEY_DOWN)
            or pyxel.btnp(pyxel.KEY_J)
            or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
        )

        if p.shoot_cd > 0:
            p.shoot_cd -= 1
        if p.wj_cd_l > 0:
            p.wj_cd_l -= 1
        if p.wj_cd_r > 0:
            p.wj_cd_r -= 1
        if p.ledge_cd > 0:
            p.ledge_cd -= 1
        if p.inv_cd > 0:
            p.inv_cd -= 1

        inputs = {
            "left": self._left(),
            "right": self._right(),
            "up": self._up(),
            "down": self._down(),
            "jump": jump,
            "shoot": self._shoot(),
            "burrow": (pyxel.btn(pyxel.KEY_C) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_Y)),
        }
        for a in p.artifacts:
            a.on_frame(p, self.world, inputs)

        if p.state == "hanging":
            p.aim_locked = self._aim_lock()
            if p.aim_locked:
                # Aim is constrained to 5 directions: up, down, straight-away,
                # diag-up-away, diag-down-away (nothing toward/into the wall).
                free = -p.hang_wall
                ady = (-1 if self._up() else 0) + (1 if self._down() else 0)
                if adx != 0 or ady != 0:
                    p.aim_dx = free if adx == free else 0
                    p.aim_dy = ady
                if jump:
                    p.state = "normal"
                    p.ledge_cd = 6
                    p.vy = JUMP_VEL * 0.75
                    p.vx = p.hang_wall * MOVE_SPEED
            else:
                if self._up() or jump:
                    # Launch upward and inward to land on top of the ledge
                    p.state = "normal"
                    p.ledge_cd = 6
                    p.vy = JUMP_VEL * 0.75
                    p.vx = p.hang_wall * MOVE_SPEED
                elif self._down() or (adx != 0 and adx == -p.hang_wall):
                    p.state = "normal"
                    p.ledge_cd = 6
                    p.vy = 0.5
        elif p.climbing:
            # MechaspiderLegs wall-climb: 2D movement along wall, no gravity
            p.aim_locked = self._aim_lock()
            if jump:
                # Jump away from wall using stored wall side
                wall_side = next(
                    (a._wall_side for a in p.artifacts if isinstance(a, MechaspiderLegs)),
                    p.wall_contact,
                )
                p.climbing = False
                p.vy = WALL_JUMP_VEL
                p.vx = -wall_side * WALL_JUMP_HVX
                p.jump_type = "spin"
            elif p.aim_locked:
                # Freeze position; direction keys steer aim
                ady = (-1 if self._up() else 0) + (1 if self._down() else 0)
                if adx != 0 or ady != 0:
                    # No horizontal input → shoot straight up/down (aim_dx = 0)
                    p.aim_dx = adx if adx != 0 else (p.facing if ady == 0 else 0)
                    p.aim_dy = ady
                p.vx = 0.0
                p.vy = 0.0
            else:
                climb_dy = (-1 if self._up() else 0) + (1 if self._down() else 0)
                p.vy = climb_dy * CLIMB_SPEED
                p.vx = adx * MOVE_SPEED
                if adx != 0:
                    p.facing = adx
                p.aim_dx = p.facing
                p.aim_dy = climb_dy
                # Cache artifact for anchor checks
                _msl = next(
                    (a for a in p.artifacts if isinstance(a, MechaspiderLegs)), None
                )
                prev_x = p.x
                self._move_x(p)
                if _msl and not _msl._has_wall_grip(p):
                    p.x = prev_x
                    p.vx = 0.0
                prev_y = p.y
                self._move_y(p)
                if _msl and not _msl._has_wall_grip(p):
                    p.y = prev_y
                    p.vy = 0.0
                self._probe_walls(p)
                if p.on_ground:
                    p.climbing = False
        else:
            p.aim_locked = self._aim_lock()

            if p.crouching:
                # Any of these uncrouches (if headroom allows): move, up, jump, Down-toggle
                want_uncrouch = (
                    (adx != 0 and not p.aim_locked) or self._up() or jump or down_p
                )
                if want_uncrouch:
                    tr = int(p.y // TILE) - 1
                    lc = int((p.x + P_HIT_INS) // TILE)
                    rc = int((p.right - 1 - P_HIT_INS) // TILE)
                    if tr < 0 or not (
                        self.world.solid(lc, tr) or self.world.solid(rc, tr)
                    ):
                        p.y -= TILE
                        p.crouching = False
                        # Apply normal movement for this frame immediately
                        p.vx = adx * MOVE_SPEED
                        if adx != 0:
                            p.facing = adx
                        p.aim_dx = p.facing
                        p.aim_dy = -1 if (self._up() and adx != 0) else 0

                if p.crouching:
                    # Still crouching (ceiling blocked stand-up, or no trigger)
                    p.vx = 0.0
                    if self._left():
                        p.facing = -1
                    if self._right():
                        p.facing = 1
                    if p.aim_locked:
                        ady = (-1 if self._up() else 0) + (1 if self._down() else 0)
                        if adx != 0 or ady != 0:
                            p.aim_dx = adx
                            p.aim_dy = ady
                    else:
                        # No lock: shoot straight forward from the crouched position
                        p.aim_dx = p.facing
                        p.aim_dy = 0
            elif p.aim_locked:
                # Freeze horizontal movement; direction keys control aim
                p.vx = 0.0
                ady = (-1 if self._up() else 0) + (1 if self._down() else 0)
                if adx != 0 or ady != 0:
                    p.aim_dx = adx
                    p.aim_dy = ady
            else:
                # Straight jump: no air control until landing
                if p.jump_type == "straight" and not p.on_ground:
                    p.vx = 0.0
                else:
                    p.vx = adx * MOVE_SPEED
                if adx != 0:
                    p.facing = adx
                # Aim: facing + vertical modifier
                p.aim_dx = p.facing
                # fmt: off
                if self._up():
                    p.aim_dy = -1            # up: diagonal when running, straight up when standing
                    if adx == 0:
                        p.aim_dx = 0         # standing still → shoot straight up
                elif self._down() and (adx != 0 or not p.on_ground):
                    p.aim_dy = 1             # diagonal/straight down while running or airborne
                # fmt: on
                else:
                    p.aim_dy = 0
                # Toggle crouch on: Down press while stationary on ground, not burrowing
                if p.on_ground and down_p and adx == 0 and not p.burrowing:
                    p.y += TILE
                    p.crouching = True
                    p.vx = 0.0

            if (
                jump and not p.burrowing and not p.crouching
            ):  # crouching uncrouches above
                if p.on_ground:
                    p.vy = JUMP_VEL
                    p.on_ground = False
                    p.jump_type = "spin" if adx != 0 else "straight"
                    if p.jump_type == "straight":
                        p.vx = 0.0
                elif p.wall_contact != 0:
                    can = (p.wall_contact == -1 and p.wj_cd_l == 0) or (
                        p.wall_contact == 1 and p.wj_cd_r == 0
                    )
                    if can:
                        p.vy = WALL_JUMP_VEL
                        p.vx = -p.wall_contact * WALL_JUMP_HVX
                        p.jump_type = "spin"
                        if p.wall_contact == -1:
                            p.wj_cd_l = WALL_JUMP_CD
                        else:
                            p.wj_cd_r = WALL_JUMP_CD

            # Variable jump height: release jump early to cut the rise
            if p.vy < JUMP_VEL_MIN and not self._jump_held():
                p.vy = JUMP_VEL_MIN
            p.vy = min(p.vy + GRAVITY, MAX_FALL)
            self._move_x(p)
            self._move_y(p)
            if p.wall_contact == 0 and not p.burrowing:
                self._probe_walls(p)

        # Cycle active missile type (SELECT)
        if self._select_btnp():
            self.active_missile_idx += 1

        # Shoot
        if self._shoot() and p.shoot_cd == 0:
            dx, dy = p.aim_dx, p.aim_dy
            if dx == 0 and dy == 0:
                dx = p.facing
            if self._missile_mode():
                art = self._active_missile()
                if art and art.ammo > 0:
                    mb = MissileBullet(p.gun_x, p.gun_y, dx, dy)
                    for a in p.artifacts:
                        a.on_shoot(p, mb)
                    self.missile_bullets.append(mb)
                    art.ammo -= 1
                    p.shoot_cd = SHOOT_COOLDOWN
            else:
                fractal = next(
                    (a for a in p.artifacts if isinstance(a, FractalBlaster)), None
                )
                if fractal is not None:
                    b = FractalBullet(
                        p.gun_x, p.gun_y, dx, dy, fractal._cache, self.cam_y
                    )
                    b.synergy_wall_break = fractal_wallbreaker_active(self.body_grid)
                    fractal.bg_timer = FractalBlaster.BG_LIFETIME
                else:
                    b = Bullet(p.gun_x, p.gun_y, dx, dy)
                for a in p.artifacts:
                    a.on_shoot(p, b)
                self.bullets.append(b)
                p.shoot_cd = SHOOT_COOLDOWN

        splinters = []
        for b in self.bullets:
            b.update(self.world)
            if getattr(b, "pending_splinters", None):
                splinters.extend(b.pending_splinters)
                b.pending_splinters.clear()
        self.bullets.extend(splinters)

        for mb in self.missile_bullets:
            mb.update(self.world)

        # Player bullets vs enemies
        for b in self.bullets:
            if not b.alive:
                continue
            piercing = getattr(b, "piercing", False)
            hit_enemies = getattr(b, "hit_enemies", None)
            for e in self.enemies:
                if not e.alive:
                    continue
                if hit_enemies is not None and id(e) in hit_enemies:
                    continue
                if b.x < e.right and b.x + 2 > e.x and b.y < e.bottom and b.y + 2 > e.y:
                    e.take_damage(FractalBullet.DAMAGE if piercing else 1)
                    if not e.alive:
                        for a in p.artifacts:
                            a.on_kill(p)
                        self._maybe_drop_canister(e)
                    if piercing:
                        if hit_enemies is not None:
                            hit_enemies.add(id(e))
                    else:
                        b.alive = False
                        break

        # Missile bullets vs enemies — freeze on hit
        for mb in self.missile_bullets:
            if not mb.alive:
                continue
            for e in self.enemies:
                if e.alive and (
                    mb.x < e.right
                    and mb.x + 3 > e.x
                    and mb.y < e.bottom
                    and mb.y + 3 > e.y
                ):
                    e.take_damage(MissileBullet.DAMAGE)
                    e.frozen_timer = MissileBullet.FREEZE_FRAMES
                    if not e.alive:
                        for a in p.artifacts:
                            a.on_kill(p)
                        self._maybe_drop_canister(e)
                    mb.alive = False
                    break

        self.bullets = [b for b in self.bullets if b.alive]
        self.missile_bullets = [mb for mb in self.missile_bullets if mb.alive]

        # Drain world spawn queue
        for sx, sy, etype in self.world.pending_spawns:
            if etype == "crawler":
                self.enemies.append(Crawler(sx, sy))
            elif etype == "flyer":
                self.enemies.append(Flyer(sx, sy))
                if abs(sy - self.player.y) < 200:
                    pyxel.play(0, 0)
            elif etype == "shooty_flier":
                self.enemies.append(ShootyFlier(sx, sy))
                if abs(sy - self.player.y) < 200:
                    pyxel.play(0, 0)
        self.world.pending_spawns.clear()

        # Update enemies (frozen enemies skip AI/movement)
        for e in self.enemies:
            if e.alive:
                if e.frozen_timer > 0:
                    e.frozen_timer -= 1
                else:
                    e.update(self.world, p, self.enemy_bullets)

        # Update enemy bullets
        for eb in self.enemy_bullets:
            eb.update()

        # Damage player (enemy contact, then enemy bullets; one source per inv window)
        if p.inv_cd == 0 and not self.immortal:
            for e in self.enemies:
                if (
                    e.alive
                    and e.frozen_timer == 0
                    and (
                        p.x < e.right
                        and p.right > e.x
                        and p.y < e.bottom
                        and p.bottom > e.y
                    )
                ):
                    p.hp = max(0, p.hp - e.damage)
                    p.inv_cd = 60
                    break
            else:
                for eb in self.enemy_bullets:
                    if eb.alive and (
                        p.x < eb.x + 2
                        and p.right > eb.x
                        and p.y < eb.y + 2
                        and p.bottom > eb.y
                    ):
                        p.hp = max(0, p.hp - 1)
                        p.inv_cd = 60
                        eb.alive = False
                        break
            if p.hp == 0:
                self.dead = True
                self.death_timer = DEATH_HOLD

        # Pickup collection
        for pu in self.world.pickups:
            if not pu.collected and (
                p.x < pu.right
                and p.right > pu.x
                and p.y < pu.bottom
                and p.bottom > pu.y
            ):
                pu.collected = True
                self.inventory.append(pu.artifact_cls())
                self.pickup_dialogue = pu.artifact_cls
                break

        # Canister update and collection
        for c in self.canisters:
            c.update()
        for c in self.canisters:
            if c.alive and (
                p.x < c.right and p.right > c.x and p.y < c.bottom and p.bottom > c.y
            ):
                missiles = [a for a in p.artifacts if isinstance(a, MissileArtifact)]
                if missiles:
                    target = min(missiles, key=lambda a: a.ammo / a.max_ammo)
                    target.ammo = min(
                        target.ammo + MissileCanister.AMMO_AMOUNT, target.max_ammo
                    )
                c.alive = False
                break

        # Cull dead / off-screen-above objects
        cull_y = self.cam_y - SCREEN_H * 3
        self.enemies = [e for e in self.enemies if e.alive and e.y > cull_y]
        self.enemy_bullets = [
            eb for eb in self.enemy_bullets if eb.alive and eb.y > cull_y
        ]
        self.missile_bullets = [
            mb for mb in self.missile_bullets if mb.alive and mb.y > cull_y
        ]
        self.canisters = [c for c in self.canisters if c.alive and c.y > cull_y]
        self.world.pickups = [
            pu for pu in self.world.pickups if not pu.collected and pu.y > cull_y
        ]

        self.world.ensure_gen(int(p.bottom // TILE) + 40)

        target = p.y - SCREEN_H * 0.33
        self.cam_y += (target - self.cam_y) * 0.12
        self.cam_y = max(0.0, self.cam_y)

        # Biome transition detection
        biome_idx = biome_for_row(int(p.bottom // TILE))
        if biome_idx != self.current_biome_idx:
            self.current_biome_idx = biome_idx
            if self.biome_trigger_cd == 0:
                self.biome_banner_idx = biome_idx
                self.biome_banner_name = _BIOMES[biome_idx][0]
                self.biome_banner_timer = 240
                self.biome_trigger_cd = 300
        if self.biome_trigger_cd > 0:
            self.biome_trigger_cd -= 1
        if self.biome_banner_timer > 0:
            self.biome_banner_timer -= 1

    def _draw_biome_banner(self):
        name = self.biome_banner_name
        bw, bh = 120, 26
        bx = (SCREEN_W - bw) // 2
        by = (SCREEN_H - bh) // 2
        brd = _BIOMES[self.biome_banner_idx][3]  # wall_brd color
        pyxel.dither(0.5)
        pyxel.rect(bx, by, bw, bh, BLACK)
        pyxel.dither(1.0)
        pyxel.rectb(bx, by, bw, bh, brd)
        label = "ENTERING"
        pyxel.text(bx + (bw - len(label) * 4) // 2, by + 5, label, DARK_GRAY)
        pyxel.text(bx + (bw - len(name) * 4) // 2, by + 14, name, YELLOW)

    def _draw_death(self):
        pyxel.cls(BLACK)
        cx = SCREEN_W // 2
        cy = SCREEN_H // 2
        pyxel.text(cx - 21, cy - 8, "YOU DIED", ORANGE)
        if self.death_timer == 0:
            pyxel.text(cx - 30, cy + 4, "Z to continue", LIGHT_GRAY)

    def draw(self):
        if self.dead:
            self._draw_death()
            return
        if self.paused:
            self._draw_pause()
            return

        cam = self.cam_y
        cam_biome = biome_for_row(int((cam + SCREEN_H * 0.5) // TILE))
        pyxel.cls(_BIOMES[cam_biome][1])
        first = max(0, int(cam // TILE) - 1)
        last = first + (SCREEN_H // TILE) + 3

        for row in range(first, last):
            for col in range(COLS):
                ttype = self.world.tiles.get((col, row), 0)
                if ttype != 0:
                    sx = col * TILE
                    sy = int(row * TILE - cam)
                    _, _, wf, wb, cf, cb = _BIOMES[biome_for_row(row)]
                    if ttype == 2:  # cave rock
                        pyxel.rect(sx, sy, TILE, TILE, cf)
                        pyxel.rectb(sx, sy, TILE, TILE, cb)
                    else:  # platform / side wall (type 1)
                        pyxel.rect(sx, sy, TILE, TILE, wf)
                        pyxel.rectb(sx, sy, TILE, TILE, wb)

        # Fractal Blaster background overlay (dithered, drawn above tiles but below entities)
        for a in self.player.artifacts:
            if isinstance(a, FractalBlaster):
                a.draw_bg()
                break

        for b in self.bullets:
            b.draw(cam)

        for mb in self.missile_bullets:
            mb.draw(cam)

        for eb in self.enemy_bullets:
            eb.draw(cam)

        for e in self.enemies:
            e.draw(cam)

        for pu in self.world.pickups:
            pu.draw(cam)

        for c in self.canisters:
            c.draw(cam)

        p = self.player
        px = int(p.x)
        py = int(p.y - cam)

        # Vampiric Cape afterimage trail (drawn before player so player renders on top)
        for a in p.artifacts:
            if isinstance(a, VampiricCape):
                a.draw_trail(cam)
                break

        # MechaspiderLegs: draw procedural legs behind player
        for a in p.artifacts:
            if isinstance(a, MechaspiderLegs):
                a.draw_legs(p, cam)
                break

        # Blink player during invincibility frames
        if p.inv_cd > 0 and (pyxel.frame_count // 4) % 2:
            pass  # skip draw this frame
        elif p.state == "hanging":
            pyxel.text(px + 2, py + 1, "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "n", YELLOW)
        elif p.climbing:
            pyxel.text(px + 2, py + 1, "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "H", YELLOW)
        elif p.crouching:
            pyxel.text(px + 2, py + 1, "@", YELLOW)
        elif p.burrowing:
            pyxel.text(px + 2, py + 1, "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "v", YELLOW)
        elif not p.on_ground and p.jump_type == "straight":
            pyxel.text(px + 2, py + 1, "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "|", YELLOW)
        elif not p.on_ground and p.jump_type == "spin":
            body = "*" if (pyxel.frame_count // 4) % 2 else "o"
            pyxel.text(px + 2, py + 1, "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, body, YELLOW)
        else:
            pyxel.text(px + 2, py + 1, "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "W", YELLOW)

        # Aim reticle: orange box when aim-locked; cyan cross when missile mode
        missile_mode = self._missile_mode()
        if p.aim_locked or missile_mode:
            cx = int(p.gun_x)
            cy = int(p.gun_y - cam)
            rx = cx + p.aim_dx * 12
            ry = cy + p.aim_dy * 12
            if missile_mode:
                # Cyan targeting cross (7×7 with corner gaps)
                pyxel.rectb(rx - 3, ry - 3, 7, 7, 12)
                pyxel.line(rx, ry - 5, rx, ry - 4, 12)
                pyxel.line(rx, ry + 4, rx, ry + 5, 12)
                pyxel.line(rx - 5, ry, rx - 4, ry, 12)
                pyxel.line(rx + 4, ry, rx + 5, ry, 12)
            else:
                pyxel.rectb(rx - 2, ry - 2, 5, 5, ORANGE)

        # HP HUD — row of 4×4 blocks at bottom-left
        for i in range(p.max_hp):
            col = YELLOW if i < p.hp else DARK_GRAY
            pyxel.rect(4 + i * 5, SCREEN_H - 8, 4, 4, col)

        # Missile HUD — shown when a missile artifact is equipped
        art = self._active_missile()
        if art is not None:
            hud_col = YELLOW if self._missile_mode() else 12  # yellow when active
            hud_x = 4 + p.max_hp * 5 + 6
            pyxel.text(hud_x, SCREEN_H - 8, f"{art.glyph}:{art.ammo:02d}", hud_col)

        if self.biome_banner_timer > 0:
            self._draw_biome_banner()

        if self.pickup_dialogue is not None:
            self._draw_pickup_dialogue(self.pickup_dialogue)
        elif self.debug_open:
            self._draw_debug()


Game()

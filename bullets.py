import math
import random
import pyxel
# fmt: off
from constants import (
    TILE, SCREEN_H,
    BULLET_SPEED, SYNERGY_WALL_BREAK_CHANCE,
)
# fmt: on
ORANGE = 9


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
        self.synergy_ice_burst = False   # set True by RocketFin+IceMissile adjacency
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

    def spawn_ice_fragments(self):
        """Return 8 IceFragment instances fanning out from this missile's position."""
        frags = []
        for i in range(8):
            angle = math.tau * i / 8
            frags.append(IceFragment(self.x, self.y, angle))
        return frags


class IceFragment:
    """One shard from a RocketFin+IceMissile explosion — rotating fan of 8."""

    # fmt: off
    LIFETIME      = 60
    SPEED         = 2.5
    FREEZE_FRAMES = 180   # 3 s
    DAMAGE        = 1
    PHASE_FRAMES  = 6     # wall-phase grace period on spawn
    # fmt: on

    def __init__(self, x, y, angle):
        # fmt: off
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = math.cos(angle) * self.SPEED
        self.vy     = math.sin(angle) * self.SPEED
        self.life   = self.LIFETIME
        self.alive  = True
        self._angle = angle
        self._phase = self.PHASE_FRAMES
        # fmt: on

    def update(self, world):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        if self._phase > 0:
            self._phase -= 1
            return
        col, row = int(self.x // TILE), int(self.y // TILE)
        if world.solid(col, row):
            self.alive = False

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < SCREEN_H:
            # Alternate cyan/white to give sparkle effect
            col = 12 if (self.life % 4) < 2 else 7
            pyxel.pset(int(self.x), sy, col)
            pyxel.pset(int(self.x) + 1, sy, col)


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

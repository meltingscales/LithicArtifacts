"""
Enemy types and enemy-bullet class.

Each enemy's update(world, player, enemy_bullets) handles AI and physics.
Enemies append EnemyBullet instances to the shared enemy_bullets list when firing.
"""

import math
import random

import pyxel

_TILE           = 8      # mirror of TILE in main.py
_SCREEN_H       = 160    # mirror of SCREEN_H in main.py
_RED            = 8      # pyxel palette index
_GRAVITY        = 0.25
_MAX_FALL       = 2.0
_CRAWLER_SPEED  = 0.5
_FLYER_SPEED    = 0.6
_FLYER_AMP      = 18     # vertical oscillation amplitude (px)
_FLYER_FREQ     = 0.04   # radians per frame
_SHOOT_INTERVAL = 120    # frames between ShootyFlier shots
_SHOOT_RANGE    = 96     # px; ShootyFlier won't fire beyond this


# ---------------------------------------------------------------------------
# Projectile
# ---------------------------------------------------------------------------

class EnemyBullet:
    LIFETIME = 150
    SPEED    = 2.5

    def __init__(self, x, y, dx, dy):
        mag       = math.sqrt(dx * dx + dy * dy) or 1.0
        self.x    = float(x)
        self.y    = float(y)
        self.vx   = dx / mag * self.SPEED
        self.vy   = dy / mag * self.SPEED
        self.life = self.LIFETIME
        self.alive = True

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < _SCREEN_H:
            pyxel.rect(int(self.x), sy, 2, 2, _RED)


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class Enemy:
    glyph  = "?"
    color  = _RED

    def __init__(self, x, y, hp, damage):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = 0.0
        self.vy     = 0.0
        self.hp     = hp
        self.damage = damage
        self.alive  = True

    @property
    def right(self):  return self.x + _TILE
    @property
    def bottom(self): return self.y + _TILE

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def update(self, world, player, enemy_bullets):
        pass

    def draw(self, cam):
        sy = int(self.y - cam)
        if -_TILE <= sy < _SCREEN_H:
            pyxel.text(int(self.x) + 2, sy + 1, self.glyph, self.color)


# ---------------------------------------------------------------------------
# Crawler
# ---------------------------------------------------------------------------

class Crawler(Enemy):
    """Walks back and forth on platforms; turns at walls and ledge edges."""
    glyph = "c"

    def __init__(self, x, y):
        super().__init__(x, y, hp=2, damage=1)
        self.vx = random.choice([-1, 1]) * _CRAWLER_SPEED

    def _move_x(self, world):
        self.x += self.vx
        lc   = int(self.x // _TILE)
        rc   = int((self.right - 1) // _TILE)
        rows = range(int(self.y // _TILE), int((self.bottom - 1) // _TILE) + 1)
        if self.vx > 0:
            if any(world.solid(rc, r) for r in rows):
                self.x  = float(rc * _TILE - _TILE)
                self.vx = -self.vx
        elif self.vx < 0:
            if any(world.solid(lc, r) for r in rows):
                self.x  = float((lc + 1) * _TILE)
                self.vx = -self.vx

    def _move_y(self, world):
        """Returns True when landing on ground."""
        self.y += self.vy
        lc = int(self.x // _TILE)
        rc = int((self.right - 1) // _TILE)
        if self.vy < 0:
            tr = int(self.y // _TILE)
            if world.solid(lc, tr) or world.solid(rc, tr):
                self.y  = float((tr + 1) * _TILE)
                self.vy = 0.0
                return False
        else:
            br = int((self.bottom - 1) // _TILE)
            if world.solid(lc, br) or world.solid(rc, br):
                self.y  = float(br * _TILE - _TILE)
                self.vy = 0.0
                return True
        return False

    def update(self, world, player, enemy_bullets):
        self.vy = min(self.vy + _GRAVITY, _MAX_FALL)
        self._move_x(world)
        on_ground = self._move_y(world)
        if on_ground:
            floor_row = int(self.bottom // _TILE)
            if self.vx > 0:
                if not world.solid(int(self.right // _TILE), floor_row):
                    self.vx = -self.vx
            elif self.vx < 0:
                if not world.solid(int(self.x // _TILE) - 1, floor_row):
                    self.vx = -self.vx


# ---------------------------------------------------------------------------
# Flyer
# ---------------------------------------------------------------------------

class Flyer(Enemy):
    """Drifts toward the player horizontally with a sinusoidal vertical bob."""
    glyph = "f"

    def __init__(self, x, y):
        super().__init__(x, y, hp=3, damage=1)
        self.base_y = float(y)
        self.t      = 0
        self.phase  = random.uniform(0.0, math.pi * 2)

    def update(self, world, player, enemy_bullets):
        self.t += 1
        # Drift toward player
        dx      = (player.x + _TILE / 2) - (self.x + _TILE / 2)
        self.vx = max(-_FLYER_SPEED, min(_FLYER_SPEED, dx * 0.04))
        self.x += self.vx
        # Sinusoidal bob around spawn height
        self.y = self.base_y + math.sin(self.t * _FLYER_FREQ + self.phase) * _FLYER_AMP


# ---------------------------------------------------------------------------
# ShootyFlier
# ---------------------------------------------------------------------------

class ShootyFlier(Flyer):
    """Flyer that periodically fires at the player when within range."""
    glyph = "F"

    def __init__(self, x, y):
        super().__init__(x, y)
        self.shoot_cd = random.randint(30, _SHOOT_INTERVAL)

    def update(self, world, player, enemy_bullets):
        super().update(world, player, enemy_bullets)
        self.shoot_cd -= 1
        if self.shoot_cd <= 0:
            self.shoot_cd = _SHOOT_INTERVAL
            dx = (player.x + _TILE / 2) - (self.x + _TILE / 2)
            dy = (player.y + _TILE)     - (self.y + _TILE / 2)
            if math.sqrt(dx * dx + dy * dy) <= _SHOOT_RANGE:
                enemy_bullets.append(EnemyBullet(
                    self.x + _TILE / 2, self.y + _TILE / 2, dx, dy
                ))

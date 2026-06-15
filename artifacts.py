"""
Artifact base class and all artifact implementations.

Artifacts are passive/active body modifications carried in player.artifacts.
Each frame, Game calls artifact.on_frame(player, world, inputs) for every
equipped artifact. Other hooks fire on specific events.
"""

import math
import random
from collections import deque

import pyxel

# fmt: off
_TILE      = 8     # mirror of TILE in main.py
_SCREEN_H  = 160   # mirror of SCREEN_H
# fmt: on


class Artifact:
    # fmt: off
    name        = ""
    glyph       = "?"
    description = ""
    # fmt: on

    def on_frame(self, player, world, inputs):
        """Called once per frame.
        inputs: dict with bool keys left/right/up/down/jump/shoot."""
        pass

    def on_shoot(self, player, bullet):
        """Called when the player fires; may modify bullet in place."""
        pass

    def on_kill(self, player):
        """Called when one of the player's bullets kills an enemy."""
        pass

    def on_land(self, player):
        """Called when the player touches ground."""
        pass


class Wallbreaker(Artifact):
    """Shots destroy solid tiles on impact."""

    # fmt: off
    name        = "Wallbreaker"
    glyph       = "W"
    description = "Your shots punch through solid walls, destroying tiles on impact."
    # fmt: on

    def on_shoot(self, player, bullet):
        bullet.can_break_walls = True


class SpiralBorer(Artifact):
    """Phase downward through solid floors without destroying them.
    Entering is a commitment — burrowing ends only when you emerge below."""

    # fmt: off
    name        = "Spiral Borer"
    glyph       = "B"
    description = ("Phase through solid floors without destroying them.")
    # fmt: on

    def on_frame(self, player, world, inputs):
        if player.burrowing:
            if self._emerged(player, world):
                player.burrowing = False
        elif player.on_ground and player.crouching and inputs["burrow"]:
            player.burrowing = True
            player.on_ground = False
            player.vy = 1.0  # seed downward velocity into the floor

    @staticmethod
    def _emerged(player, world):
        """True when the tile row at the player's feet is fully open."""
        br = int(player.bottom // _TILE)
        lc = int(player.x // _TILE)
        rc = int((player.right - 1) // _TILE)
        return not world.solid(lc, br) and not world.solid(rc, br)


class MissileArtifact(Artifact):
    """Base for missile-type subweapons. Tracks ammo; fired via missile mode (hold RB)."""

    # fmt: off
    ammo     = 0
    max_ammo = 0
    # fmt: on


class IceMissile(MissileArtifact):
    """Freezing missiles: 2 damage, freeze 5 s on hit, limited ammo."""

    # fmt: off
    name        = "Ice Missiles"
    glyph       = "~"
    description = ("Fires freezing missiles (hold RB+Z). "
                   "Limited ammo.")
    MAX_AMMO    = 30
    # fmt: on

    def __init__(self):
        self.ammo = 10
        self.max_ammo = self.MAX_AMMO


class VampiricCape(Artifact):
    """Leave a ghostly afterimage trail while moving; kills have a 1-in-3
    chance to restore 1 HP."""

    # fmt: off
    name        = "Vampiric Cape"
    glyph       = "V"
    description = ("A spectral cape that drinks the life from fallen foes.")
    # fmt: on

    # Pyxel color indices, oldest ghost → newest ghost (8 steps)
    # fmt: off
    _TRAIL_COLORS = (1, 1, 2, 2, 13, 13, 5, 6)
    # fmt: on

    def __init__(self):
        # Circular buffer of (x, y) positions; oldest at index 0
        self._trail: deque = deque(maxlen=8)
        self._tick = 0  # frame counter for trail sample rate
        self._decay_cd = 0  # frames until next oldest-ghost removal

    def on_frame(self, player, world, inputs):
        self._tick += 1
        moving = abs(player.vx) > 0.1 or abs(player.vy) > 0.5
        if moving:
            self._decay_cd = 20  # reset grace period while moving
            if self._tick % 3 == 0:
                self._trail.append((player.x, player.y))
        else:
            if self._decay_cd > 0:
                self._decay_cd -= 1
            elif self._trail:
                self._trail.popleft()  # drop oldest ghost
                self._decay_cd = 12  # pace between removals

    def on_kill(self, player):
        if random.random() < 1 / 3:
            player.hp = min(player.hp + 1, player.max_hp)

    def draw_trail(self, cam):
        """Draw ghostly afterimages behind the player. Call before player draw."""
        positions = list(self._trail)  # index 0 = oldest
        for i, (tx, ty) in enumerate(positions):
            sy = int(ty - cam)
            if -_TILE <= sy < _SCREEN_H:
                col = self._TRAIL_COLORS[min(i, len(self._TRAIL_COLORS) - 1)]
                pyxel.text(int(tx) + 2, sy + 1, "@", col)
                pyxel.text(int(tx) + 2, sy + _TILE + 1, "W", col)


class FractalBlaster(Artifact):
    """Piercing shots that weave through space. Firing briefly reveals a fractal vision."""

    # fmt: off
    name        = "Fractal Blaster"
    glyph       = "J"
    description = "Shots pierce through enemies and weave through the air. Firing briefly tears a rift in space."
    BG_LIFETIME = 180

    _C_RE_BASE = -0.4;  _C_RE_AMP = 0.3;  _C_RE_FREQ = 0.003
    _C_IM_BASE =  0.6;  _C_IM_AMP = 0.2;  _C_IM_FREQ = 0.002
    # fmt: on

    def __init__(self):
        # fmt: off
        self._t          = 0
        self.bg_timer    = 0
        self.c_re        = self._C_RE_BASE
        self.c_im        = self._C_IM_BASE
        self._cache      = None
        self._cache_tick = -999
        # fmt: on

    def on_frame(self, player, world, inputs):
        self._t += 1
        self.c_re = (
            self._C_RE_BASE + math.sin(self._t * self._C_RE_FREQ) * self._C_RE_AMP
        )
        self.c_im = (
            self._C_IM_BASE + math.cos(self._t * self._C_IM_FREQ) * self._C_IM_AMP
        )
        if self.bg_timer > 0:
            self.bg_timer -= 1

    def draw_bg(self):
        if self.bg_timer <= 0:
            return
        import numpy as np

        if self._cache is None or (self._t - self._cache_tick) >= 3:
            W, H, MAX_ITER = 30, 20, 20
            re = np.linspace(-1.5, 1.5, W)
            im = np.linspace(-1.0, 1.0, H)
            zr, zi = np.meshgrid(re, im)
            iters = np.full((H, W), MAX_ITER, dtype=np.int32)
            mask = np.ones((H, W), dtype=bool)
            with np.errstate(over="ignore", invalid="ignore"):
                for n in range(MAX_ITER):
                    zr2, zi2 = zr * zr, zi * zi
                    escaped = mask & (zr2 + zi2 > 4.0)
                    iters[escaped] = n
                    mask &= ~escaped
                    zi_new = 2 * zr * zi + self.c_im
                    zr = zr2 - zi2 + self.c_re
                    zi = zi_new
            self._cache = iters
            self._cache_tick = self._t

        alpha = min(self.bg_timer / self.BG_LIFETIME, 0.5)
        pyxel.dither(alpha)
        S = 8
        for ry in range(20):
            for rx in range(30):
                n = int(self._cache[ry, rx])
                if n == 20:  # in-set: dark purple
                    pyxel.rect(rx * S, ry * S, S, S, 2)
                elif n >= 13:  # near-boundary: navy
                    pyxel.rect(rx * S, ry * S, S, S, 1)
        pyxel.dither(1.0)

"""
Artifact base class and all artifact implementations.

Artifacts are passive/active body modifications carried in player.artifacts.
Each frame, Game calls artifact.on_frame(player, world, inputs) for every
equipped artifact. Other hooks fire on specific events.
"""

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
    description = ("Phase through solid floors without destroying them. "
                   "Commitment — burrowing ends only when you emerge below.")
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
                   "Hits freeze enemies for 5 s and deal 2 damage. "
                   "Limited ammo.")
    MAX_AMMO    = 30
    # fmt: on

    def __init__(self):
        self.ammo     = 10
        self.max_ammo = self.MAX_AMMO


class VampiricCape(Artifact):
    """Leave a ghostly afterimage trail while moving; kills have a 1-in-3
    chance to restore 1 HP."""

    # fmt: off
    name        = "Vampiric Cape"
    glyph       = "V"
    description = ("A cape that drinks the life from fallen foes (1-in-3 chance "
                   "to heal 1 HP on kill) and leaves a spectral trail as you move.")
    # fmt: on

    # Pyxel color indices, oldest ghost → newest ghost (8 steps)
    # fmt: off
    _TRAIL_COLORS = (1, 1, 2, 2, 13, 13, 5, 6)
    # fmt: on

    def __init__(self):
        # Circular buffer of (x, y) positions; oldest at index 0
        self._trail: deque = deque(maxlen=8)
        self._tick = 0  # frame counter for trail sample rate

    def on_frame(self, player, world, inputs):
        self._tick += 1
        moving = abs(player.vx) > 0.1 or abs(player.vy) > 0.5
        if moving and self._tick % 3 == 0:
            self._trail.append((player.x, player.y))

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

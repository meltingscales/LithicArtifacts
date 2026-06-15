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
from constants import TILE as _TILE, SCREEN_H as _SCREEN_H, ICE_MISSILE_MAX_AMMO
# fmt: on

_P_H = _TILE * 2   # player height in pixels (2 tiles)


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
    MAX_AMMO    = ICE_MISSILE_MAX_AMMO
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


class MechaspiderLegs(Artifact):
    """Eight mechanical legs that grip walls, letting the player crawl in any direction."""

    # fmt: off
    name        = "Mechaspider Legs"
    glyph       = "M"
    description = "Eight mechanical legs sprout from your sides. Walls become footholds."
    # fmt: on

    # fmt: off
    _N_LEGS      = 8
    _LEG_REACH   = 4    # tile radius searched for nearest anchor tile face
    _STEP_DIST   = 4    # px (2D) foot displacement before replanting
    _STEP_FRAMES = 10   # frames to complete one step animation
    _ELBOW_OUT   = 5    # px elbow bulge away from body center
    # fmt: on

    def __init__(self):
        # fmt: off
        self._feet       = [(0.0, 0.0)] * self._N_LEGS
        self._step_timer = [0]          * self._N_LEGS
        self._step_from  = [(0.0, 0.0)] * self._N_LEGS
        self._step_to    = [(0.0, 0.0)] * self._N_LEGS
        self._tick       = 0
        self._wall_side  = 1   # 1=right, -1=left; set on grip
        # fmt: on

    # ---- helpers ----

    def _preferred_y(self, player, i):
        """World-space Y for leg i's shoulder, spread across player height ±4 px."""
        return player.y + (i / (self._N_LEGS - 1)) * (_P_H + 8) - 4

    def _preferred_foot(self, player, i):
        """Preferred world-space foot position: one tile out on wall side, at leg height."""
        ws = self._wall_side
        px = (player.right + _TILE * 0.5) if ws == 1 else (player.x - _TILE * 0.5)
        return px, self._preferred_y(player, i)

    def _find_anchor(self, player, world, preferred_y):
        """Nearest solid tile face to preferred foot, within _LEG_REACH radius.

        Searches all tiles in a square around the preferred foot position and
        tests all 4 face-center points per tile. Handles rough / cave surfaces.
        """
        pref_x = (player.right + _TILE * 0.5) if self._wall_side == 1 else (player.x - _TILE * 0.5)

        pcol = int(pref_x // _TILE)
        prow = int(preferred_y // _TILE)
        R = self._LEG_REACH + 1

        best = None
        best_dist = float("inf")
        for dc in range(-R, R + 1):
            for dr in range(-R, R + 1):
                c, r = pcol + dc, prow + dr
                if not world.solid(c, r):
                    continue
                x0, y0, hT = c * _TILE, r * _TILE, _TILE * 0.5
                for fx, fy in (
                    (x0,          y0 + hT),   # left face
                    (x0 + _TILE,  y0 + hT),   # right face
                    (x0 + hT,     y0),         # top face
                    (x0 + hT,     y0 + _TILE), # bottom face
                ):
                    dist = math.sqrt((fx - pref_x) ** 2 + (fy - preferred_y) ** 2)
                    if dist < best_dist:
                        best_dist = dist
                        best = (fx, fy)
        return best

    def _has_wall_grip(self, player, world):
        """True if any solid tile exists within leg reach on the wall side.

        Searches only columns in the wall direction — prevents ceiling/floor tiles
        from counting as a grip when the player has drifted far from the wall.
        """
        ws = self._wall_side
        if ws == 1:
            base_col = int(player.right // _TILE)
        else:
            base_col = int(player.x // _TILE) - 1
        prow = int((player.y + _P_H * 0.5) // _TILE)
        R = self._LEG_REACH + 1
        for dc in range(R):
            c = base_col + dc * ws
            for dr in range(-R, R + 1):
                if world.solid(c, prow + dr):
                    return True
        return False

    def _init_feet(self, player, world):
        self._wall_side = player.wall_contact
        for i in range(self._N_LEGS):
            py = self._preferred_y(player, i)
            anchor = self._find_anchor(player, world, py)
            if anchor:
                self._feet[i] = anchor
            else:
                bx = float(player.x + _TILE) if self._wall_side == 1 else float(player.x)
                self._feet[i] = (bx, py)

    # ---- on_frame ----

    def on_frame(self, player, world, inputs):
        self._tick += 1

        if not player.climbing and player.wall_contact != 0 and not player.on_ground:
            wd = player.wall_contact
            pressing = (wd == 1 and inputs["right"]) or (wd == -1 and inputs["left"])
            if pressing:
                player.climbing = True
                self._init_feet(player, world)

        if player.climbing:
            self._update_feet(player, world)

    def _update_feet(self, player, world):
        wall_out = -self._wall_side
        for i in range(self._N_LEGS):
            pref_x, pref_y = self._preferred_foot(player, i)
            fx, fy = self._feet[i]

            # Mid-step: interpolate; cancel early if target became stale
            if self._step_timer[i] > 0:
                tx, ty = self._step_to[i]
                stale = math.sqrt((tx - pref_x) ** 2 + (ty - pref_y) ** 2) > self._STEP_DIST * 2
                if stale:
                    self._step_timer[i] = 0   # fall through to replant below
                else:
                    self._step_timer[i] -= 1
                    t = 1.0 - self._step_timer[i] / self._STEP_FRAMES
                    fx0, fy0 = self._step_from[i]
                    arc = math.sin(t * math.pi) * 3
                    self._feet[i] = (
                        fx0 + (tx - fx0) * t + arc * wall_out,
                        fy0 + (ty - fy0) * t,
                    )
                    continue

            # Replant when 2D foot distance exceeds threshold
            foot_dist = math.sqrt((fx - pref_x) ** 2 + (fy - pref_y) ** 2)
            if foot_dist >= self._STEP_DIST:
                anchor = self._find_anchor(player, world, pref_y)
                if anchor:
                    self._step_from[i] = (fx, fy)
                    self._step_to[i] = anchor
                    self._step_timer[i] = self._STEP_FRAMES

    # ---- draw ----

    def draw_legs(self, player, cam):
        if not player.climbing:
            return
        # fmt: off
        _LEG_COLS = (5, 13, 5, 13, 5, 13, 5, 13)
        # fmt: on
        body_sx = player.x + _TILE * 0.5          # body center x (screen = world, no h-cam)
        body_sy = player.y + _P_H * 0.5 - cam     # body center y (screen space)

        for i in range(self._N_LEGS):
            sy_world = self._preferred_y(player, i)
            shoulder_sx = int(player.x + _TILE - 1) if self._wall_side == 1 else int(player.x + 1)
            shoulder_sy = int(sy_world - cam)

            fx, fy = self._feet[i]
            foot_sx = int(fx)
            foot_sy = int(fy - cam)

            # Elbow: midpoint + outward bulge away from body center
            mid_sx = (shoulder_sx + foot_sx) * 0.5
            mid_sy = (shoulder_sy + foot_sy) * 0.5
            out_x = mid_sx - body_sx
            out_y = mid_sy - body_sy
            out_len = math.sqrt(out_x ** 2 + out_y ** 2) or 1.0
            knee_sx = int(mid_sx + out_x / out_len * self._ELBOW_OUT)
            knee_sy = int(mid_sy + out_y / out_len * self._ELBOW_OUT)

            col = _LEG_COLS[i]
            pyxel.line(shoulder_sx, shoulder_sy, knee_sx, knee_sy, col)
            pyxel.line(knee_sx, knee_sy, foot_sx, foot_sy, col)
            pyxel.pset(foot_sx, foot_sy, 6)


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

import pyxel
# fmt: off
from constants import TILE, SCREEN_H
# fmt: on
# fmt: off
YELLOW = 10
ORANGE = 9
# fmt: on


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

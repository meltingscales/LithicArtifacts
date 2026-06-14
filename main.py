import pyxel
import random

SCREEN_W = 240
SCREEN_H = 160
TILE     = 8
COLS     = SCREEN_W // TILE   # 30

BLACK      = 0
DARK_GRAY  = 5
LIGHT_GRAY = 6
YELLOW     = 10

GRAVITY    = 0.25
MAX_FALL   = 4.0
MOVE_SPEED = 1.5
JUMP_VEL   = -4.5

P_W = TILE      # 8px  (1 tile wide)
P_H = TILE * 2  # 16px (2 tiles tall)


class World:
    def __init__(self, seed=0):
        self.tiles  = {}
        self.rng    = random.Random(seed)
        self._gen_to = -1
        self._gen(80)

    def _gen(self, up_to):
        for y in range(self._gen_to + 1, up_to + 1):
            self.tiles[(0, y)]        = 1
            self.tiles[(COLS - 1, y)] = 1
            if y == 0:
                for x in range(COLS):
                    self.tiles[(x, y)] = 1
            elif y == 8:
                # First platform with one gap
                gap = self.rng.randint(5, COLS - 10)
                for x in range(1, COLS - 1):
                    if not (gap <= x < gap + 5):
                        self.tiles[(x, y)] = 1
            elif y > 14 and self.rng.random() < 0.12:
                gap   = self.rng.randint(2, COLS - 9)
                gap_w = self.rng.randint(4, 8)
                for x in range(1, COLS - 1):
                    if not (gap <= x < gap + gap_w):
                        self.tiles[(x, y)] = 1
        self._gen_to = up_to

    def ensure_gen(self, row):
        if row > self._gen_to:
            self._gen(row + 40)

    def solid(self, col, row):
        return self.tiles.get((int(col), int(row)), 0) == 1


class Player:
    def __init__(self):
        self.x  = float(SCREEN_W // 2 - P_W // 2)
        self.y  = float(TILE * 2)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False

    @property
    def right(self):  return self.x + P_W
    @property
    def bottom(self): return self.y + P_H


class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Lithic Artifacts", fps=60)
        self.world  = World(seed=42)
        self.player = Player()
        self.cam_y  = 0.0
        pyxel.run(self.update, self.draw)

    # ---- input ----

    def _left(self):
        return (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_H) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT))

    def _right(self):
        return (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_L) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT))

    def _jump(self):
        return (pyxel.btnp(pyxel.KEY_SPACE)              or
                pyxel.btnp(pyxel.KEY_UP)                 or
                pyxel.btnp(pyxel.KEY_K)                  or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)      or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP))

    # ---- physics ----

    def _occupied_rows(self, p):
        """All tile rows the player currently overlaps (for X collision checks)."""
        return range(int(p.y // TILE), int((p.y + P_H - 1) // TILE) + 1)

    def _move_x(self, p):
        p.x += p.vx
        if p.vx < 0:
            lc = int(p.x // TILE)
            for row in self._occupied_rows(p):
                if self.world.solid(lc, row):
                    p.x  = (lc + 1) * TILE
                    p.vx = 0
                    break
        elif p.vx > 0:
            rc = int((p.right - 1) // TILE)
            for row in self._occupied_rows(p):
                if self.world.solid(rc, row):
                    p.x  = rc * TILE - P_W
                    p.vx = 0
                    break

    def _move_y(self, p):
        p.y += p.vy
        p.on_ground = False
        lc = int(p.x // TILE)
        rc = int((p.right - 1) // TILE)
        if p.vy < 0:
            tr = int(p.y // TILE)
            if self.world.solid(lc, tr) or self.world.solid(rc, tr):
                p.y  = (tr + 1) * TILE
                p.vy = 0
        else:
            # Use p.bottom (exclusive) so the player rests stably on the tile above
            br = int(p.bottom // TILE)
            if self.world.solid(lc, br) or self.world.solid(rc, br):
                p.y  = br * TILE - P_H
                p.vy = 0
                p.on_ground = True

    # ---- update / draw ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        p = self.player
        p.vx = 0.0
        if self._left():  p.vx = -MOVE_SPEED
        if self._right(): p.vx =  MOVE_SPEED
        if self._jump() and p.on_ground:
            p.vy = JUMP_VEL

        p.vy = min(p.vy + GRAVITY, MAX_FALL)
        self._move_x(p)
        self._move_y(p)

        self.world.ensure_gen(int(p.bottom // TILE) + 40)

        # Camera smoothly tracks player, biased toward showing what's below
        target     = p.y - SCREEN_H * 0.33
        self.cam_y += (target - self.cam_y) * 0.12
        self.cam_y  = max(0.0, self.cam_y)

    def draw(self):
        pyxel.cls(BLACK)
        cam   = self.cam_y
        first = max(0, int(cam // TILE) - 1)
        last  = first + (SCREEN_H // TILE) + 3

        for row in range(first, last):
            for col in range(COLS):
                if self.world.solid(col, row):
                    sx = col * TILE
                    sy = int(row * TILE - cam)
                    pyxel.rect(sx, sy, TILE, TILE, DARK_GRAY)
                    pyxel.rectb(sx, sy, TILE, TILE, LIGHT_GRAY)

        px = int(self.player.x)
        py = int(self.player.y - cam)
        pyxel.text(px + 2, py + 1,        "@", YELLOW)   # head
        pyxel.text(px + 2, py + TILE + 1, "W", YELLOW)   # legs


Game()

import math
import pyxel
import random

SCREEN_W = 240
SCREEN_H = 160
TILE     = 8
COLS     = SCREEN_W // TILE

BLACK      = 0
DARK_GRAY  = 5
LIGHT_GRAY = 6
YELLOW     = 10
ORANGE     = 9

GRAVITY       = 0.25
MAX_FALL      = 4.0
MOVE_SPEED    = 1.5
JUMP_VEL      = -4.5
WALL_JUMP_VEL = -4.0
WALL_JUMP_HVX = 2.0
WALL_JUMP_CD  = 24    # frames before same-side wall jump allowed again

BULLET_SPEED   = 5.0
SHOOT_COOLDOWN = 12

P_W       = TILE
P_H       = TILE * 2
P_HIT_INS = 1       # horizontal inset for floor/ceiling checks; lets player slip into 1-tile gaps


class World:
    def __init__(self, seed=0):
        self.tiles   = {}
        self.rng     = random.Random(seed)
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

    def destroy(self, col, row):
        self.tiles.pop((int(col), int(row)), None)


class Bullet:
    LIFETIME = 90

    def __init__(self, x, y, dx, dy):
        mag = math.sqrt(dx * dx + dy * dy)
        self.x     = float(x)
        self.y     = float(y)
        self.vx    = dx / mag * BULLET_SPEED
        self.vy    = dy / mag * BULLET_SPEED
        self.life  = self.LIFETIME
        self.alive = True

    def update(self, world):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        if world.solid(int(self.x // TILE), int(self.y // TILE)):
            world.destroy(int(self.x // TILE), int(self.y // TILE))
            self.alive = False

    def draw(self, cam):
        sy = int(self.y - cam)
        if 0 <= sy < SCREEN_H:
            pyxel.rect(int(self.x), sy, 2, 2, ORANGE)


class Player:
    def __init__(self):
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

    @property
    def right(self):  return self.x + P_W
    @property
    def bottom(self): return self.y + P_H
    @property
    def gun_x(self):  return self.x + P_W / 2
    @property
    def gun_y(self):  return self.y + P_H / 4


class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Lithic Artifacts", fps=60)
        self.world   = World(seed=42)
        self.player  = Player()
        self.bullets = []
        self.cam_y   = 0.0
        pyxel.run(self.update, self.draw)

    # ---- input ----

    def _left(self):
        return (pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_H) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT))

    def _right(self):
        return (pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_L) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT))

    def _up(self):
        return (pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_K) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP))

    def _down(self):
        return (pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_J) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN))

    def _jump(self):
        return (pyxel.btnp(pyxel.KEY_SPACE)        or
                pyxel.btnp(pyxel.KEY_UP)            or
                pyxel.btnp(pyxel.KEY_K)             or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B))

    def _shoot(self):
        return (pyxel.btn(pyxel.KEY_Z) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_X))

    def _aim_lock(self):
        return (pyxel.btn(pyxel.KEY_X) or
                pyxel.btn(pyxel.GAMEPAD1_BUTTON_LEFTSHOULDER))

    # ---- physics ----

    def _occupied_rows(self, p):
        return range(int(p.y // TILE), int((p.y + P_H - 1) // TILE) + 1)

    def _try_ledge_grab(self, p, wall_col, blocking_row, wall_dir):
        """Grab when bottom tile hits wall but top tile is open."""
        if p.on_ground or p.state == "hanging" or p.ledge_cd > 0:
            return False
        top_row = int(p.y // TILE)
        if blocking_row == top_row + 1 and not self.world.solid(wall_col, top_row):
            p.state     = "hanging"
            p.hang_wall = wall_dir
            p.y  = float(top_row * TILE)
            p.x  = float((wall_col * TILE - P_W) if wall_dir == 1
                         else (wall_col + 1) * TILE)
            p.vx     = 0.0
            p.vy     = 0.0
            p.aim_dx = -wall_dir   # default: aim away from wall
            p.aim_dy = 0
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
                    p.x  = float((lc + 1) * TILE)
                    p.vx = 0.0
                    p.wall_contact = -1
                    break
        elif p.vx > 0:
            rc = int((p.right - 1) // TILE)
            for row in self._occupied_rows(p):
                if self.world.solid(rc, row):
                    if self._try_ledge_grab(p, rc, row, 1):
                        return
                    p.x  = float(rc * TILE - P_W)
                    p.vx = 0.0
                    p.wall_contact = 1
                    break

    def _move_y(self, p):
        p.y += p.vy
        p.on_ground = False
        lc = int((p.x + P_HIT_INS) // TILE)
        rc = int((p.right - 1 - P_HIT_INS) // TILE)
        if p.vy < 0:
            tr = int(p.y // TILE)
            if self.world.solid(lc, tr) or self.world.solid(rc, tr):
                p.y  = float((tr + 1) * TILE)
                p.vy = 0.0
        else:
            br = int(p.bottom // TILE)
            if self.world.solid(lc, br) or self.world.solid(rc, br):
                p.y         = float(br * TILE - P_H)
                p.vy        = 0.0
                p.on_ground = True
                p.jump_type = "none"

    def _probe_walls(self, p):
        """Detect passive wall contact (for wall jump without pressing into wall)."""
        if p.on_ground:
            p.wall_contact = 0
            return
        tr = int(p.y // TILE)
        br = int((p.y + P_H - 1) // TILE)
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

    # ---- update / draw ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        p    = self.player
        adx  = (-1 if self._left() else 0) + (1 if self._right() else 0)
        jump = self._jump()

        if p.shoot_cd > 0: p.shoot_cd -= 1
        if p.wj_cd_l  > 0: p.wj_cd_l  -= 1
        if p.wj_cd_r  > 0: p.wj_cd_r  -= 1
        if p.ledge_cd > 0: p.ledge_cd -= 1

        if p.state == "hanging":
            p.aim_locked = self._aim_lock()
            if p.aim_locked:
                # Aim is constrained to 5 directions: up, down, straight-away,
                # diag-up-away, diag-down-away (nothing toward/into the wall).
                free = -p.hang_wall
                ady  = (-1 if self._up() else 0) + (1 if self._down() else 0)
                if adx != 0 or ady != 0:
                    p.aim_dx = free if adx == free else 0
                    p.aim_dy = ady
                if jump:
                    p.state    = "normal"
                    p.ledge_cd = 6
                    p.vy       = JUMP_VEL * 0.75
                    p.vx       = p.hang_wall * MOVE_SPEED
            else:
                if self._up() or jump:
                    # Launch upward and inward to land on top of the ledge
                    p.state    = "normal"
                    p.ledge_cd = 6
                    p.vy       = JUMP_VEL * 0.75
                    p.vx       = p.hang_wall * MOVE_SPEED
                elif self._down() or (adx != 0 and adx == -p.hang_wall):
                    p.state    = "normal"
                    p.ledge_cd = 6
                    p.vy       = 0.5
        else:
            p.aim_locked = self._aim_lock()

            if p.aim_locked:
                # Freeze horizontal movement; direction keys control aim
                p.vx = 0.0
                ady  = (-1 if self._up() else 0) + (1 if self._down() else 0)
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
                # Aim: facing direction; diagonal-up only with up + horizontal
                p.aim_dx = p.facing
                p.aim_dy = -1 if (self._up() and adx != 0) else 0

            if jump:
                if p.on_ground:
                    p.vy        = JUMP_VEL
                    p.on_ground = False
                    p.jump_type = "spin" if adx != 0 else "straight"
                    if p.jump_type == "straight":
                        p.vx = 0.0
                elif p.wall_contact != 0:
                    can = ((p.wall_contact == -1 and p.wj_cd_l == 0) or
                           (p.wall_contact ==  1 and p.wj_cd_r == 0))
                    if can:
                        p.vy        = WALL_JUMP_VEL
                        p.vx        = -p.wall_contact * WALL_JUMP_HVX
                        p.jump_type = "spin"
                        if p.wall_contact == -1:
                            p.wj_cd_l = WALL_JUMP_CD
                        else:
                            p.wj_cd_r = WALL_JUMP_CD

            p.vy = min(p.vy + GRAVITY, MAX_FALL)
            self._move_x(p)
            self._move_y(p)
            if p.wall_contact == 0:
                self._probe_walls(p)

        # Shoot
        if self._shoot() and p.shoot_cd == 0:
            dx, dy = p.aim_dx, p.aim_dy
            if dx == 0 and dy == 0:
                dx = p.facing
            self.bullets.append(Bullet(p.gun_x, p.gun_y, dx, dy))
            p.shoot_cd = SHOOT_COOLDOWN

        for b in self.bullets:
            b.update(self.world)
        self.bullets = [b for b in self.bullets if b.alive]

        self.world.ensure_gen(int(p.bottom // TILE) + 40)

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

        for b in self.bullets:
            b.draw(cam)

        p  = self.player
        px = int(p.x)
        py = int(p.y - cam)

        if p.state == "hanging":
            pyxel.text(px + 2, py + 1,        "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "n", YELLOW)
        elif not p.on_ground and p.jump_type == "straight":
            pyxel.text(px + 2, py + 1,        "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "|", YELLOW)
        elif not p.on_ground and p.jump_type == "spin":
            body = "*" if (pyxel.frame_count // 4) % 2 else "o"
            pyxel.text(px + 2, py + 1,        "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, body, YELLOW)
        else:
            pyxel.text(px + 2, py + 1,        "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "W", YELLOW)

        # Aim reticle when locked
        if p.aim_locked:
            cx = int(p.gun_x)
            cy = int(p.gun_y - cam)
            pyxel.rectb(cx + p.aim_dx * 12 - 2, cy + p.aim_dy * 12 - 2, 5, 5, ORANGE)


Game()

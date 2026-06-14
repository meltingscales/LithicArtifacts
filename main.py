import math
import pyxel
import random

from artifacts import SpiralBorer
from enemies   import Crawler, Flyer, ShootyFlier, EnemyBullet

SCREEN_W = 240
SCREEN_H = 160
TILE     = 8
COLS     = SCREEN_W // TILE

BLACK      = 0
DARK_GRAY  = 5
LIGHT_GRAY = 6
YELLOW     = 10
ORANGE     = 9

# Pause / body-panel layout
_CELL  = 13    # body-grid cell pitch (12 px visible + 1 px gap)
_GX    = 8     # body grid left edge
_GY    = 18    # body grid top edge
_IX    = 82    # inventory list left edge
_IY    = 18    # inventory list top edge
_IRH   = 10    # inventory row height
_TIPY  = 131   # tooltip divider y
_HOVER = 180   # frames of hover before description appears (3 s @ 60 fps)

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
        self.tiles          = {}
        self.rng            = random.Random(seed)
        self._gen_to        = -1
        self.pending_spawns = []   # list of (px_x, px_y, type_str) drained by Game
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
                # Maybe spawn an enemy on the new platform (skip very top)
                if y > 22 and self.rng.random() < 0.45:
                    solid = [x for x in range(1, COLS - 1)
                             if not (gap <= x < gap + gap_w)]
                    if len(solid) >= 2:
                        sc = self.rng.choice(solid)
                        r  = self.rng.random()
                        if r < 0.5:
                            self.pending_spawns.append(
                                (sc * TILE, (y - 1) * TILE, "crawler"))
                        elif r < 0.8:
                            self.pending_spawns.append(
                                (sc * TILE, (y - 4) * TILE, "flyer"))
                        else:
                            self.pending_spawns.append(
                                (sc * TILE, (y - 4) * TILE, "shooty_flier"))
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
        self.burrowing    = False
        self.crouching    = False
        self.artifacts    = []
        self.hp           = 10
        self.max_hp       = 10
        self.inv_cd       = 0    # invincibility frames after taking damage

    @property
    def right(self):  return self.x + P_W
    @property
    def bottom(self): return self.y + (TILE if self.crouching else P_H)
    @property
    def gun_x(self):  return self.x + P_W / 2
    @property
    def gun_y(self):  return self.y + (2 if self.crouching else P_H // 4)


DEBUG_ITEMS = [
    ("Spiral Borer", SpiralBorer),
]


class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Lithic Artifacts", fps=60)
        self.world        = World(seed=42)
        self.player       = Player()
        self.bullets      = []
        self.cam_y        = 0.0
        # Pause / body-panel state
        self.body_grid     = [[None] * 5 for _ in range(5)]
        self.inventory     = [SpiralBorer()]   # start with one for testing
        self.enemies       = []
        self.enemy_bullets = []
        self.held         = None              # artifact currently being moved
        self.held_src     = None              # ("body", r, c) | ("inv", i)
        self.paused       = False
        self.pause_panel  = 0                 # 0 = body, 1 = inventory
        self.body_cursor  = [0, 0]            # [row, col]
        self.inv_cursor   = 0
        self.hover_timer  = 0
        self.hover_key    = None
        # Debug menu state
        self.debug_open   = False
        self.debug_cursor = 0
        pyxel.run(self.update, self.draw)

    # ---- debug menu ----

    def _update_debug(self):
        n = len(DEBUG_ITEMS)
        if pyxel.btnp(pyxel.KEY_UP)   or pyxel.btnp(pyxel.KEY_K):
            self.debug_cursor = (self.debug_cursor - 1) % n
        if pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_J):
            self.debug_cursor = (self.debug_cursor + 1) % n
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN):
            _, cls = DEBUG_ITEMS[self.debug_cursor]
            inv_hit = next((a for a in self.inventory if isinstance(a, cls)), None)
            bod_pos = next(((r, c) for r in range(5) for c in range(5)
                            if isinstance(self.body_grid[r][c], cls)), None)
            if inv_hit:
                self.inventory.remove(inv_hit)
            elif bod_pos:
                r, c = bod_pos
                self.body_grid[r][c] = None
                self._sync_artifacts()
            else:
                self.inventory.append(cls())
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            self.debug_open = False

    def _draw_debug(self):
        p      = self.player
        lines  = len(DEBUG_ITEMS)
        pw     = 150
        ph     = 24 + lines * 10
        px0    = 4
        py0    = 4
        pyxel.rect(px0, py0, pw, ph, BLACK)
        pyxel.rectb(px0, py0, pw, ph, LIGHT_GRAY)
        pyxel.text(px0 + 4, py0 + 4,  "-- DEBUG --", YELLOW)
        pyxel.text(px0 + 60, py0 + 4, "Z:toggle  Esc/F1:close", DARK_GRAY)
        for i, (label, cls) in enumerate(DEBUG_ITEMS):
            has    = (any(isinstance(a, cls) for a in self.inventory) or
                      any(isinstance(self.body_grid[r][c], cls)
                          for r in range(5) for c in range(5)
                          if self.body_grid[r][c] is not None))
            marker = "[x]" if has else "[ ]"
            cursor = ">" if i == self.debug_cursor else " "
            color  = YELLOW if i == self.debug_cursor else LIGHT_GRAY
            pyxel.text(px0 + 4, py0 + 14 + i * 10,
                       f"{cursor} {marker} {label}", color)

    # ---- pause / body panel ----

    def _sync_artifacts(self):
        """Rebuild player.artifacts from body_grid; handle side-effects."""
        self.player.artifacts = [
            a for row in self.body_grid for a in row if a is not None
        ]
        if not any(isinstance(a, SpiralBorer) for a in self.player.artifacts):
            self.player.burrowing  = False
            self.player.crouching  = False

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
        self.held     = a
        self.held_src = ("body", r, c)
        self._sync_artifacts()

    def _pickup_from_inventory(self):
        if not self.inventory or self.inv_cursor >= len(self.inventory):
            return
        a = self.inventory.pop(self.inv_cursor)
        self.inv_cursor = min(self.inv_cursor, max(0, len(self.inventory) - 1))
        self.held     = a
        self.held_src = ("inv", self.inv_cursor)

    def _place_on_body(self, r, c):
        other = self.body_grid[r][c]
        self.body_grid[r][c] = self.held
        if other is not None:
            self._return_to_src(other)
        self.held     = None
        self.held_src = None
        self._sync_artifacts()

    def _place_in_inventory(self):
        idx = min(self.inv_cursor, len(self.inventory))
        self.inventory.insert(idx, self.held)
        self.held     = None
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
        self.held     = None
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
        if (pyxel.btnp(pyxel.KEY_TAB) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_LEFTSHOULDER) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_RIGHTSHOULDER)):
            self.pause_panel = 1 - self.pause_panel
            return

        # Escape / Start / B: cancel hold or close menu
        if (pyxel.btnp(pyxel.KEY_ESCAPE) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B)):
            if self.held:
                self._cancel_hold()
            else:
                self.paused = False
            return

        up   = (pyxel.btnp(pyxel.KEY_UP)    or pyxel.btnp(pyxel.KEY_K) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_UP))
        down = (pyxel.btnp(pyxel.KEY_DOWN)  or pyxel.btnp(pyxel.KEY_J) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN))
        left = (pyxel.btnp(pyxel.KEY_LEFT)  or pyxel.btnp(pyxel.KEY_H) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT))
        rght = (pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_L) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT))
        act  = (pyxel.btnp(pyxel.KEY_Z)     or pyxel.btnp(pyxel.KEY_RETURN) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A))

        if self.pause_panel == 0:   # body grid
            r, c = self.body_cursor
            if up:    r = max(0, r - 1)
            if down:  r = min(4, r + 1)
            if left:  c = max(0, c - 1)
            if rght:  c = min(4, c + 1)
            self.body_cursor = [r, c]
            if act:
                if self.held:
                    self._place_on_body(r, c)
                else:
                    self._pickup_from_body(r, c)
        else:                       # inventory list
            n = len(self.inventory)
            if up:   self.inv_cursor = max(0, self.inv_cursor - 1)
            if down: self.inv_cursor = min(max(0, n - 1), self.inv_cursor + 1)
            if act:
                if self.held:
                    self._place_in_inventory()
                else:
                    self._pickup_from_inventory()

        # Hover-timer: reset whenever cursor lands on a different artifact
        hov = self._hovered_artifact()
        if hov is not self.hover_key:
            self.hover_key   = hov
            self.hover_timer = 0
        else:
            self.hover_timer += 1

    def _draw_pause(self):
        pyxel.cls(BLACK)

        # Panel headers
        bc = YELLOW if self.pause_panel == 0 else LIGHT_GRAY
        ic = YELLOW if self.pause_panel == 1 else LIGHT_GRAY
        pyxel.text(_GX, 4, "BODY",              bc)
        pyxel.text(_IX, 4, "INVENTORY",          ic)
        pyxel.text(170, 4, "TAB:switch Esc:close", DARK_GRAY)

        # Body grid
        for r in range(5):
            for c in range(5):
                x0     = _GX + c * _CELL
                y0     = _GY + r * _CELL
                is_cur = (self.pause_panel == 0 and self.body_cursor == [r, c])
                a      = self.body_grid[r][c]
                pyxel.rectb(x0, y0, _CELL - 1, _CELL - 1,
                            YELLOW if is_cur else DARK_GRAY)
                if is_cur and self.held:
                    pyxel.text(x0 + 3, y0 + 3, self.held.glyph, ORANGE)
                elif a:
                    pyxel.text(x0 + 3, y0 + 3, a.glyph, LIGHT_GRAY)

        # "HOLDING" indicator below the grid
        if self.held:
            hy = _GY + 5 * _CELL + 3
            pyxel.text(_GX, hy,     f"HOLD:{self.held.glyph} {self.held.name}", ORANGE)
            pyxel.text(_GX, hy + 9, "Z:place  Esc:cancel", DARK_GRAY)

        # Inventory list (scrolling)
        max_vis = (_TIPY - _IY - 2) // _IRH
        scroll  = max(0, self.inv_cursor - max_vis + 1)
        if not self.inventory:
            pyxel.text(_IX, _IY, "(empty)", DARK_GRAY)
        for i, a in enumerate(self.inventory):
            vi = i - scroll
            if vi < 0 or vi >= max_vis:
                continue
            is_cur = (self.pause_panel == 1 and self.inv_cursor == i)
            col    = YELLOW if is_cur else LIGHT_GRAY
            pre    = ">" if is_cur else " "
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
        return range(int(p.y // TILE), int((p.bottom - 1) // TILE) + 1)

    def _try_ledge_grab(self, p, wall_col, blocking_row, wall_dir):
        """Grab when bottom tile hits wall but top tile is open."""
        if p.on_ground or p.state == "hanging" or p.ledge_cd > 0 or p.burrowing:
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
        if p.burrowing:
            return
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
                p.y         = float(br * TILE - (TILE if p.crouching else P_H))
                p.vy        = 0.0
                p.on_ground = True
                p.jump_type = "none"

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

    # ---- update / draw ----

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        # Pause takes input priority; Tab/Start opens it from gameplay
        if self.paused:
            self._update_pause()
            return

        # F1 debug menu (only when not paused)
        if pyxel.btnp(pyxel.KEY_F1):
            self.debug_open   = not self.debug_open
            self.debug_cursor = 0
        if self.debug_open:
            self._update_debug()
            return

        # Tab / Start opens pause menu from gameplay
        if (pyxel.btnp(pyxel.KEY_TAB) or
                pyxel.btnp(pyxel.GAMEPAD1_BUTTON_START)):
            self.paused = True
            return

        p      = self.player
        adx    = (-1 if self._left() else 0) + (1 if self._right() else 0)
        jump   = self._jump()
        down_p = (pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(pyxel.KEY_J) or
                  pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN))

        if p.shoot_cd > 0: p.shoot_cd -= 1
        if p.wj_cd_l  > 0: p.wj_cd_l  -= 1
        if p.wj_cd_r  > 0: p.wj_cd_r  -= 1
        if p.ledge_cd > 0: p.ledge_cd -= 1
        if p.inv_cd   > 0: p.inv_cd   -= 1

        inputs = {
            "left":  self._left(),  "right": self._right(),
            "up":    self._up(),    "down":  self._down(),
            "jump":  jump,          "shoot": self._shoot(),
            "burrow": (pyxel.btn(pyxel.KEY_C) or
                       pyxel.btn(pyxel.GAMEPAD1_BUTTON_Y)),
        }
        for a in p.artifacts:
            a.on_frame(p, self.world, inputs)

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

            if p.crouching:
                # Crouching: stationary; left/right only updates facing
                p.vx = 0.0
                if self._left():  p.facing = -1
                if self._right(): p.facing = 1
                if p.aim_locked:
                    ady = (-1 if self._up() else 0) + (1 if self._down() else 0)
                    if adx != 0 or ady != 0:
                        p.aim_dx = adx
                        p.aim_dy = ady
                else:
                    # No lock: shoot straight forward from the crouched position
                    p.aim_dx = p.facing
                    p.aim_dy = 0
                # Toggle off: Down press → stand up if headroom allows
                if down_p:
                    tr = int(p.y // TILE) - 1
                    lc = int((p.x + P_HIT_INS) // TILE)
                    rc = int((p.right - 1 - P_HIT_INS) // TILE)
                    if tr < 0 or not (self.world.solid(lc, tr) or
                                      self.world.solid(rc, tr)):
                        p.y        -= TILE
                        p.crouching = False
            elif p.aim_locked:
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
                # Toggle crouch on: Down press while on ground, not burrowing
                if p.on_ground and down_p and not p.burrowing:
                    p.y        += TILE
                    p.crouching = True
                    p.vx        = 0.0

            if jump and not p.burrowing and not p.crouching:
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
            if p.wall_contact == 0 and not p.burrowing:
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

        # Player bullets vs enemies
        for b in self.bullets:
            if not b.alive:
                continue
            for e in self.enemies:
                if e.alive and (b.x < e.right and b.x + 2 > e.x and
                                b.y < e.bottom and b.y + 2 > e.y):
                    e.take_damage(1)
                    b.alive = False
                    break

        self.bullets = [b for b in self.bullets if b.alive]

        # Drain world spawn queue
        for sx, sy, etype in self.world.pending_spawns:
            if   etype == "crawler":      self.enemies.append(Crawler(sx, sy))
            elif etype == "flyer":        self.enemies.append(Flyer(sx, sy))
            elif etype == "shooty_flier": self.enemies.append(ShootyFlier(sx, sy))
        self.world.pending_spawns.clear()

        # Update enemies
        for e in self.enemies:
            if e.alive:
                e.update(self.world, p, self.enemy_bullets)

        # Update enemy bullets
        for eb in self.enemy_bullets:
            eb.update()

        # Damage player (enemy contact, then enemy bullets; one source per inv window)
        if p.inv_cd == 0:
            for e in self.enemies:
                if e.alive and (p.x < e.right and p.right > e.x and
                                p.y < e.bottom and p.bottom > e.y):
                    p.hp    = max(0, p.hp - e.damage)
                    p.inv_cd = 60
                    break
            else:
                for eb in self.enemy_bullets:
                    if eb.alive and (p.x < eb.x + 2 and p.right > eb.x and
                                     p.y < eb.y + 2 and p.bottom > eb.y):
                        p.hp     = max(0, p.hp - 1)
                        p.inv_cd = 60
                        eb.alive = False
                        break

        # Cull dead / off-screen-above objects
        cull_y = self.cam_y - SCREEN_H * 3
        self.enemies       = [e  for e  in self.enemies       if e.alive  and e.y  > cull_y]
        self.enemy_bullets = [eb for eb in self.enemy_bullets if eb.alive and eb.y > cull_y]

        self.world.ensure_gen(int(p.bottom // TILE) + 40)

        target     = p.y - SCREEN_H * 0.33
        self.cam_y += (target - self.cam_y) * 0.12
        self.cam_y  = max(0.0, self.cam_y)

    def draw(self):
        if self.paused:
            self._draw_pause()
            return

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

        for eb in self.enemy_bullets:
            eb.draw(cam)

        for e in self.enemies:
            e.draw(cam)

        p  = self.player
        px = int(p.x)
        py = int(p.y - cam)

        # Blink player during invincibility frames
        if p.inv_cd > 0 and (pyxel.frame_count // 4) % 2:
            pass  # skip draw this frame
        elif p.state == "hanging":
            pyxel.text(px + 2, py + 1,        "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "n", YELLOW)
        elif p.crouching:
            pyxel.text(px + 2, py + 1, "@", YELLOW)
        elif p.burrowing:
            pyxel.text(px + 2, py + 1,        "@", YELLOW)
            pyxel.text(px + 2, py + TILE + 1, "v", YELLOW)
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

        # HP HUD — row of 4×4 blocks at bottom-left
        for i in range(p.max_hp):
            col = YELLOW if i < p.hp else DARK_GRAY
            pyxel.rect(4 + i * 5, SCREEN_H - 8, 4, 4, col)

        if self.debug_open:
            self._draw_debug()


Game()

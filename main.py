import pyxel

SCREEN_W = 240
SCREEN_H = 160
TILE = 8
COLS = SCREEN_W // TILE  # 30
ROWS = SCREEN_H // TILE  # 20

BLACK = 0
DARK_GRAY = 5
LIGHT_GRAY = 6
WHITE = 7
YELLOW = 10


class Game:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Lithic Artifacts")
        self.px = COLS // 2
        self.py = ROWS // 2
        self.map = self._gen_map()
        pyxel.run(self.update, self.draw)

    def _gen_map(self):
        m = [[0] * COLS for _ in range(ROWS)]
        for x in range(COLS):
            m[0][x] = 1
            m[ROWS - 1][x] = 1
        for y in range(ROWS):
            m[y][0] = 1
            m[y][COLS - 1] = 1
        return m

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        dx, dy = 0, 0
        if pyxel.btnp(pyxel.KEY_UP, hold=10, period=3) or pyxel.btnp(pyxel.KEY_K, hold=10, period=3):
            dy = -1
        if pyxel.btnp(pyxel.KEY_DOWN, hold=10, period=3) or pyxel.btnp(pyxel.KEY_J, hold=10, period=3):
            dy = 1
        if pyxel.btnp(pyxel.KEY_LEFT, hold=10, period=3) or pyxel.btnp(pyxel.KEY_H, hold=10, period=3):
            dx = -1
        if pyxel.btnp(pyxel.KEY_RIGHT, hold=10, period=3) or pyxel.btnp(pyxel.KEY_L, hold=10, period=3):
            dx = 1

        nx, ny = self.px + dx, self.py + dy
        if self.map[ny][nx] == 0:
            self.px, self.py = nx, ny

    def draw(self):
        pyxel.cls(BLACK)

        for y in range(ROWS):
            for x in range(COLS):
                if self.map[y][x] == 1:
                    pyxel.text(x * TILE, y * TILE, "#", LIGHT_GRAY)
                else:
                    pyxel.text(x * TILE, y * TILE, ".", DARK_GRAY)

        pyxel.text(self.px * TILE, self.py * TILE, "@", YELLOW)


Game()

# fmt: off
from constants import SCREEN_W, TILE
P_W = TILE
P_H = TILE * 2
# fmt: on


class Player:
    def __init__(self):
        # fmt: off
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
        self.wj_cd_l         = 0
        self.wj_cd_r         = 0
        self.wj_away_window  = 0   # frames remaining to press jump after "away" detected
        self.wj_away_side    = 0   # wall_contact value when away was pressed (-1/1)
        self.wj_rise_wall    = 0   # wall jumped from; non-zero during penalised rise
        self.wj_coyote       = 0   # frames of coyote wall contact remaining
        self.wj_coyote_side  = 0   # side (-1/1) of last real wall contact
        self.ledge_cd     = 0
        self.burrowing    = False
        self.crouching    = False
        self.climbing     = False
        self.artifacts    = []
        self.hp           = 10
        self.max_hp       = 10
        self.inv_cd       = 0    # invincibility frames after taking damage
        # fmt: on

    # fmt: off
    @property
    def right(self):  return self.x + P_W
    @property
    def bottom(self): return self.y + (TILE if self.crouching else P_H)
    @property
    def gun_x(self):  return self.x + P_W / 2
    @property
    def gun_y(self):  return self.y + (2 if self.crouching else P_H // 4)
    # fmt: on

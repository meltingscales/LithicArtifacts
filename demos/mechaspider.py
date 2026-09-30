"""
MechaspiderLegs wall-climb demo / bug hunt.

Runs the real Game physics on a hand-built scene: floor, a tall wall with a
2-tile gap in it, open air above the wall top. Input is scripted (no keyboard)
so runs are reproducible. A debug overlay shows state, wall contact, grip and
leg anchors.

    just demo mechaspider              # interactive, scripted input, overlay
    just demo mechaspider --headless   # print a per-frame trace, flag snaps
    just demo mechaspider --script gap # choose a script (see SCRIPTS)
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyxel  # noqa: E402

from artifacts import MechaspiderLegs  # noqa: E402
from constants import CLIMB_SPEED, COLS, TILE  # noqa: E402
from main import Game  # noqa: E402

# fmt: off
FLOOR_ROW = 13   # solid floor across the preamble
WALL_COL  = 18   # tall wall, two columns wide
WALL_TOP  = 3    # first solid row of the wall
GAP_ROWS  = (8, 9)   # 2-tile opening in the wall
# fmt: on

# Each script: list of (frames, {"left","right","up","down","jump"}) held for that many frames.
SCRIPTS = {
    # Walk into the wall, jump, hold right to grip, climb straight up past the gap and the top.
    "gap": [
        (30, {"right"}),
        (1, {"right", "jump"}),
        (12, {"right"}),
        (200, {"right", "up"}),
        (60, {"right"}),
    ],
    # Grip, then let go of the wall direction and drift away from it while climbing.
    "drift": [
        (30, {"right"}),
        (1, {"right", "jump"}),
        (12, {"right"}),
        (30, {"right", "up"}),
        (120, {"left"}),
        (60, set()),
    ],
    # Climb to the top, then push over the edge to stand on the wall.
    "crest": [
        (30, {"right"}),
        (1, {"right", "jump"}),
        (12, {"right"}),
        (60, {"right", "up"}),
        (30, set()),
    ],
    # Grip below the gap, then climb down to the floor.
    "down": [
        (30, {"right"}),
        (1, {"right", "jump"}),
        (12, {"right"}),
        (20, {"right", "up"}),
        (120, {"right", "down"}),
    ],
}


class Demo(Game):
    def __init__(self, script, headless):
        self.script = script
        self.headless = headless
        self.frame = 0
        self.trace = []
        super().__init__()

    # ---- scene ----

    def _full_reset(self, seed=0):
        super()._full_reset(seed)
        w = self.world
        w.tiles = {}
        for x in range(COLS):
            w.tiles[(x, 0)] = 1
            w.tiles[(x, FLOOR_ROW)] = 1
        for y in range(1, FLOOR_ROW):
            w.tiles[(0, y)] = 1
            w.tiles[(COLS - 1, y)] = 1
        for y in range(WALL_TOP, FLOOR_ROW):
            if y not in GAP_ROWS:
                w.tiles[(WALL_COL, y)] = 1
                w.tiles[(WALL_COL + 1, y)] = 1  # two wide so the top is standable
        w.ensure_gen = lambda row: None  # no procedural sections
        w.pickups = []
        self.enemies = []
        p = self.player
        p.x = float((WALL_COL - 4) * TILE)
        p.y = float((FLOOR_ROW - 2) * TILE)
        legs = MechaspiderLegs()
        p.artifacts = [legs]
        self.body_grid[0][0] = legs
        self.legs = legs
        self.immortal = True

    # ---- scripted input (overrides the pyxel.btn wrappers) ----

    def _held(self):
        f = 0
        for n, keys in self.script:
            if self.frame < f + n:
                return keys
            f += n
        return set()

    # fmt: off
    def _left(self):     return "left"  in self._held()
    def _right(self):    return "right" in self._held()
    def _up(self):       return "up"    in self._held()
    def _down(self):     return "down"  in self._held()
    def _jump(self):     return "jump"  in self._held()
    def _jump_held(self):return "jump"  in self._held()
    def _left_p(self):   return False
    def _right_p(self):  return False
    def _up_p(self):     return False
    def _down_p(self):   return False
    def _shoot(self):    return False
    def _aim_lock(self): return False
    def _missile_mode(self): return False
    def _select_btnp(self):  return False
    # fmt: on

    # ---- loop ----

    def update(self):
        p = self.player
        prev = (p.x, p.y, p.state, p.climbing)
        super().update()
        self.frame += 1
        dy = p.y - prev[1]
        dx = p.x - prev[0]
        anchored = sum(self.legs._foot_anchored)
        note = []
        if p.climbing and abs(dy) > CLIMB_SPEED + 0.01:
            note.append(f"SNAP dy={dy:+.1f}")
        if p.state != prev[2]:
            note.append(f"state {prev[2]}->{p.state}")
        if p.climbing != prev[3]:
            note.append(f"climbing {prev[3]}->{p.climbing}")
        if p.climbing and p.state == "hanging":
            note.append("CONFLICT climbing+hanging")
        if p.climbing and anchored == 0:
            note.append("NO-ANCHOR")
        if p.climbing and not self.legs._has_wall_grip(p, self.world):
            note.append("NO-WALL")
        self.trace.append(
            (
                self.frame,
                p.x,
                p.y,
                p.state,
                p.climbing,
                p.wall_contact,
                anchored,
                dx,
                dy,
                note,
            )
        )
        if self.headless:
            if note:
                print(
                    f"f{self.frame:4d} x={p.x:6.1f} y={p.y:6.1f} wc={p.wall_contact:+d} legs={anchored} "
                    + " | ".join(note)
                )
            if self.frame >= sum(n for n, _ in self.script):
                self._report()
                sys.stdout.flush()
                pyxel.quit()

    def _report(self):
        p = self.player
        snaps = [t for t in self.trace if any(n.startswith("SNAP") for n in t[9])]
        conflicts = [
            t for t in self.trace if any(n.startswith("CONFLICT") for n in t[9])
        ]
        noanchor = [t for t in self.trace if "NO-ANCHOR" in t[9]]
        nowall = [t for t in self.trace if "NO-WALL" in t[9]]
        climbing = [t for t in self.trace if t[4]]
        top_y = min((t[2] for t in climbing), default=None)
        print(
            f"--- {len(self.trace)} frames, climbing {len(climbing)}, snaps {len(snaps)}, "
            f"climb+hang conflicts {len(conflicts)}, no-anchor {len(noanchor)}, no-wall {len(nowall)}, "
            f"highest y while climbing {top_y} (wall top y={WALL_TOP * TILE}), final x={p.x:.1f} y={p.y:.1f} on_ground={p.on_ground} climbing={p.climbing}"
        )

    def draw(self):
        super().draw()
        if self.headless:
            return
        p = self.player
        cam = self.cam_y
        legs = self.legs
        for i, (fx, fy) in enumerate(legs._feet):
            col = 11 if legs._foot_anchored[i] else 8
            pyxel.rectb(int(fx) - 1, int(fy - cam) - 1, 3, 3, col)
        pyxel.text(
            2,
            2,
            f"f{self.frame} {p.state} climb={p.climbing} wc={p.wall_contact:+d}",
            7,
        )
        pyxel.text(
            2,
            10,
            f"x={p.x:.1f} y={p.y:.1f} vy={p.vy:.2f} grip={legs._has_wall_grip(p, self.world)}",
            7,
        )
        pyxel.text(
            2,
            18,
            f"legs anchored={sum(legs._foot_anchored)}  ws={legs._wall_side:+d}",
            7,
        )
        last = self.trace[-1][9] if self.trace else []
        if last:
            pyxel.text(2, 26, " | ".join(last)[:58], 8)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", choices=sorted(SCRIPTS), default="gap")
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    Demo(SCRIPTS[args.script], args.headless).run()

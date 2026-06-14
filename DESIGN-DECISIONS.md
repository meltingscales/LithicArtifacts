# Design Decisions

Locked decisions with rationale. Update this when a decision changes.

---

## Movement

Modeled closely on **Metroid Fusion** (GBA). All mechanics below are implemented.

**Spin jump vs. straight jump.**
Jump while pressing a direction → spin jump: full air control, can change direction mid-flight.
Jump while neutral → straight jump: locked vertical trajectory, no air steering until landing.
The distinction is visible in the player glyph (`*`/`o` spinning vs. `|` rigid).

**Aim lock (trigger lock).**
Hold `X` / LB to freeze horizontal movement and enter 8-way aim mode.
Direction keys control aim angle while locked; an orange reticle shows the aimed direction.
Releasing aim lock restores movement. Can still jump while locked.
Without lock, aim is always the facing direction (or diagonal-up with up + horizontal).

**Crouch.**
Press Down to toggle crouch; press Down again to stand (blocked if a ceiling is directly above).
While crouching the player is 1 tile tall (hitbox top shifts down, feet stay anchored).
Movement is locked to zero — left/right only updates facing.
Without aim lock, shooting fires horizontally from the crouched gun position (lower than standing).
With aim lock, full directional aim is available (same 8-way system as standing).
Jump and wall-jump are blocked while crouching; burrow (Spiral Borer) requires crouching + C/Y.

**Ledge grab.**
When the player's bottom tile collides with a wall edge mid-air and the top tile is in open space,
the player grabs the ledge and enters a hanging state (`@`/`n`).
Press up or jump to launch upward off the ledge; press down or away from the wall to drop.

**Wall jump.**
Touching a wall mid-air (actively or passively) enables a wall jump on the next jump press.
The player kicks off in the opposite direction with reduced horizontal velocity.
**Direction restriction:** each wall side has an independent 24-frame cooldown after use,
preventing infinite same-side climbing. The two sides are independent (left wall and right wall
have separate cooldown timers `wj_cd_l` / `wj_cd_r`).

---

## Combat

TBD

---

## Rendering

**Pixel-rendered at native 240×160 (GBA resolution), scaled up.**
Not terminal/ASCII. Characters are glyphs drawn as pixels, not printed characters.
Tile size: 8×8 px → 30×20 grid.

**16-color palette enforced aesthetically.**
Pyxel's default palette. No per-pixel color freedom — this keeps the look coherent and GBA-authentic.

---

## Engine

**Pyxel (Python).**
Chosen over LÖVE2D (Lua), Bevy (Rust), and Godot.
Rationale: fastest to prototype, built-in retro constraints, `.pyxres` sprite/tilemap editor included.
`uv` manages the Python environment.

---

## Game Structure

**Vertical-scrolling platformer, like Downwell.**
Not top-down, not horizontal. The player falls downward through a generated dungeon.
Camera follows the player with a bias toward showing what's below.

**Real-time physics, not turn-based.**
Gravity, velocity, tile-collision AABB. 60fps.
The roguelike elements (artifacts, permadeath, procedural floors) live on top of real-time movement.

**Player is 2 tiles tall (16px), like Metroid's Samus.**
Rendered as `@` (head) over `W` (legs). Hard requirement — affects all collision and level design.

---

## Input

Both keyboard and gamepad supported from day one. No analog stick — D-pad only.
Rationale: GBA aesthetic implies D-pad primacy.

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | arrows / hjkl | D-pad |
| Jump | space / up / K | A or B |
| Crouch (toggle) | down / J | D-pad Down |
| Shoot | Z | X |
| Aim lock (hold) | X | LB |
| Burrow (while crouching) | C | Y |
| Quit | Q | — |

---

## Content

**Artifacts are found, not chosen.**
No "pick 1 of 3" draft screen. Artifacts appear in the dungeon as items you walk over.
Rationale: the "holy shit, cool artifact" discovery moment is the core loop. A menu drains that.

**~30–40 artifacts. Interactions are emergent, not documented.**
The game does not explain what artifacts do to each other. Players find the cracks.
When a broken combo is detected, the game acknowledges it ("ABERRANT BUILD") and escalates difficulty.

**5–10 dungeon floors. Sessions under 30 minutes.**
Scope anchor. This is a small, cheap game. No overworld, no factions, no dialogue.

---

## Inspirations

| Game | What we're taking |
|---|---|
| Caves of Qud | Body modification system, emergent mutation interactions |
| Metroid Fusion | Body horror aesthetic, 2-tile-tall protagonist, sense of dread |
| Rogue (1980) | Random item discovery, permadeath, austerity |
| Downwell | Vertical scrolling, real-time fall mechanics |
| Noita | Rewarding the player for breaking the game |
| LithicRivers | Aesthetic sensibility, glyph-forward rendering |

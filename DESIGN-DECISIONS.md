# Design Decisions

Locked decisions with rationale. Update this when a decision changes.

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

**Keyboard: arrows / hjkl / space. Gamepad: D-pad + A button.**
Both supported from day one. No analog stick (D-pad only for now).
Rationale: GBA aesthetic implies D-pad primacy.

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

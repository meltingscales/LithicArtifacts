# Current Context

Last updated: 2026-06-13

## What this project is

**Lithic Artifacts** — a small pixel-rendered roguelike/platformer at GBA resolution (240×160).
The player descends through a procedurally generated vertical dungeon finding body-modifying artifacts.
The "break the game" emergent combo system is the core appeal. Short sessions (<30 min). Cheap.

See `README.md` and `DESIGN-DECISIONS.md` for locked decisions.

## Tech stack

- Python, managed by `uv`
- Pyxel 2.9.6 (pixel game engine, 16-color palette, 240×160 native resolution)
- `just run` to launch

## Where the codebase is right now

`main.py` is a working scaffold with:

- **World**: procedurally generated infinite vertical dungeon. Tile dict `{(col, row): 1}`. `destroy(col, row)` removes tiles (for bullet block destruction).
- **Bullet**: fires in 8 directions, destroys solid tiles on contact, 90-frame lifetime.
- **Player** (2 tiles tall, `@`/`W`): full Metroid Fusion-style movement —
  - Spin jump (jump + direction): full air control
  - Straight jump (jump, no direction): locked vertical, no air steering
  - Aim lock (`X` / LB hold): freeze horizontal, 8-way aim with D-pad; orange reticle shown
  - Shoot (`Z` / gamepad X): fires bullet in aimed direction; destroys blocks
  - Ledge grab: bottom tile hits wall edge mid-air → hang state (`@`/`n`); up/jump to launch off
  - Wall jump: touch wall mid-air → jump kicks off opposite direction; per-side 24-frame cooldown
  - Wall contact detected both actively (pressing into wall) and passively (`_probe_walls`)
- **Camera**: smooth follow, biased 33% from top to show what's below

## What's NOT done yet (obvious next steps)

- No enemies
- No artifacts / item pickups
- No HP / death
- No floors / progression (just infinite descent)
- No HUD
- DESIGN-DECISIONS.md has a "Movement" section the user started filling in — needs enriching
- TODO.md referenced in CLAUDE.md but doesn't exist yet

## Key implementation notes

- Tile collision uses AABB: `_move_x` then `_move_y` separately
- `_occupied_rows(p)` returns all tile rows player spans (important: player can span 3 rows when not tile-aligned)
- `_try_ledge_grab`: triggers when `blocking_row == top_row + 1` and top tile is open
- Wall jump cooldown: `wj_cd_l` / `wj_cd_r` per side, not a shared cooldown
- `p.jump_type`: "none" | "straight" | "spin" — reset to "none" on landing
- Bullet fires from `gun_x, gun_y` (upper-body center); `dx==0 and dy==0` falls back to facing

## Commit log so far

- `c6b0109` — scaffold: vertical-scrolling platformer, real-time physics, camera, DESIGN-DECISIONS.md
- `610d197` — gun + aim lock + straight/spin jump + ledge grab + wall jump

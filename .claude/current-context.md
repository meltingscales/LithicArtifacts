# Current Context

Last updated: 2026-06-14

## What this project is

**Lithic Artifacts** — small pixel roguelike/platformer at GBA resolution (240×160).
Player descends through procedurally generated vertical dungeon collecting body-modifying artifacts.
"Break the game" emergent combos are the core appeal. Short sessions (<30 min). Cheap.

See `README.md` and `DESIGN-DECISIONS.md` for locked decisions.

## Tech stack

- Python, managed by `uv`
- Pyxel 2.9.6 (16-color palette, 240×160)
- `just run` to launch, `just fmt` to format (uses `uvx ruff`)

## Where the codebase is right now

### World / worldgen (`worldgen.py`)
- Infinite vertical dungeon, section-based (20-row sections)
- Section types: `open`, `platforms`, `chamber`, `cave` (Perlin noise, tile type 2)
- Cave sections: BFS traversability check + up to 15 retries; falls back to open
- `world.tiles`: `{(col, row): tile_type}` — 1 = platform, 2 = cave rock
- `world.solid()` checks `!= 0`; `world.destroy()` removes tiles

### Player (`main.py: Player`)
- 2 tiles tall (`@`/`W` glyphs), full Metroid Fusion-style movement
- Spin/straight jump, aim lock (8-way), ledge grab, wall jump
- Shoot straight up when stationary (aim_dx=0, aim_dy=-1)
- Down-aim while running or airborne
- HP (10/10), invincibility frames after hits, death → respawn screen

### Artifacts (`artifacts.py`)
- `Wallbreaker`: shots destroy tiles
- `SpiralBorer`: phase through floors while crouching
- `VampiricCape`: SotN-style 8-ghost afterimage trail; 1-in-3 heal on kill
- Hook system: `on_frame`, `on_shoot`, `on_kill`, `on_land`
- Equipped via body grid (pause menu); world pickups spawn every few sections

### Enemies (`enemies.py`)
- `Crawler`: walks on platforms, damages on contact
- `Flyer`: drifts toward player
- `ShootyFlier`: drifts + fires projectiles; plays chiptune sounds on spawn/shoot

### Game systems
- Smooth camera (33% from top bias)
- Pause menu: body grid + inventory panel; artifact drag-and-drop
- F1 debug menu: toggle artifacts + immortality flag
- Death: hp==0 → 1.5s death screen → Z-to-respawn (resets pos/hp/enemies)
- Tile rendering: type 1 = dark gray/light gray; type 2 = brown/dark gray

## What's NOT done yet

- Floors / progression (floor counter, difficulty scaling, biome transitions)
- Player HP shown in HUD (row of blocks) — exists; death/respawn exists
- Fractal Blaster, Ice Missiles artifacts
- Assets/ inclusion in .spec file
- PyInstaller/Steam release

## Key implementation notes

- `_try_ledge_grab`: skips if solid ground at `blocking_row+1` under player col (prevents 1-block grabs)
- `_occupied_rows(p)`: player can span 3 tile rows when not tile-aligned
- Wall jump: per-side cooldowns `wj_cd_l`/`wj_cd_r`
- `VampiricCape.draw_trail(cam)` called before player draw so player renders on top
- `_ARTIFACT_POOL` controls world drop pool; `DEBUG_ITEMS` controls F1 menu
- ruff `# fmt: off`/`# fmt: on` guards around all intentionally aligned blocks

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
- `_is_traversable` now two-pass: Pass 1 finds all reachable states; Pass 2 verifies every reachable grounded state can also reach the section bottom (catches side-pocket soft-locks)
- `world.tiles`: `{(col, row): tile_type}` — 1 = platform, 2 = cave rock
- `world.solid()` checks `!= 0`; `world.destroy()` removes tiles
- Biome system: 5 biomes (Dungeon→Caverns→Abyss→Depths→Inferno), cycle every 6 sections; "ENTERING [NAME]" banner on transition (5s cooldown)

### Player (`main.py: Player`)
- 2 tiles tall (`@`/`W` glyphs), full Metroid Fusion-style movement
- Spin/straight jump, aim lock (8-way), ledge grab, wall jump
- Shoot straight up when stationary; down-aim while running or airborne
- HP (10/10), invincibility frames after hits, death → respawn screen

### Artifacts (`artifacts.py`)
- `Wallbreaker`: shots destroy tiles
- `SpiralBorer`: phase through floors while crouching
- `VampiricCape`: SotN-style 8-ghost afterimage trail; 1-in-3 heal on kill
- `IceMissile` (`MissileArtifact` base): hold RB+Z to fire; freeze 5s on hit; limited ammo; `~:XX` HUD
- `FractalBlaster`: piercing shots trace Julia set boundary (waypoints from cached grid); fires dithered Julia bg overlay (3s fade, 50% alpha cap); slowly drifting c parameter; FractalBullet emits FractalBulletSmall splinters every 3rd waypoint (max 5 events); synergy with Wallbreaker (adjacency → 10% wall-break on pass-through)
- Hook system: `on_frame`, `on_shoot`, `on_kill`, `on_land`
- Equipped via body grid (pause menu); world pickups spawn every few sections
- Synergy UI: pulsing pink dithered line between adjacent FractalBlaster+Wallbreaker in body panel

### Enemies (`enemies.py`)
- `Crawler`: walks on platforms, damages on contact
- `Flyer`: sine-bob movement, dithered navy overlay when frozen
- `ShootyFlier`: drifts + fires projectiles
- Frozen enemies: `frozen_timer` set by Ice Missiles; skipped in damage check; walkable as platforms

### Bullet types (`main.py`)
- `Bullet`: normal orange 2×2, wall-dies, Wallbreaker sets `can_break_walls`
- `MissileBullet`: cyan 3×3, white center, DAMAGE=2, FREEZE_FRAMES=300
- `FractalBullet`: cyan/indigo pulse 3×3, follows Julia boundary waypoints, pierces terrain+enemies, emits `FractalBulletSmall` splinters, `synergy_wall_break` for Wallbreaker adjacency
- `FractalBulletSmall`: pink/red 2×2, straight-line, pierces terrain+enemies, never breaks walls
- Piercing: `hit_enemies` set on bullet; collision loop checks `getattr(b, 'piercing', False)`
- Splinters queued in `pending_splinters`; drained into `self.bullets` after update pass

### Game systems
- Smooth camera (33% from top bias)
- Pause menu: body grid + inventory panel; artifact drag-and-drop; synergy link drawn between qualifying adjacent cells
- F1 debug menu: toggle artifacts + immortality flag; gamepad: D-pad nav, A toggle, B/Start close
- Death: hp==0 → 1.5s death screen → Z-to-respawn (resets pos/hp/enemies)
- Missile canisters: 1/5 drop chance on kill; 10s lifetime, blinks last 3s; refills least-full missile
- Artifact pickup dialogue: Tab/Start to open body panel directly

## Key implementation notes

- `_try_ledge_grab`: skips if solid ground at `blocking_row+1` under player col (prevents 1-block grabs)
- `_occupied_rows(p)`: player can span 3 tile rows when not tile-aligned
- Wall jump: per-side cooldowns `wj_cd_l`/`wj_cd_r`
- `VampiricCape.draw_trail(cam)` called before player draw so player renders on top
- `FractalBlaster.draw_bg()` called after tile render but before entities (dithered overlay)
- `_ARTIFACT_POOL` controls world drop pool; `DEBUG_ITEMS` controls F1 menu
- ruff `# fmt: off`/`# fmt: on` guards around all intentionally aligned blocks
- `biome_trigger_cd=300` (5s) prevents banner re-triggering on boundary bounces
- `biome_banner_idx` frozen at trigger time — separate from `current_biome_idx` (stability)

# Current Context

Last updated: 2026-06-14

## What this project is

**Lithic Artifacts** — small pixel roguelike/platformer at GBA resolution (240×160).
Player descends through procedurally generated vertical dungeon collecting body-modifying artifacts.
"Break the game" emergent combos are the core appeal. Short sessions (<30 min). Cheap.

See `README.md` and `DESIGN-DECISIONS.md` for locked decisions.

## Tech stack

- Python, managed by `uv`
- Pyxel 2.9.6 (240×160). Palette is PICO-8 (`sprites.PALETTE`), set explicitly at init — Pyxel's default palette is different and every doc/sprite assumes PICO-8 indices
- Art pipeline: `assets/sprites/*.ppm` (LLM-authored text, PICO-8 RGB) → `sprites.load_all()` writes PNGs to gitignored `assets/img/` and loads bank 0 per `sprites.SHEET`; code uses `SPR[name]`. Use Fable-class models to author PPMs. Tiles are one set (5=fill,6=edge) palette-swapped per biome in `draw()`; variant picked by exposure: top > side (flipped for right) > fill
- Demos: `just demo <name>` runs `demos/<name>.py`; `main.Game` is importable (guarded by `__main__`, call `.run()`), so demos subclass it with a custom `_full_reset` scene and override the `_left/_right/...` input wrappers for scripted input
- Projectiles/particles are sprites: `sprites.blt_directional(base, ...)` picks `<base>-h/-v/-d` and flips by velocity; `blt_centered` + `frame()` for pulsing 3x3 bullets; particles use `spark-a/b/c` pal-swapped to their colour
- ARTIFACT warning: `Game.warn_pickup` = nearest uncollected pickup from 0.5 screens above to 1.5 below; first sighting sets `warn_timer` (fullscreen CICADAMATA-style alert, wordmark sprite scaled 2x); right-edge indicator persists while in range
- Startup splash: `splash_timer` (SPLASH_FRAMES=300) blocks update/draw; logo sprites `logo-emblem`, `wordmark-lithic/-artifacts`; warning text never flashes. Demos zero `splash_timer`
- Drop lane: `_draw_drop_lane` draws a dithered column at the tracked artifact's x behind entities; white when the player is lined up
- Feel: `COYOTE_FRAMES` / `JUMP_BUFFER` in constants.py; `Game._burst` particles, `Game.shake`, `Enemy.flash` for hit feedback
- `just run` to launch, `just fmt` to format (uses `uvx ruff`)

## Where the codebase is right now

### World / worldgen (`worldgen.py`)
- Infinite vertical dungeon, section-based (20-row sections)
- Section types: `open`, `platforms`, `chamber`, `cave` (Perlin noise, tile type 2)
- Cave sections: BFS traversability check + up to 15 retries; falls back to open
- `_is_traversable` now two-pass: Pass 1 finds all reachable states; Pass 2 verifies every reachable grounded state can also reach the section bottom (catches side-pocket soft-locks)
- `world.tiles`: `{(col, row): tile_type}` — 1 = platform, 2 = cave rock
- `world.solid()` checks `!= 0`; `world.destroy()` removes tiles
- Biome system: 5 biomes (Biomechanical Dungeon→Caverns→Abyss→Depths→Inferno), cycle every 6 sections; "ENTERING [NAME]" banner on transition (5s cooldown)

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
- Pause menu (Tab/Start): Body & Inventory / Keybinds / Quit (`pause_screen` = menu|body|keys); `input_device` tracks last-used kb/pad and `_hint(kb, pad)` picks hint text; body screen = body grid + inventory panel; artifact drag-and-drop; synergy link drawn between qualifying adjacent cells
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

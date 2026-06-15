# Done

- PyInstaller spec: added assets/ datas, collect_all for noise (C ext) and numpy; justfile gets clean/rebuild recipes; build/ dist/ added to .gitignore

- Variable jump height: release jump early clamps vy to JUMP_VEL_MIN (-1.5); full jump is JUMP_VEL (-4.5)

- Refactor: gameplay constants extracted to `constants.py`; all mirror defs and inline magic numbers replaced across main.py, worldgen.py, enemies.py, artifacts.py

- Refactor: synergy detection extracted to `synergies.py`; `fractal_wallbreaker_pairs/active(body_grid)` replace duplicated adjacency loops in main.py

- Seeded runs: DEFAULT_SEED=314159, seed shown in pause menu, F1→Restart[N] for full reset; special seeds 0 (wall playground), 1 (empty), 2 (gauntlet); SPECIAL-SEEDS.md created

- Bug: player couldn't pass 2-tile-high wall gaps — fixed `_occupied_rows` to use tile-row arithmetic (no float drift) + `_gap_snap` for airborne alignment assist

- Bug: cave soft-lock — two-pass BFS in `_is_traversable`: pass 1 collects all reachable states, pass 2 verifies every grounded reachable state can reach the section bottom; rejects side-pocket traps
- Synergy: FractalBlaster+Wallbreaker adjacent in body grid → FractalBullet/Small get 10% chance to destroy walls while piercing through them; pulsing pink (color 14) dithered line drawn between adjacent pair in body panel
- FractalBulletSmall splinters: FractalBullet emits 2 pink/red (color 14/8) splinters every 3rd waypoint advance (max 5 events); splinters pierce terrain+enemies, SPEED=2, LIFETIME=50, never break walls
- Debug menu gamepad support: D-pad Up/Down to navigate, A to toggle, B/Start to close; hint text updated
- Fractal Blaster artifact: shots trace real Julia set boundary (boundary cells extracted from cached grid, sorted by projection onto firing direction, bullet hops between waypoints); pierces enemies AND terrain; dithered Julia set background overlay on fire (3s fade, capped at 50% alpha; re-fire resets timer); slowly drifting c parameter
- Artifact pickup dialogue: Tab/Start now dismisses dialogue and opens body panel; hint text updated to show both options ("Z dismiss / Tab install")
- Missile refill canisters: 1/5 drop chance on enemy kill; refills 5 ammo to least-full equipped missile; 10s lifetime, blinks last 3s (6f on/off cyan/white), despawns on pickup or timeout
- Bug: frozen enemies now keep original sprite/glyph tinted blue (dither(0.5) navy overlay for Flyer sprite; cyan glyph color for text enemies); previously replaced with nav rect
- Bug: debug menu crash on immortality toggle — `isinstance(a, None)` called before `cls is None` guard; fixed by checking `cls is None` first
- Vampiric Cape trail fade: trail drains when player stops — 20f grace period then oldest ghost dropped every 12f; full trail clears ~2s after halting
- Frozen enemies (Ice Missiles): harmless platforms — skipped in contact damage check; floor collision added to `_move_y` (player lands on frozen enemy tops)
- Bug: Flyer/ShootyFlier phased through walls — destination-only check allowed sine to jump over walls when self.y was blocked for multiple frames; fixed by sweeping all tile rows between current and desired y
- Ice Missiles artifact: hold RB+Z to fire; 2 dmg + 5s freeze on hit; ammo=10/30; `~:XX` HUD right of HP bar (yellow in missile mode); SELECT cycles missile types; MissileArtifact base class for future types
- Biome transitions: 5 biomes (Dungeon→Caverns→Abyss→Depths→Inferno, cycles) every 6 sections; distinctive bg + tile colors per biome; "ENTERING [NAME]" modal on transition, 4s timer, re-triggers on backtrack

- Vampiric Cape artifact: SotN-style 8-ghost afterimage trail (dark navy→light gray, sampled every 3 frames); 1-in-3 heal on kill; `on_kill` hook added to Artifact base
- Player HP / death / respawn: die at 0 hp → 1.5s death screen → Z-to-respawn (resets pos/hp/enemies); immortality debug toggle in F1 menu
- Bug: 1-block ledge grab suppressed — check for solid ground under player at `blocking_row+1` prevents grabbing single-tile obstacles on jump frame
- Bug: pressing up while standing now shoots straight up (aim_dx=0, aim_dy=-1); running+up still shoots diagonally
- Cave worldgen: Perlin-noise cave sections (tile type 2, brown/dark-gray visuals), BFS traversability check with 15-retry fallback; `solid()` updated to `!= 0`; `noise` moved to main deps; `just fmt` fixed to use `uvx ruff`

- Player can't walk outside the world (hard clamp in `_move_x`)
- Wallbreaker artifact: shots destroy tiles on impact; walls are indestructible without it
- Bug: closing "ARTIFACT FOUND" dialogue no longer triggers a shot (shoot_cd reset on dismiss)
- Bug: can now aim down / diagonally down while running or airborne; down-press while running no longer crouches

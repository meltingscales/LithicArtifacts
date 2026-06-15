# Done

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

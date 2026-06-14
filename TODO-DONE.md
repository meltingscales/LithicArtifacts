# Done

- Bug: 1-block ledge grab suppressed — check for solid ground under player at `blocking_row+1` prevents grabbing single-tile obstacles on jump frame
- Bug: pressing up while standing now shoots straight up (aim_dx=0, aim_dy=-1); running+up still shoots diagonally
- Cave worldgen: Perlin-noise cave sections (tile type 2, brown/dark-gray visuals), BFS traversability check with 15-retry fallback; `solid()` updated to `!= 0`; `noise` moved to main deps; `just fmt` fixed to use `uvx ruff`

- Player can't walk outside the world (hard clamp in `_move_x`)
- Wallbreaker artifact: shots destroy tiles on impact; walls are indestructible without it
- Bug: closing "ARTIFACT FOUND" dialogue no longer triggers a shot (shoot_cd reset on dismiss)
- Bug: can now aim down / diagonally down while running or airborne; down-press while running no longer crouches

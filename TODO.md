# TODO

## Artifacts
- Fractal Blaster: piercing shots that trace a constantly-shifting Julia set outline
- Ice Missiles: [TBD]

## Gameplay
- Player HP / death / respawn
- Floors / progression (floor counter, difficulty scaling)

## Worldgen
- Organic cave variety (more section types: shafts, puzzle chambers)
  - worldgen should be minecraft-esque in that we use perlin noise to generate cave-like structures.

- Floor/biome transitions after every N sections
  - transitioning biomes/floors shows a small center-screen modal like in Castlevania when areas change (no pause).
  - it doesn't expire, so re-visited areas will keep the same transition effect.

- Difficulty scaling: denser spawns + harder enemies deeper down

## Other
- Make sure assets/ is included in .spec file

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.

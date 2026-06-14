# TODO

## Bugs

None yet.

## Artifacts
- Fractal Blaster: piercing shots that trace a constantly-shifting Julia set outline
- Ice Missiles: [TBD]

## Gameplay
- Player HP / death / respawn
- Floors / progression (floor counter, difficulty scaling)

## Worldgen
- Organic cave variety (more section types: shafts, puzzle chambers)
  - worldgen should be minecraft-esque in that we use perlin noise to generate cave-like structures, instead of only random platforms.
    - for now, use different block sprites for platforms vs. cave blocks. we will add real art later.
    - to guarantee traversability, we need to use a pathfinding algorithm to ensure the player can always reach below what we generated.
    - the pathfinding algorithm should be able to handle obstacles (cave blocks) and generate a valid path for the player to follow.
    - if it fails, we re-generate the section and try again.

- Floor/biome transitions after every N sections
  - transitioning biomes/floors shows a small center-screen modal like in Castlevania when areas change (no pause).
  - it doesn't expire, so re-visited areas will keep the same transition effect.

- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.

## Visuals/Aesthetic

- Moving should leave an afterimage/trail behind you, Castlevania: Symphony of the Night - similar to the trail effect seen in Castlevania: Symphony of the Night.  <https://www.youtube.com/watch?v=qmDrNeoD2X0> - see LithicArtifacts/art-direction/sotn-trail.png

## Other
- Make sure assets/ is included in .spec file

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.

# TODO

## Bugs

- Cave generation is a bit too sparse, the world feels empty. Bump it up a little bit.

## Artifacts
- Fractal Blaster: piercing shots that trace a constantly-shifting Julia set outline
- Ice Missiles: [TBD]

## Gameplay
- Player HP / death / respawn
- Floors / progression (floor counter, difficulty scaling)

## Worldgen
- Floor/biome transitions after every N sections
  - transitioning biomes/floors shows a small center-screen modal like in Castlevania when areas change (no pause).
  - it doesn't expire, so re-visited areas will keep the same transition effect.

- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.

## Visuals/Aesthetic

- New Artifact: Vampiric Cape (gives change for heal on kills), also does this: Moving should leave an afterimage/trail behind you, Castlevania: Symphony of the Night - similar to the trail effect seen in Castlevania: Symphony of the Night.  <https://www.youtube.com/watch?v=qmDrNeoD2X0> - see LithicArtifacts/art-direction/sotn-trail.png

## Other
- Make sure assets/ is included in .spec file

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.

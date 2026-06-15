# TODO

## Bugs

<!--None yet.-->


## Gameplay
- Floors / progression (floor counter, difficulty scaling)

- Jumping should be able to be partial, based on how long the jump button is held down.

## Worldgen
- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.

## Visuals/Aesthetic

<!--None yet.-->

## Artifacts

Mechaspider legs
- Spidertron climbing legs
- Anchor or traverse blocks
- Similar animation to factorio spidertron 
- Procedurally generated climbing animation with eight legs 


Jump sphere
- Simple double jump

Viv Wings
- Short flight after single or double jump
- Wireframe esque like Viv ribbon, dithered too


## Other
- Make sure assets/ is included in .spec file

- Seeded runs with seed visible in pause menu
  - we should also seed all RNG with an int
  - by default, it's `314159`

- Debug F1 menu lets you also reset the game with a specific seed.

- Special seeds for testing should exist:
  - `0`: Wall playground with many different types of walls to test wall phasing and collision detection.
  - `1`: Empty world with no walls to test floor progression and artifact spawning.
  - `2`: "Gauntlet" seed with all enemy types in different chambers, to test combat mechanics.

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.

- Question: Should we make these python scripts into their own module in `./lithicartifacts/`?

## Core

- Pull RNG-related things out into CONSTANTS_NAMED_LIKE_THIS in `rng.py` so we can easily tweak them. Things like worldgen, item spawn chances, etc.

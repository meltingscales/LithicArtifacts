# TODO

## Bugs

<!--None yet.-->

- Player can't go through 2-block-high gaps in walls. Maybe lower their pushbox height very slightly? Or suggest another fix.

- It's possible for the player to get stuck if they go into a cave that's deep but has no exit. How can we update our worldgen search-tree algorithm to account for this and reject caves that would soft-lock the player?

## Gameplay
- Floors / progression (floor counter, difficulty scaling)


## Worldgen
- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.

## Visuals/Aesthetic

<!--None yet.-->


## Other
- Make sure assets/ is included in .spec file

- Seeded runs with seed visible in pause menu
  - we should also seed all RNG with an int
  - by default, it's `314159`

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.

- Question: Should we make these python scripts into their own module in `./lithicartifacts/`?

## Core

- Pull RNG-related things out into CONSTANTS_NAMED_LIKE_THIS in `rng.py` so we can easily tweak them. Things like worldgen, item spawn chances, etc.

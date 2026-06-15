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


## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.

- Question: Should we make these python scripts into their own module in `./lithicartifacts/`?

## Core

- Pull RNG-related things out into CONSTANTS_NAMED_LIKE_THIS in `rng.py` so we can easily tweak them. Things like worldgen, item spawn chances, etc.
  - also store special seeds as constants in `rng.py`

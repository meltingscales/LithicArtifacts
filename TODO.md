# TODO

## Bugs

None yet.

## Artifacts
- Fractal Blaster: piercing shots that trace a constantly-shifting Julia set outline
  - firing it briefly renders a dithered, rendered julia set in the background with the same constants as the current shot (both the outline and background julia set follow the same slowly drifting parameters)
    - the background julia set should fade out smoothly within 3 seconds. re-firing the Fractal Blaster just clamps the fadeout to the top value again.


## Gameplay
- Floors / progression (floor counter, difficulty scaling)



## Worldgen
- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.

## Visuals/Aesthetic

<!--None yet.-->


## Other
- Make sure assets/ is included in .spec file

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.


## Core

- Pull RNG-related things out into CONSTANTS_NAMED_LIKE_THIS in `rng.py` so we can easily tweak them. Things like worldgen, item spawn chances, etc.

# TODO

## Bugs
<!--None yet.-->

## Gameplay
- Floors / progression (floor counter, difficulty scaling)


## Worldgen
- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.
  - artifact drop table chances in constants.py with biome modifier chance dict

## Visuals/Aesthetic
None yet.

## Synergies
None yet.

## Artifacts
None yet.

Long jump
- Doubles jump height, just like in metroid

Jump sphere
- Simple double jump

Viv Wings
- Short flight after single or double jump
- Wireframe esque like Viv ribbon, dithered too
  - flap animation when using
  - folded sprite when not in use

## Enemies

The fliers should have an idle animation (sine wave flight) until they see you (within 4 tiles). Then, they should signal to the player that they are ready to attack, and then swoop towards you briefly. Then resume their pre-programmed flight pattern/attack pattern.

## Bosses

None yet.

## Other

None yet.

## Later

- Add UI scrolling to the debug menu (as it will grow too large eventually)

- Set up GitHub CICD
  - should release a windows, linux, and macos version using pyinstaller

- set up steam packaging
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.


- Rework MechaspiderLegs artifact
  - create entire separate test harness and game chamber until we get the movement and physics and rendering working perfectly.

## Core/Architecture

## For me

Actually learn how to create pixel art.

Focus on 8x8 sprites.

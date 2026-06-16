# Art Direction Prompts

## Tools

- Aseprite
- GIMP

## Workflow

Still in progress. Idea: Use prompts to generate high-res images, then downscale them into 64x64 sprites using some tool and nearest-neighbor (not bilinear), do cleanup/tiling, then do further cleanup in some tool and downscale again into 8x8/8x16 sprites using GIMP and nearest-neighbor.

## Overview

Prompts for generating pixel art assets via [RetroDiffusion](https://retrodiffusion.ai/) or similar tools.

All sprites target the **Pyxel 16-color palette** at **GBA resolution (240×160)**. Tile size is **8×8 px**. Player is **8×16 px** (two tiles tall).

## Palette (Pyxel default)
```
0  = black
1  = dark navy
2  = dark purple
3  = dark green
4  = brown
5  = dark gray
6  = light gray
7  = white
8  = red
9  = orange
10 = yellow
11 = lime green
12 = cyan
13 = indigo/slate blue
14 = pink/magenta
15 = peach/skin
```

## Existing sprites (skip these)
- `assets/img/flyer.png` — Flyer enemy (8×8, 2-frame wing animation) ✓

## Files in this folder
- `player.md` — Player character: all states and artifact mutations
- `enemies.md` — Crawler (8×8), ShootyFlier (16×8)
- `tiles-biomechanical.md` — Biome 1: wet metal and flesh
- `tiles-wet-stone.md` — Biome 2: dripping cave rock
- `tiles-ancient-ruins.md` — Biome 3: pre-human carved stone
- `artifacts.md` — Artifact item sprites (8×8 pickup icons)
- `ui.md` — UI chrome: HP blocks, panel borders, dialogue frames

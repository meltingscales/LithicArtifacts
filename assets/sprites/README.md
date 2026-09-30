# Sprites

All game art lives here as **P3 PPM text files**, one sprite per file. PPMs are
plain text, so a language model can author and edit them directly, and diffs
are readable. No image-generation models, no upscaling/downscaling pipeline.

## Why text PPMs

The previous approach (AI image generation, then downscale to 8x8) produced
mush: soft edges, off-palette colours, sprites that did not tile. An 8x8 sprite
is 64 pixels. A capable text model can place 64 pixels deliberately, name the
colour of each one, and revise a single pixel on request.

**Use Claude Fable (or a comparably capable model) to author PPMs.** Smaller
models lose track of row widths and palette roles; the result looks like noise.

## Pipeline

1. `assets/sprites/<name>.ppm` is the source.
2. `sprites.SHEET` in `sprites.py` maps each name to its slot in Pyxel image bank 0.
3. At startup `sprites.load_all()` converts every PPM to an indexed PNG under
   `assets/img/` (gitignored, regenerated every run) and loads it.
4. Code draws by name: `u, v, w, h = SPR["crawler-a"]`.

Adding a sprite = write the PPM, add one line to `SHEET`, use `SPR[name]`.

## Authoring rules

- Format: `P3`, a `# name: description` comment on line 2, then `W H`, `255`,
  then one text row per pixel row with `R G B` triples.
- Colours must be exact PICO-8 RGB values (table below). Index 0 (black) is
  the transparency key for every sprite; tiles are fully opaque.
- Sizes: 8x8 for tiles, enemies, icons; 8x16 for the player (head tile on top
  of body tile); 16x8 for wide fliers. Wide sprites are centred over an 8x8 hitbox.
- Author facing **right**. Code flips with a negative blit width.
- Tiles use canonical roles: 5 = fill, 6 = edge/highlight, 1 = shadow. `main.py`
  palette-swaps 5 and 6 per biome, so one tile set serves every biome. Variants:
  `tile-top` (open above), `tile-side` (open on the left; flipped for right),
  `tile-fill` (enclosed), `tile-rock` (cave, tile type 2).
- Keep silhouettes readable at 1x: one colour for the mass, one for a highlight,
  one accent. Three colours beat six.
- Player things lean yellow/orange, hostile things red/dark, world tiles gray.

## Palette (PICO-8)

```
 0 black         0   0   0      8 red        255   0  77
 1 dark blue    29  43  83      9 orange     255 163   0
 2 dark purple 126  37  83     10 yellow     255 236  39
 3 dark green    0 135  81     11 green        0 228  54
 4 brown       171  82  54     12 blue        41 173 255
 5 dark gray    95  87  79     13 indigo     131 118 156
 6 light gray  194 195 199     14 pink       255 119 168
 7 white       255 241 232     15 peach      255 204 170
```

## Quick preview

```
uv run python -c "import sprites; print(sprites.read_ppm('assets/sprites/crawler-a.ppm'))"
```

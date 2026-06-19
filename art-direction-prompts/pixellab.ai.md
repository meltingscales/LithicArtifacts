# Pixellab.ai Prompt Styles

10 prompt framings for the same subject — use whichever gets the best result
from your tool. Test subject used throughout: **8×8 biomechanical dungeon wall tile**.

Aesthetic reference: dark purple-gray fill, cold metallic border, rivets over wet
muscle, bioluminescent cracks. Pyxel 16-color palette. GBA resolution.

---

## 1 — ComfyUI / SD Tag Soup

Best for: ComfyUI + PixelartSpritesheet + PixelArtRedmond LoRA

```
pixel art, 8x8 tile sprite, biomechanical wall, metal rivets, wet muscle underneath,
bioluminescent fluid in cracks, dark purple-gray, cold metallic border, GBA game,
PixelartSpritesheet, PixelArtRedmond, retro sprite sheet, hard pixel edges,
no anti-aliasing, limited 16-color palette, black background,
(masterpiece:1.1), (crisp pixels:1.2)
```

Negative:
```
blurry, gradient, smooth, anti-aliasing, photorealistic, 3D render, noise,
watermark, text, high resolution detail, dithering, glow, lens flare, JPEG artifacts
```

---

## 2 — Natural Language (Midjourney / GPT-Image style)

Best for: tools that prefer sentence-form descriptions

```
An 8×8 pixel art tile for a biomechanical dungeon wall. The tile is mostly dark
purple-gray with a thin cold metallic border. Visible rivets hold metal plating
over what looks like wet, dark muscle underneath. A hairline crack glows faintly
with bioluminescent teal. Hard pixel edges, no anti-aliasing, limited palette,
black background.
```

---

## 3 — Director's Brief (high-concept, mood-first)

Best for: tools that respond well to intent and atmosphere over technical specs

```
This tile is part of a living facility. The walls breathe. Metal was bolted onto
flesh that wasn't dead when they did it. Show me the seam where engineering meets
biology — cold rivets, dark stain, a crack that glows wrong. 8 pixels. Make it
feel claustrophobic and ancient and wrong.
```

---

## 4 — Reference-Anchored

Best for: tools with strong training on known games/art

```
8×8 pixel art tile in the style of Metroid Fusion's interior corridors crossed
with Caves of Qud's biomechanical aesthetic. Dark purple-gray like SR388's depths.
Metal panel with visible biology underneath. Teal bioluminescent crack. GBA color
depth — roughly 16 colors. Hard edges, no smoothing.
```

---

## 5 — Technical Spec Sheet

Best for: structured tools or when you want precise reproducibility

```
Format:       8×8 pixels, PNG, black background (colkey=0)
Palette:      Pyxel 16-color (closest match to target)
Subject:      Wall tile, biomechanical dungeon biome
Fill color:   Dark purple-gray (#393960 approx)
Border color: Cold metallic gray-blue (#A9C1FF approx)
Details:      2–3 rivet pixels (white/light gray), 1 bioluminescent crack (teal #197F9C)
Style:        Hard pixel edges, no anti-aliasing, no gradients
```

---

## 6 — Contrast Pair (what it is vs. what it isn't)

Best for: models that respond well to contrastive framing

```
An 8×8 pixel tile that looks mechanical but feels organic. Not a clean sci-fi panel —
more like something grew around the metal. Not bright or sterile — dark, damp, old.
Not smooth — every edge is a hard pixel boundary. The glow in the crack isn't light,
it's something secreted. Biomechanical dungeon wall. GBA pixel art.
```

---

## 7 — Material Description

Best for: tools that handle material/surface language well

```
8×8 pixel art tile. Surface: corroded dark steel plate, matte, cold. Substructure:
dense dark muscle or chitinous organic matter visible at seams. Fasteners: 2px
square rivets, oxidized silver. Damage: single hairline fracture emitting teal
phosphorescence. Ambient: no reflected light. Palette: 4–5 colors max from a
16-color set. GBA game tile.
```

---

## 8 — Iterative Refinement Seed

Best for: starting point when you don't know what you want yet — refine from here

Round 1 (broad):
```
8x8 pixel art, dark wall tile, sci-fi organic, GBA style
```

Round 2 (add material):
```
8x8 pixel art, biomechanical wall tile, metal over muscle, dark purple, GBA sprite
```

Round 3 (lock details):
```
8x8 pixel art, biomechanical dungeon wall, dark purple-gray fill, metallic border,
2 rivets, teal glowing crack, no anti-aliasing, black background, retro game tile
```

---

## 9 — Palette-Locked

Best for: when color accuracy matters most — use exact Pyxel hex values in prompt

```
8×8 pixel art tile. Use only these colors:
- #000000 (black) — background and deep shadow
- #393960 (dark navy) — primary fill
- #A9C1FF (light blue) — metallic border highlight
- #197F9C (teal) — bioluminescent crack glow
- #A3A3A3 (gray) — rivet and edge detail

Subject: biomechanical wall tile with rivets and a cracked glowing seam.
Hard pixel boundaries. No colors outside the list above.
```

---

## 10 — Narrative Context

Best for: tools that use narrative/world context to steer output

```
You are generating sprites for a GBA-style body-horror platformer. The player
descends through a facility that is partially mechanical, partially alive. The
walls in the first biome — the Biomechanical Dungeon — are made of metal plating
bolted over organic matter that still pulses. Generate one 8×8 wall tile for
this biome. It should feel oppressive and wrong, but readable as a tile at
small scale. Dark palette. Hard pixel edges.
```

---

## Cross-tool notes

| Style | Best tool |
|---|---|
| 1 — Tag soup | ComfyUI + SD LoRA |
| 2 — Natural language | Pixellab.ai, GPT-4o image, Midjourney |
| 3 — Director's brief | Claude/GPT → then feed output into image gen |
| 4 — Reference-anchored | Midjourney, Leonardo.ai |
| 5 — Spec sheet | Any; most reproducible across sessions |
| 6 — Contrast pair | Midjourney, Ideogram |
| 7 — Material description | Stable Diffusion, Firefly |
| 8 — Iterative seed | Any — use when starting cold |
| 9 — Palette-locked | Tools with color control; DALL-E 3 ignores this |
| 10 — Narrative context | GPT-4o image, Claude image gen, Gemini |

After generating, run:
```bash
python localai-pixel-art/quantize_sprite.py input.png assets/img/mytile.png --size 8x8
```

# Lithic Artifacts

A tiny roguelike about finding cursed body modifications and breaking yourself in interesting ways.

Inspired by **Caves of Qud**, **Metroid Fusion**, **the original Rogue**, and **LithicRivers**.

---

## Concept

You descend into a short dungeon (5–10 floors). The dungeon is simple. The enemies are simple. The point is the **artifacts** — strange body modifications you find along the way.

Artifacts do things to your body: extra limbs, acid blood, magnetic hands, phase shifting, regeneration. They have hidden properties that interact with each other in ways the game doesn't explain. You discover the interactions yourself. Some of them are broken. That's the point.

When you find a combination the game considers aberrant, it tells you. Then it throws harder enemies at you.

## Aesthetics

- **GBA resolution: 240×160**
- Chunky tile-based rendering, limited palette
- ASCII/symbol-forward — characters and creatures are glyphs, not sprites
- Influenced by the original Rogue's austerity

## Design Pillars

- **Random discovery over deliberate builds** — artifacts are found, not chosen from a menu
- **Emergent interactions over designed synergies** — the game has rules; players find the cracks
- **Short sessions** — a full run should take under 30 minutes
- **Simple and cheap** — this is a small game, intentionally

## Scope

| Thing | Scope |
|---|---|
| Dungeon floors | 5–10 |
| Enemy types | ~10 |
| Artifacts | ~30–40 |
| Documented synergies | Few |
| Emergent/broken combos | Many |

## Rendering

- Pixel-rendered at native **240×160** (GBA resolution), scaled up to window
- Limited color palette enforced aesthetically (targeting ~16–256 colors on screen)
- Tile-based: creatures and terrain are small pixel sprites on a grid

## Engine

**Pyxel** (Python)

- Native 240×160 canvas, scaled to window
- 16-color palette (customizable)
- Built-in tilemap and sprite editor (`.pyxres` resource files)
- `pip install pyxel`

```python
import pyxel
pyxel.init(240, 160, title="Lithic Artifacts")
```

## Status

Early concept. Not yet started.

## Influences

| Game | What we're stealing |
|---|---|
| Caves of Qud | Body modification system, emergent mutation interactions |
| Metroid Fusion | Body horror aesthetic, organism absorption, sense of dread |
| Rogue (1980) | Austerity, random item discovery, permadeath |
| LithicRivers | Aesthetic sensibility, terminal-forward thinking |
| Noita | Rewarding the player for breaking the game |

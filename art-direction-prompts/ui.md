# UI Element Prompts

**Style:** Metroid Fusion × Castlevania SotN — stark, functional, dark panels, fine borders
**Palette:** dark gray (5) backgrounds, light gray (6) borders, yellow (10) active, orange (9) accents
**Rule:** single-pixel `rectb` borders only. No rounded corners. No gradients.

These are small decorative/texture elements to inform hand-crafted UI; most UI is drawn in code.

---

## HP Block (full)
```
4x4 pixel art icon, small solid HP health block,
filled yellow square with single orange highlight pixel top-left,
dark gray single-pixel border, black background,
GBA HUD element, Metroid Fusion health bar aesthetic
```

## HP Block (empty)
```
4x4 pixel art icon, small depleted HP health block,
dark gray fill with slightly lighter gray border,
hollow or dim feel, no highlight,
black background, GBA HUD element
```

## Body Panel Corner Decoration
```
8x8 pixel art tile, UI panel corner piece for body modification grid,
single-pixel light gray border lines forming an L-corner,
dark gray or black fill, optional small circuit-trace detail,
GBA-era UI chrome, Metroid Fusion pause menu aesthetic
```

## Artifact Dialogue Frame (top strip)
```
16x8 pixel art tile, top edge of artifact pickup dialogue modal,
yellow single-pixel border top and sides, black fill,
intended to tile horizontally across 240px screen width,
GBA pixel art, stark modal dialogue header,
Metroid Fusion item-get screen influence
```

## Artifact Slot (empty cell)
```
8x8 pixel art tile, empty artifact body-grid cell,
dark gray fill, single-pixel light gray border on all sides,
subtle inner shadow or recess implied (1px darker inner edge),
GBA pixel art UI, body modification panel, Caves of Qud body-slot aesthetic
```

## Artifact Slot (occupied — glow state)
```
8x8 pixel art tile, occupied artifact body-grid cell with active artifact,
dark background, yellow border pulsing (show one phase),
small orange inner glow pixel at corners,
GBA pixel art UI, Metroid Fusion active item slot
```

## Synergy Link Dot
```
4x4 pixel art icon, small connection node for synergy line endpoints,
pink or cyan filled circle (2px solid center, 1px border),
placed at artifact slot centers when synergy active,
black background, GBA pixel art, body panel UI decoration
```

# Art Direction — Lithic Artifacts

## Aesthetic Statement

A body-horror platformer that feels like Metroid Fusion crossed with Caves of Qud:
oppressive and lonely like Fusion, but weird and colorful like Qud. The world is
ancient, hostile, and alive in ways that are wrong. The player character is visibly
changing as artifacts accumulate on their body.

---

## Canvas & Resolution

| Property | Value |
|---|---|
| Resolution | 240 × 160 px (GBA native) |
| Tile size | 8 × 8 px |
| Grid | 30 × 20 tiles |
| Palette | Pyxel default 16-color |
| Scale | Integer-scaled up for display |

---

## Color Palette Usage

Pyxel's fixed 16-color palette. Colors are assigned roles, not used freely.

| Role | Color(s) | Notes |
|---|---|---|
| Background / void | Black (0) | Fills all unlit space |
| World tiles (shadow) | Dark gray (5) | Tile fill |
| World tiles (edge) | Light gray (6) | Tile border / highlight |
| Player | Yellow (10) | Dominant player color; warm against cold world |
| Player accent | Orange (9) | Secondary — gun flash, highlights |
| Bullets | Orange (9) | Player projectiles |
| Enemy bullets | Red (8) | Hostile projectiles, always red |
| UI chrome | Light gray (6) | Borders, inactive labels |
| UI active / selected | Yellow (10) | Cursor, active panel title |
| UI accent | Orange (9) | Held items, warnings |
| UI dimmed | Dark gray (5) | Inactive / disabled text |
| Artifact pickups | Yellow ↔ Orange | Alternating pulse |
| Damage flash | Red (8) | Enemy contact |
| HP full | Yellow (10) | HP HUD blocks |
| HP empty | Dark gray (5) | HP HUD blocks |

Enemies, artifacts, and the player mid-sprite use additional palette colors for
detail — see per-entity notes below. The rule is: **hostile things lean red/dark,
player things lean yellow/orange, world tiles lean gray**.

---

## Sprite Dimensions

| Entity | Size | Notes |
|---|---|---|
| World tile | 8 × 8 px | Solid fill + border; no sub-tile detail yet |
| Player | 8 × 16 px | Two-tile tall; head (top 8px) + body (bottom 8px) |
| Crawler | 8 × 8 px | Ground-hugging; wide, low silhouette |
| Flyer | 8 × 8 px | Compact; wings implied by frame animation |
| ShootyFlier | 16 × 8 px | Wider than a tile; protrudes to show it shoots |
| Artifact pickup | 8 × 8 px | Glyph on pedestal; pedestal is a standard tile |
| Enemy bullet | 2 × 2 px | |
| Player bullet | 2 × 2 px | |

**Current state:** all entities render as Pyxel text glyphs (`@`, `W`, `c`, `f`, `F`).
Pixel sprites are the roadmap target; glyph rendering is a placeholder.
The sprite sheet grid is 8 × 8 px cells regardless.

---

## Player Character

An armored humanoid explorer whose body is being modified by the artifacts they carry.
Mutations and grafts should be **visibly present on the sprite** — extra limbs, fused
metal, organic protrusions — reflecting the equipped artifact loadout.

- **Head tile (top):** helmet or exposed face; always the `@` or equivalent silhouette
- **Body tile (bottom):** legs + torso; changes posture by state (stand, crouch, hang, burrow)
- **Palette:** primarily yellow, with orange trim and 1–2 accent colors for mutation detail
- **Crouch:** body tile replaced by a compressed single tile (player becomes 8 × 8)
- **Burrow:** body tile shows downward-drilling glyph/animation

---

## Enemies

### Crawler
Low, chitinous ground creature. Walks back and forth on platforms.
- **Silhouette:** wide and flat, multi-legged
- **Palette:** dark purple + gray; red eyes
- **Animation:** legs cycling; turns smoothly at ledge edges

### Flyer
Winged organic form; drifts toward the player with a sinusoidal bob.
- **Silhouette:** small body, large membranous wings
- **Palette:** dark teal + light gray; single glowing eye (yellow or green)
- **Animation:** wings flap 2-frame cycle; bob driven by code not animation

### ShootyFlier
Larger Flyer variant with a visible weapon protrusion. Wider sprite (16 px).
- **Silhouette:** asymmetric — one side has a gun-arm or maw that fires
- **Palette:** same base as Flyer but with red weapon accent
- **Tell:** the weapon glows orange briefly before firing

---

## World Biomes

Sections cycle through three biome themes as the player descends. Each biome spans
roughly 5–8 sections before transitioning. The tile border color and fill tint shift
to signal the new environment.

### 1 — Biomechanical (shallowest)
The facility or organism the player is inside is partially mechanical, partially alive.
Tubes pulse. Metal plating is bolted over wet muscle.

- **Tile fill:** very dark purple-gray
- **Tile border:** cold metallic gray or sickly green
- **Accent details:** rivets, conduits, bioluminescent fluid in cracks
- **Mood:** claustrophobic, alien, wrong

### 2 — Wet Stone (mid-depth)
Natural cave systems beneath the structure. Water drips. Moss clings to cracked rock.
Remnants of the biomechanical layer still appear as rusting intrusions.

- **Tile fill:** dark blue-gray
- **Tile border:** lighter blue-gray or near-white
- **Accent details:** water droplets, hanging moss, dim reflected light on floors
- **Mood:** vast and cold; the sounds change here

### 3 — Ancient Lithic Ruins (deepest)
Pre-human or non-human architecture. Massive carved stone blocks. Glyphs that predate
any known language. The artifacts the player is carrying were made here, or came from
something that was.

- **Tile fill:** deep ochre-brown
- **Tile border:** pale sand or faded red
- **Accent details:** carved geometric relief, cracked pillars, faint phosphorescent lichen
- **Mood:** reverent dread; Caves of Qud's "you are small, this is old"

---

## UI

Inspired by Metroid Fusion and Castlevania: Symphony of the Night — stark, functional,
dark-background panels with fine borders.

- **HP HUD:** row of small blocks at bottom-left; yellow = full, dark gray = depleted
- **Body panel (pause):** two-column layout — 5×5 grid left, inventory list right
- **Tooltip:** appears after 3 seconds of hovering; light gray text on black
- **Dialogue (artifact pickup):** centered modal with yellow border; world visible behind it
- **Debug menu:** gray-bordered overlay; dev-only

Panel borders use single-pixel `rectb`. No rounded corners. No gradients.
Text is Pyxel's built-in 4×6 px font.

---

## Atmosphere & Mood Reference

| Feeling | Source | How it lands here |
|---|---|---|
| Alone in a hostile place | Metroid Fusion | Silence between encounters; sparse color |
| Your body is not entirely yours | Metroid Fusion + CoQ | Visible artifact mutations on sprite |
| Reverent weirdness | Caves of Qud | Ancient ruins biome; artifact lore |
| Vertical momentum and dread | Downwell | Camera bias downward; falling into the unknown |
| Breaking things feels good | Noita | Artifact combos that visibly escalate the world |

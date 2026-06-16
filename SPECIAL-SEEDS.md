# Special Seeds

Certain integer seeds produce hand-designed worlds instead of standard procedural
generation. Activate via **F1 → Restart [N]** in-game.

The default seed is **314159**.

---

## Seed 0 — Wall Playground

Preamble: four vertical walls (cols 6, 12, 18, 24) each with a 2-tile-high gap at a
different height (rows 3–4, 5–6, 2–3, 4–5). Solid floor at row 12 with a centre gap
(cols 13–16) to descend to the section below.

Section 0: solid floor with 1-block pillars every 3 columns — verifies `_gap_snap`
does not auto-climb 1-tile obstacles. Sections 1+ are normal.

**Use for:** gap traversal, `_gap_snap` behaviour, 1-block step collision, SpiralBorer
floor phasing.

---

## Seed 1 — Empty World

Every section strips all interior tiles — only the left/right boundary walls remain.
No enemy spawns. Artifacts still drop on schedule.

**Use for:** floor progression, camera behaviour, artifact pickup flow, and any
feature that needs an uncluttered space.

---

## Seed 2 — Gauntlet

Every section gets one Crawler, one Flyer, and one ShootyFlier added on top of
whatever the normal generator produces.

**Use for:** combat tuning, enemy interaction testing, artifact damage output.

---

## Seed 3 — All Items

One hand-crafted room per artifact in `_ARTIFACT_POOL`. No enemies.

Room layout per section:
- **Left half (cols 1–14):** zigzag stair ledge — alternates high (row +5) / low
  (row +13) each section, so the player must jump down and across to descend.
- **Divider (col 15):** solid wall with a 3-tile gap at rows +7 to +9 — enter the
  right zone by walking through the gap.
- **Right half (cols 16–28):** open room with a solid floor and an artifact pedestal
  centred on that floor.

Generation stops after all artifacts are shown.

**Use for:** artifact testing, pickup flow, body-panel interaction, synergy testing.

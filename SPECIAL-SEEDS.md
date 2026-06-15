# Special Seeds

Certain integer seeds produce hand-designed worlds instead of standard procedural
generation. Activate via **F1 → Restart [N]** in-game.

The default seed is **314159**.

---

## Seed 0 — Wall Playground

Preamble contains four vertical walls (cols 6, 12, 18, 24) each with a 2-tile-high
gap at a different height (rows 3–4, 5–6, 2–3, 4–5). Sections below are normal.

**Use for:** gap traversal, `_gap_snap` behaviour, SpiralBorer floor phasing,
collision edge cases.

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

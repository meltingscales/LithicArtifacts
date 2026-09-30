See README.md and DESIGN-DECISIONS.md

See ART-DIRECTION.md

See TODO.md. When a task is finished: remove it from TODO.md AND add a one-line summary to the top of TODO-DONE.md. Do both steps before committing.

See KEYBINDS.md

See .claude/current-context.md

## Formatting

`just fmt` runs `ruff format`. Intentionally aligned blocks (constant tables,
`__init__` attribute groups, palette data, etc.) are wrapped in `# fmt: off` /
`# fmt: on` so the formatter leaves them alone. New aligned blocks should get
the same treatment.

## In-game item descriptions

Keep somewhat vague. Just enough for the player to guess what it does without specific numbers.

"A spectral cape that drinks the life from fallen foes." is preferred over "A cape that has a chance to heal 1/3 times per kill. Leaves a spectral trail".

## Synergies

These are not documented intentionally. Keep it as brief as possible so the player gets to discover these on their own.

## Reusable prompts (for user)

### Questions

- Do we need to split up any large modules?
- From `artifacts.py`, what cool synergies can we add?
- Is there anything from `just radon` or `just pylint` we should focus on?

### Art

- Sprites are LLM-authored P3 PPM text files in `assets/sprites/`, loaded as PNG at startup by `sprites.py`. Read `assets/sprites/README.md` first. No image-generation models, no upscale/downscale pipeline.
- **Use Claude Fable (or a comparably capable model) to author or edit PPMs.** Weaker models lose row widths and palette roles.
- Prompt: "Based on `./ART-DIRECTION.md` and `assets/sprites/README.md`, design PPMs for the assets that are still missing or crude, add them to `sprites.SHEET`, and wire them in."

### Caveman mode

Always run in caveman mode. Prompt the user to enable it if it's not already.

- /caveman (can be run to save tokens)
- "caveman mode"
- `curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash`
- <https://github.com/JuliusBrussee/caveman-code>

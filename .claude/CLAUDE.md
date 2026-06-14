See README.md and DESIGN-DECISIONS.md

See ART-DIRECTION.md

See TODO.md. Finished items go in TODO-DONE.md

See KEYBINDS.md

See .claude/current-context.md

## Formatting

`just fmt` runs `ruff format`. Intentionally aligned blocks (constant tables,
`__init__` attribute groups, palette data, etc.) are wrapped in `# fmt: off` /
`# fmt: on` so the formatter leaves them alone. New aligned blocks should get
the same treatment.

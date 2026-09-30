Self-contained demos of specific mechanics should go here.

Things like new rendering ideas, physics simulations, and artifact demonstrations.

It should be possible to run these demos completely independently of the main game.

`just demo` with no name lists demos, using line 2 of each file (the first docstring line) as the description. Run one with `just demo <name>` (e.g. `just demo mechaspider`, add `--headless` for a printed trace).

- `mechaspider.py` — wall-climb scene with scripted input and a debug overlay; flags snaps, state conflicts and climbing without a wall.

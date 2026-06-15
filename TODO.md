# TODO

## Bugs

<!--None yet.-->
- Frozen enemy sprites shouldn't be replaced with a glyph, but the same sprite they already have, just tinted blue.

- Sometimes, sinusoidal-movement-type enemies will phase through walls.

- Choosing immortality in the debug menu has a bug: 
    ~/Git/LithicArtifacts master* ⇡
    ❯ just run
    uv run python main.py
    Traceback (most recent call last):
      File "/home/henrypost/Git/LithicArtifacts/main.py", line 902, in update
        self._update_debug()
        ~~~~~~~~~~~~~~~~~~^^
      File "/home/henrypost/Git/LithicArtifacts/main.py", line 355, in _update_debug
        inv_hit = next((a for a in self.inventory if isinstance(a, cls)), None)
      File "/home/henrypost/Git/LithicArtifacts/main.py", line 355, in <genexpr>
        inv_hit = next((a for a in self.inventory if isinstance(a, cls)), None)
                                                    ~~~~~~~~~~^^^^^^^^
    TypeError: isinstance() arg 2 must be a type, a tuple of types, or a union
    error: recipe `run` failed on line 5 with exit code 1
    


## Artifacts
- Fractal Blaster: piercing shots that trace a constantly-shifting Julia set outline
  - firing it briefly renders a dithered, rendered julia set in the background with the same constants as the current shot (both the outline and background julia set follow the same slowly drifting parameters)
    - the background julia set should fade out smoothly within 3 seconds. re-firing the Fractal Blaster just clamps the fadeout to the top value again.


## Gameplay
- Floors / progression (floor counter, difficulty scaling)

- Enemies sometimes (1/5 chance) drop missile refill canisters (5 missiles for any type of missile that is the least full)
  - canisters blink within 10 seconds (for 3 seconds), then despawn

## Worldgen
- Difficulty scaling: denser spawns + harder enemies deeper down, but better artifacts.

## Visuals/Aesthetic

<!--None yet.-->

- Vampiric Cape trail should slowly disappear if the player is not moving.

## Other
- Make sure assets/ is included in .spec file

## Later
- Set up pyinstaller release for Steam distribution
  - For a working example, see CICD and scripts in ~/Git/LithicRivers.


## Core

Pull RNG-related things out into `rng.py` so we can easily tweak them. Things like worldgen, item spawn chances, etc.

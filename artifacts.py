"""
Artifact base class and all artifact implementations.

Artifacts are passive/active body modifications carried in player.artifacts.
Each frame, Game calls artifact.on_frame(player, world, inputs) for every
equipped artifact. Other hooks fire on specific events.
"""

_TILE = 8   # mirror of TILE in main.py


class Artifact:
    name        = ""
    glyph       = "?"
    description = ""

    def on_frame(self, player, world, inputs):
        """Called once per frame.
        inputs: dict with bool keys left/right/up/down/jump/shoot."""
        pass

    def on_shoot(self, player, bullet):
        """Called when the player fires; may modify bullet in place."""
        pass

    def on_land(self, player):
        """Called when the player touches ground."""
        pass


class SpiralBorer(Artifact):
    """Phase downward through solid floors without destroying them.
    Entering is a commitment — burrowing ends only when you emerge below."""
    name        = "Spiral Borer"
    glyph       = "B"
    description = ("Phase through solid floors without destroying them. "
                   "Commitment — burrowing ends only when you emerge below.")

    def on_frame(self, player, world, inputs):
        if player.burrowing:
            if self._emerged(player, world):
                player.burrowing = False
        elif player.on_ground and inputs["down"] and not player.aim_locked:
            player.burrowing = True
            player.on_ground = False
            player.vy        = 1.0   # seed downward velocity into the floor

    @staticmethod
    def _emerged(player, world):
        """True when the tile row at the player's feet is fully open."""
        br = int(player.bottom // _TILE)
        lc = int(player.x // _TILE)
        rc = int((player.right - 1) // _TILE)
        return not world.solid(lc, br) and not world.solid(rc, br)

"""Top-level API for the bot. Takes care of coordination of all other
objects. Exposes update and get_moves that the top level MyBot.py
interfaces with.
"""

from dexlib.game_state import Move
from dexlib.pathing import PathFinder
from dexlib.move_finder import MoveFinder


class BotAPI:

    def __init__(self, ms):
        self.pf = PathFinder(ms)
        self.mf = MoveFinder(ms)

    def update(self, ms):
        """Trigger all start-of-turn calculations."""
        ms.update()
        self.mf.update(ms)

    def get_moves(self, ms):
        """Find all moves!"""
        moves = []
        for x, y in ms.owned_locs:
            tx, ty = self.mf.get_target(x, y, ms)
            cardinal = self.pf.find_pref_cardinal(x, y, tx, ty, ms)
            moves.append(Move(x, y, cardinal))
        return moves

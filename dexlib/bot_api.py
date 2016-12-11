"""Top-level API for the bot. Takes care of coordination of all other
objects. Exposes update and get_moves that the top level MyBot.py
interfaces with.
"""
from dexlib.game_state import Move
from dexlib.pathing import PathFinder
from dexlib.move_finder import MoveFinder


class BotAPI:

    def __init__(self, ms):
        ms.update()
        self.pf = PathFinder(ms)
        self.mf = MoveFinder(ms)
        print('', file=open('moves.txt', 'w'))

    def update(self, ms):
        """Trigger all start-of-turn calculations."""
        ms.update()
        self.mf.update(ms)
        print("Turn ", ms.turn, " -----", file=open('moves.txt', 'a'))

    def get_moves(self, ms):
        """Find all moves!"""
        moves = []
        for x, y in ms.owned_locs:
            tx, ty = self.mf.get_target(x, y, ms)
            cardinal = self.pf.find_pref_cardinal(x, y, tx, ty, ms)
            if cardinal != 0:
                print(ms.strn[x, y], (x, y), (tx, ty), file=open('moves.txt', 'a'))
            moves.append(Move(x, y, cardinal))
        return moves

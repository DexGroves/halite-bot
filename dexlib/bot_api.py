"""Top-level API for the bot. Takes care of coordination of all other
objects. Exposes update and get_moves that the top level MyBot.py
interfaces with.
"""
from dexlib.pathing import PathFinder
from dexlib.move_finder import MoveFinder
from dexlib.move_resolver import MoveResolver


class BotAPI:

    def __init__(self, ms):
        ms.update()
        self.pf = PathFinder(ms)
        self.mf = MoveFinder(ms)
        print('turn x y tx ty', file=open('moves.txt', 'w'))

    def update(self, ms):
        """Trigger all start-of-turn calculations."""
        ms.update()
        self.mf.update(ms)

    def get_moves(self, ms):
        """Find all moves!"""
        mr = MoveResolver()
        for x, y in ms.owned_locs:
            qmove = self.mf.get_target(x, y, ms)
            mr.add_move(qmove)

        return mr.process_moves(ms, self.pf)

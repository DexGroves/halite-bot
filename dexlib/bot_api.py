"""Top-level API for the bot. Takes care of coordination of all other
objects. Exposes update and get_moves that the top level MyBot.py
interfaces with.
"""
from dexlib.pathing import PathFinder
from dexlib.move_finder import MoveFinder
from dexlib.move_resolver import MoveResolver
from dexlib.border_operator import BorderOperator


class BotAPI:

    def __init__(self, ms, config):
        ms.update()
        self.pf = PathFinder(ms)
        self.mf = MoveFinder(ms, config)
        self.bo = BorderOperator(config)

    def update(self, ms):
        """Trigger all start-of-turn calculations."""
        ms.update()
        self.mf.update(ms)

    def get_moves(self, ms):
        """Find all moves!"""
        mr = MoveResolver()
        self.mf.get_moves(ms, mr)
        self.mf.get_combat_moves(ms, mr)
        return mr.process_moves(ms, self.pf)
        # self.bo.improve_moves(mr, ms, self.mf)

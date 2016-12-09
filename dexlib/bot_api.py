"""Top-level API for the bot. Takes care of coordination of all other
objects. Exposes update and get_moves that the top level MyBot.py
interfaces with.
"""

import numpy as np
from dexlib.game_state import Move


class BotAPI:

    def __init__(self):
        pass

    def update(self, ms):
        ms.update()

    def get_moves(self, ms):
        return [Move(x, y, np.random.choice(range(5)))
                for (x, y) in np.transpose(np.nonzero(ms.owned))]

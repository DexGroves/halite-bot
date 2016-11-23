"""Hold a queue of moves that can be written to in any order."""


import random
import numpy as np
from halitesrc.hlt import Move, Location


class MoveQueue(object):

    def __init__(self, locs):
        self.rem_locs = [(r[0], r[1]) for r in locs]

        self.moves = np.empty(len(locs), dtype=Move)
        self.nmoved = 0

    def pend_move(self, x, y, cardinal):
        self.moves[self.nmoved] = Move(Location(x, y), cardinal)
        self.nmoved += 1

    def process_pending(self, pending):
        if len(pending) == 0:
            return None

        start = self.nmoved
        end = self.nmoved + len(pending)

        insert_moves = [Move(Location(pending.locs[i][0], pending.locs[i][1]),
                             pending.cardinals[i])
                        for i in range(len(pending))]

        with open('debug.txt', 'a') as f:
            f.write(repr(insert_moves) + '\n' +
                    repr(self.moves[start:end]) + '\n' +
                    repr((start, end)) + '\n' +
                    repr(self.moves))

        self.moves[start:end] = insert_moves

        self.rem_locs = [r for r in self.rem_locs if not r in pending.locs]
        self.nmoved = end

    def shuffle_remaining_locs(self):
        random.shuffle(self.rem_locs)

class PendingMoves(object):

    def __init__(self):
        self.locs = []
        self.cardinals = []

    def __len__(self):
        return len(self.locs)

    def pend_move(self, x, y, cardinal):
        """Queue a move."""
        self.locs.append((x, y))
        self.cardinals.append(cardinal)

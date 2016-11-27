"""Hold a queue of moves that can be written to in any order."""


import random
import numpy as np
from halitesrc.hlt import Move, Location


class MoveQueue(object):

    def __init__(self, locs):
        self.rem_locs = [(r[0], r[1]) for r in locs]

        self.moves = np.empty(len(locs), dtype=Move)
        self.nmoved = 0

    def __repr__(self):
        rep = 'MoveQueue:\n'
        for rem in self.rem_locs:
            rep += "StartUnassigned:\t" + repr(rem) + "\n"
        for move in self.moves[0:self.nmoved]:
            rep += "Move:\t" + repr((move.loc.x, move.loc.y)) + "\t" + \
                repr(move.direction) + "\n"

        return rep

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

        self.moves[start:end] = insert_moves

        self.rem_locs = [r for r in self.rem_locs if r not in pending.locs]
        self.nmoved = end

    def shuffle_remaining_locs(self):
        random.shuffle(self.rem_locs)

    def order_locs_by_strength(self, appraiser):
        if len(self.rem_locs) < 2:
            return None

        strs = np.zeros(len(self.rem_locs), dtype=int)
        for i, (x, y) in enumerate(self.rem_locs):
            strs[i] = appraiser.value[x, y]

        sort_value = np.argsort(-1 * strs)
        self.rem_locs = [self.rem_locs[i] for i in sort_value]


class PendingMoves(object):

    def __init__(self):
        self.locs = []
        self.cardinals = []

    def __len__(self):
        return len(self.locs)

    def __repr__(self):
        rep = 'PendingMoves:\n'
        for i in range(len(self.locs)):
            rep += repr(self.locs[i]) + "\t" + repr(self.cardinals[i]) + "\n"
        return rep

    def pend_move(self, x, y, cardinal):
        """Queue a move."""
        self.locs.append((x, y))
        self.cardinals.append(cardinal)

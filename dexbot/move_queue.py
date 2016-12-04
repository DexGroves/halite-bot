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

    def queue_all_still(self):
        self.moves = [Move(Location(x, y), 0) for x, y in self.rem_locs]


class MoveResolver(MoveQueue):

    def __init__(self, locs):
        self.rem_locs = [(r[0], r[1]) for r in locs]
        self.moves = np.empty(len(locs), dtype=Move)

        self.origins = np.empty(len(locs), dtype=tuple)
        self.targets = np.empty(len(locs), dtype=tuple)
        self.nxy1 = np.empty(len(locs), dtype=tuple)
        self.nxy2 = np.empty(len(locs), dtype=tuple)

        self.nmoved = 0
        self.npend = 0
        self.npreproc = 0

        self.iterlim = 500

    def pend_move(self, x, y, tx, ty):
        """Insert a move that you WANT to make. This object decides."""
        self.origins[self.npend] = (x, y)
        self.targets[self.npend] = (tx, ty)
        self.npend += 1

    def process_pending(self, pending, map_state):
        if len(pending) == 0:
            return None

        start = self.npend
        end = self.npend + len(pending)

        self.origins[start:end] = pending.locs
        self.targets[start:end] = [
            map_state.cardinal_to_nxny(pending.locs[i][0], pending.locs[i][1],
                                       pending.cardinals[i])
            for i in range(len(pending))
        ]

        self.rem_locs = [r for r in self.rem_locs if r not in pending.locs]
        self.npend = end

    def resolve_dirs(self, pathfinder, map_state):
        """Resolve the primary and secondary desired cardinals."""
        nxy1 = np.empty(self.npend, dtype=tuple)
        nxy2 = np.empty(self.npend, dtype=tuple)
        for i in range(self.npend):
            x, y = self.origins[i]
            tx, ty = self.targets[i]
            nxy1[i], nxy2[i] = pathfinder.find_pref_next(x, y, tx, ty,
                                                         map_state)

        self.block_to_mover = {(nx, ny): [] for (nx, ny) in np.unique(nxy1)}
        mover_to_secondary = {self.origins[i]: nxy2[i]
                              for i in range(self.npend)}
        skiplist = {self.origins[i]: False for i in range(self.npend)}

        for i in range(self.npend):
            x, y = self.origins[i]
            tx, ty = nxy1[i]
            self.block_to_mover[(tx, ty)].append((x, y))

        # Resolve directions and log moves when done!
        for i in range(self.iterlim):
            resolving = False
            iterkeys = list(self.block_to_mover.keys())  # Freeze these!
            random.shuffle(iterkeys)
            for tx, ty in iterkeys:
                movers = self.block_to_mover[tx, ty]
                strs = [map_state.mine_strn[(c[0], c[1])]
                        for c in movers]
                # should prob make this a config parameter
                if len(strs) == 1 or np.sum(strs) < 240:
                    continue

                # Else have to do some resolving
                second_str = np.where(np.argsort(-1 * np.array(strs)) == 1)[0][0]

                from_x, from_y = movers[second_str]

                if skiplist[from_x, from_y]:
                    continue
                else:
                    resolving = True

                # Kick him to second cardinal if it exists
                sec_x, sec_y = mover_to_secondary[from_x, from_y]
                if sec_x is not None:
                    if (sec_x, sec_y) in self.block_to_mover.keys():
                        self.block_to_mover[sec_x, sec_y].append((from_x, from_y))
                    else:
                        self.block_to_mover[sec_x, sec_y] = [(from_x, from_y)]
                    mover_to_secondary[from_x, from_y] = None, None

                # Else make him stay if he isn't already staying
                elif not (from_x == tx and from_y == ty):
                    if (from_x, from_y) in self.block_to_mover.keys():
                        self.block_to_mover[from_x, from_y].append((from_x, from_y))
                    else:
                        self.block_to_mover[from_x, from_y] = [(from_x, from_y)]

                # Else move.. against the dir of the strongest
                else:
                    strongest = np.argmax(strs)
                    saik_x, saik_y = movers[strongest]
                    dx, dy = saik_x - tx, saik_y - ty
                    snx, sny = from_x + dx, from_y + dy
                    if (snx, sny) in self.block_to_mover.keys():
                        self.block_to_mover[snx, sny].append((from_x, from_y))
                    else:
                        self.block_to_mover[snx, sny] = [(from_x, from_y)]
                    skiplist[from_x, from_y] = True  # We've done all we can

                del self.block_to_mover[tx, ty][second_str]

                break  # Don't want to continue, start again!

            if not resolving:
                break

    def write_moves(self, map_state):
        """Actually make the move objects and get on with it."""
        for (tx, ty), movers in self.block_to_mover.items():
            for mx, my in movers:
                cardinal = map_state.nxny_to_cardinal(mx, my, tx, ty)
                self.moves[self.nmoved] = Move(Location(mx, my), cardinal)
                self.nmoved += 1

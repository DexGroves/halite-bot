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


class MoveResolver(MoveQueue):

    def __init__(self, locs):
        self.rem_locs = [(r[0], r[1]) for r in locs]
        self.moves = np.empty(len(locs), dtype=Move)

        self.origins = np.empty(len(locs), dtype=tuple)
        self.targets = np.empty(len(locs), dtype=tuple)
        self.scores = np.zeros(len(locs), dtype=float)
        self.nxy1 = np.empty(len(locs), dtype=tuple)
        self.nxy2 = np.empty(len(locs), dtype=tuple)

        self.nmoved = 0
        self.npend = 0
        self.npreproc = 0

        self.iterlim = 500

    def pend_move(self, x, y, tx, ty, score):
        """Insert a move that you WANT to make. This object decides."""

        self.origins[self.npend] = (x, y)
        self.targets[self.npend] = (tx, ty)
        self.scores[self.npend] = score
        self.npend += 1

    def process_pending(self, pending, ms):
        if len(pending) == 0:
            return None

        start = self.npend
        end = self.npend + len(pending)

        self.origins[start:end] = pending.locs
        self.targets[start:end] = [
            ms.cardinal_to_nxny(pending.locs[i][0], pending.locs[i][1],
                                pending.cardinals[i])
            for i in range(len(pending))
        ]
        self.scores[start:end] = np.inf

        self.rem_locs = [r for r in self.rem_locs if r not in pending.locs]
        self.npend = end

    def resolve_dirs(self, pf, ms):
        """Resolve the primary and secondary desired cardinals."""
        self.output_moves = []
        self.dodges = []
        self.landscape = np.zeros_like(ms.strn)

        msort = np.argsort(self.scores)
        for i in reversed(msort):
            x, y = self.origins[i]
            tx, ty = self.targets[i]
            if np.isinf(self.scores[i]):
                self.output_moves.append(self.force_move(ms, x, y, tx, ty))
                continue

            tx, ty = self.resolve_move(x, y, tx, ty, ms, pf)
            if tx is None:
                continue  # It hit the dodge queue RIP

            cardinal = self.nxny_to_cardinal(ms, x, y, tx, ty)
            self.output_moves.append((x, y, cardinal))

        for dodge in self.dodges:
            x, y, tx, ty = dodge
            tx, ty = self.resolve_dodge(x, y, tx, ty, ms)
            cardinal = self.nxny_to_cardinal(ms, x, y, tx, ty)
            self.output_moves.append((x, y, cardinal))

    def force_move(self, ms, x, y, tx, ty):
        cardinal = self.nxny_to_cardinal(ms, x, y, tx, ty)
        return (x, y, cardinal)

    def resolve_move(self, x, y, tx, ty, ms, pf):
        strn = ms.strn[x, y]
        (fx, fy), (sx, sy) = pf.find_pref_next(x, y,
                                               tx, ty, ms)
        if (self.landscape[fx, fy] + strn) <= max(strn, 255):
            # Can move safely, so do it
            self.landscape[fx, fy] += strn
            if ms.combat[fx, fy]:
                self.set_combat_patch(ms, x, y, fx, fy)
            return fx, fy

        if sx is not None and \
                (self.landscape[sx, sy] + strn) <= max(strn, 255):
            # Maybe our second cardinal is better
            self.landscape[sx, sy] += strn
            if ms.combat[sx, sy]:
                self.set_combat_patch(ms, x, y, sx, sy)
            return sx, sy

        if (self.landscape[x, y] + strn) <= max(strn, 255):
            # Maybe we can just stay instead
            self.landscape[x, y] += strn

            return x, y

        # Else kick it to the dodge queue
        self.dodges.append((x, y, tx, ty))
        return None, None  # Don't look at me like that...

    def resolve_dodge(self, x, y, tx, ty, ms):
        nbrs = ms.nbrs[(x, y)]
        strn = ms.strn[x, y]
        is_mine = [ms.mine[nx, ny] for (nx, ny) in nbrs]
        is_free = [(self.landscape[nx, ny] + strn) < 255
                   for (nx, ny) in nbrs]

        for i, (nx, ny) in enumerate(nbrs):
            if is_mine[i] and is_free[i]:
                self.landscape[nx, ny] += strn

                # logging.debug(
                #     (ms.turn, (x, y), (nx, ny), 'dodge mine and free')
                # )

                return nx, ny

        is_enemy = [ms.enemy[nx, ny] for (nx, ny) in nbrs]

        for i, (nx, ny) in enumerate(nbrs):
            if is_enemy[i] and is_free[i]:
                self.landscape[nx, ny] += strn

                # logging.debug(
                #     (ms.turn, (x, y), (nx, ny), 'dodge enemy')
                # )

                return nx, ny

        is_blank = np.array([ms.blank[nx, ny] for (nx, ny) in nbrs])
        if is_blank.sum() > 0:
            strn_arr = np.array([ms.strn[nx, ny] + self.landscape[nx, ny]
                                 for (nx, ny) in nbrs])
            strn_arr[np.where(is_blank == 0)] = 999
            min_str = np.argmin(strn_arr)

            nx, ny = nbrs[min_str]
            if (self.landscape[nx, ny] + strn) <= 255:
                self.landscape[nx, ny] += strn

                # logging.debug(
                #     (ms.turn, (x, y), (nx, ny), 'dodge weakest blank')
                # )

                return nx, ny

        nbrs += [(x, y)]
        strn_burn = np.array([strn + self.landscape[nnx, nny]
                              for (nnx, nny) in nbrs])
        min_burn = np.argmin(strn_burn)
        nx, ny = nbrs[min_burn]
        self.landscape[nx, ny] += strn

        # logging.debug(
        #     (ms.turn, (x, y), (nx, ny), 'dodge lowest burn')
        # )

        return nx, ny

    def set_combat_patch(self, ms, x, y, nx, ny):
        for nbrx, nbry in ms.nbrs[nx, ny]:
            self.landscape[nbrx, nbry] += ms.strn[x, y]

    def write_moves(self, ms):
        """Actually make the move objects and get on with it."""
        for move in self.output_moves:
            x, y, cardinal = move
            self.moves[self.nmoved] = Move(Location(x, y), cardinal)
            self.nmoved += 1

    @staticmethod
    def nxny_to_cardinal(ms, x, y, nx, ny):
        dx, dy = (nx - x), (ny - y)

        if (dx, dy) == (0, 0):
            return 0

        if dx == ms.width - 1:
            dx = -1
        if dx == -1 * (ms.width - 1):
            dx = 1
        if dy == ms.height - 1:
            dy = -1
        if dy == -1 * (ms.height - 1):
            dy = 1

        if (dx, dy) == (0, -1):
            return 1
        elif (dx, dy) == (1, 0):
            return 2
        elif (dx, dy) == (0, 1):
            return 3
        elif (dx, dy) == (-1, 0):
            return 4
        else:
            print(repr((x, y)) + '\t' + repr((nx, ny)) + '\t' + repr((dx, dy)) +
                  repr((ms.width, ms.height)))
            raise CardinalityError


class CardinalityError(ValueError):
    """What did you do?!"""
    pass

# nxy1 = np.empty(self.npend, dtype=tuple)
# nxy2 = np.empty(self.npend, dtype=tuple)
# for i in range(self.npend):
#     x, y = self.origins[i]
#     tx, ty = self.targets[i]
#     nxy1[i], nxy2[i] = pf.find_pref_next(x, y, tx, ty,
#                                                  ms)

# self.block_to_mover = {(nx, ny): [] for (nx, ny) in np.unique(nxy1)}
# mover_to_secondary = {self.origins[i]: nxy2[i]
#                       for i in range(self.npend)}
# skiplist = {self.origins[i]: False for i in range(self.npend)}

# for i in range(self.npend):
#     x, y = self.origins[i]
#     tx, ty = nxy1[i]
#     self.block_to_mover[(tx, ty)].append((x, y))

# # Resolve directions and log moves when done!
# for i in range(self.iterlim):
#     resolving = False
#     iterkeys = list(self.block_to_mover.keys())  # Freeze these!
#     random.shuffle(iterkeys)
#     for tx, ty in iterkeys:
#         movers = self.block_to_mover[tx, ty]
#         strs = [ms.mine_strn[(c[0], c[1])]
#                 for c in movers]
#         # should prob make this a config parameter
#         if len(strs) == 1 or np.sum(strs) < 240:
#             continue

#         # Else have to do some resolving
#         second_str = np.where(np.argsort(-1 * np.array(strs)) == 1)[0][0]

#         from_x, from_y = movers[second_str]

#         if skiplist[from_x, from_y]:
#             continue
#         else:
#             resolving = True

#         # Kick him to second cardinal if it exists
#         sec_x, sec_y = mover_to_secondary[from_x, from_y]
#         if sec_x is not None:
#             if (sec_x, sec_y) in self.block_to_mover.keys():
#                 self.block_to_mover[sec_x, sec_y].append((from_x, from_y))
#             else:
#                 self.block_to_mover[sec_x, sec_y] = [(from_x, from_y)]
#             mover_to_secondary[from_x, from_y] = None, None

#         # Else make him stay if he isn't already staying
#         elif not (from_x == tx and from_y == ty):
#             if (from_x, from_y) in self.block_to_mover.keys():
#                 self.block_to_mover[from_x, from_y].append((from_x, from_y))
#             else:
#                 self.block_to_mover[from_x, from_y] = [(from_x, from_y)]

#         # Else move.. against the dir of the strongest
#         else:
#             strongest = np.argmax(strs)
#             saik_x, saik_y = movers[strongest]
#             dx, dy = saik_x - tx, saik_y - ty
#             snx, sny = from_x + dx, from_y + dy
#             if (snx, sny) in self.block_to_mover.keys():
#                 self.block_to_mover[snx, sny].append((from_x, from_y))
#             else:
#                 self.block_to_mover[snx, sny] = [(from_x, from_y)]
#             skiplist[from_x, from_y] = True  # We've done all we can

#         del self.block_to_mover[tx, ty][second_str]

#         break  # Don't want to continue, start again!

#     if not resolving:
#         break

# def write_moves(self, ms):
#     """Actually make the move objects and get on with it."""
#     for (tx, ty), movers in self.block_to_mover.items():
#         for mx, my in movers:
#             cardinal = ms.nxny_to_cardinal(mx, my, tx, ty)
#             self.moves[self.nmoved] = Move(Location(mx, my), cardinal)
#             self.nmoved += 1

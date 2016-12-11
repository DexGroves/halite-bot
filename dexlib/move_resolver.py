import operator
import numpy as np
from dexlib.game_state import Move


class MoveResolver:
    """Stop people from bumping into each other while moving.
    Avoid the cap, have a good formation, etc etc.
    """

    def __init__(self):
        self.moves = {}
        self.dodges = []

    def add_move(self, qmove):
        if qmove.priority in self.moves.keys():
            self.moves[qmove.priority].append(qmove)
        else:
            self.moves[qmove.priority] = [qmove]

    def process_moves(self, ms, pf):
        output_moves = []
        self.landscape = np.zeros_like(ms.strn)

        priorities = sorted(self.moves.keys())
        for priority in priorities:
            self.moves[priority].sort(key=operator.attrgetter('score'))

            for move in self.moves[priority]:
                tx, ty = self.resolve_move(move, ms, pf)
                if tx is None:
                    continue

                cardinal = self.nxny_to_cardinal(ms, move.x, move.y, tx, ty)
                output_moves.append(Move(move.x, move.y, cardinal))

        for move in self.dodges:
            tx, ty = self.resolve_dodge(move, ms)
            cardinal = self.nxny_to_cardinal(ms, move.x, move.y, tx, ty)
            output_moves.append(Move(move.x, move.y, cardinal))

        return output_moves

    def resolve_move(self, move, ms, pf):
        strn = ms.strn[move.x, move.y]
        (fx, fy), (sx, sy) = pf.find_pref_next(move.x, move.y,
                                               move.tx, move.ty, ms)
        if (self.landscape[fx, fy] + strn) <= max(strn, 255):
            # Can move safely, so do it
            self.landscape[fx, fy] += strn
            return fx, fy

        if sx is not None and \
                (self.landscape[sx, sy] + strn) <= max(strn, 255):
            # Maybe our second cardinal is better
            self.landscape[sx, sy] += strn
            return sx, sy

        if (self.landscape[move.x, move.y] + strn) <= max(strn, 255):
            # Maybe we can just stay instead
            self.landscape[move.x, move.y] += strn
            return move.x, move.y

        # Else kick it to the dodge queue
        self.dodges.append(move)
        return None, None  # Don't look at me like that...

    def resolve_dodge(self, move, ms):
        nbrs = ms.nbrs[(move.x, move.y)]
        strn = ms.strn[move.x, move.y]
        is_mine = [ms.owned[nx, ny] for (nx, ny) in nbrs]
        is_free = [(self.landscape[nx, ny] + strn) < 255
                   for (nx, ny) in nbrs]

        for i, (nx, ny) in enumerate(nbrs):
            if is_mine[i] and is_free[i]:
                self.landscape[nx, ny] += strn
                return nx, ny

        is_enemy = [ms.owned[nx, ny] for (nx, ny) in nbrs]

        for i, (nx, ny) in enumerate(nbrs):
            if is_enemy[i]:
                self.landscape[nx, ny] += strn
                return nx, ny

        nx, ny = np.random.choice(nbrs)
        self.landscape[nx, ny] += strn
        return nx, ny

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

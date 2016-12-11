import operator
import numpy as np
from dexlib.game_state import Move
# import logging
# logging.basicConfig(filename='bo.info', filemode="w", level=logging.DEBUG)


class MoveResolver:
    """Stop people from bumping into each other while moving.
    Avoid the cap, have a good formation, etc etc.
    """

    def __init__(self):
        self.moves = {}
        self.map_ = {}
        self.dodges = []

    def add_move(self, qmove):
        if qmove.priority in self.moves.keys():
            self.moves[qmove.priority].append(qmove)
        else:
            self.moves[qmove.priority] = [qmove]
        self.map_[(qmove.x, qmove.y)] = qmove.priority, len(self.moves[qmove.priority]) - 1

    def process_moves(self, ms, pf):
        output_moves = []
        self.landscape = np.zeros_like(ms.strn)

        priorities = sorted(self.moves.keys())
        for priority in priorities:
            self.moves[priority].sort(key=operator.attrgetter('score'))

            for move in self.moves[priority]:
                if move.x is None:
                    continue

                if priority == -2:
                    output_moves.append(self.force_move(ms, move))
                    continue

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

    def force_move(self, ms, move):
        cardinal = self.nxny_to_cardinal(ms, move.x, move.y, move.tx, move.ty)
        return Move(move.x, move.y, cardinal)

    def resolve_move(self, move, ms, pf):
        strn = ms.strn[move.x, move.y]
        (fx, fy), (sx, sy) = pf.find_pref_next(move.x, move.y,
                                               move.tx, move.ty, ms)
        if (self.landscape[fx, fy] + strn) <= max(strn, 255):
            # Can move safely, so do it
            self.landscape[fx, fy] += strn
            if ms.combat[fx, fy]:
                self.set_combat_patch(ms, move.x, move.y, fx, fy)

            # logging.debug(
            #     (ms.turn, (move.x, move.y), (fx, fy), 'first card')
            # )

            return fx, fy

        if sx is not None and \
                (self.landscape[sx, sy] + strn) <= max(strn, 255):
            # Maybe our second cardinal is better
            self.landscape[sx, sy] += strn
            if ms.combat[sx, sy]:
                self.set_combat_patch(ms, move.x, move.y, sx, sy)

            # logging.debug(
            #     (ms.turn, (move.x, move.y), (sx, sy), 'second card')
            # )

            return sx, sy

        if (self.landscape[move.x, move.y] + strn) <= max(strn, 255):
            # Maybe we can just stay instead
            self.landscape[move.x, move.y] += strn

            # logging.debug(
            #     (ms.turn, (move.x, move.y), (move.x, move.y), 'force stay')
            # )

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

                # logging.debug(
                #     (ms.turn, (move.x, move.y), (nx, ny), 'dodge mine and free')
                # )

                return nx, ny

        is_enemy = [ms.enemy[nx, ny] for (nx, ny) in nbrs]

        for i, (nx, ny) in enumerate(nbrs):
            if is_enemy[i] and is_free[i]:
                self.landscape[nx, ny] += strn

                # logging.debug(
                #     (ms.turn, (move.x, move.y), (nx, ny), 'dodge enemy')
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
                #     (ms.turn, (move.x, move.y), (nx, ny), 'dodge weakest blank')
                # )

                return nx, ny

        nbrs += [(move.x, move.y)]
        strn_burn = np.array([strn + self.landscape[nx, ny] for (nx, ny) in nbrs])
        min_burn = np.argmin(strn_burn)
        nx, ny = nbrs[min_burn]
        self.landscape[nx, ny] += strn

        # logging.debug(
        #     (ms.turn, (move.x, move.y), (nx, ny), 'dodge lowest burn')
        # )

        return nx, ny

    def set_combat_patch(self, ms, x, y, nx, ny):
        for nbrx, nbry in ms.nbrs[nx, ny]:
            self.landscape[nbrx, nbry] += ms.strn[x, y]

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

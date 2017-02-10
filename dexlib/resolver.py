import numpy as np
from dexlib.find_path import find_pref_next


import logging
logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class Resolver:
    """Handle str cap avoiding, patch mechanics, etc."""

    def __init__(self, gm):
        pass

    def resolve(self, gm, moveset):
        # I don't do anything about over-growing the cap, but can I even.
        self.set_implicit_stays(gm, moveset)
        pstrn_map = np.zeros_like(gm.strn)

        on_moves = {(ax, ay): v for (ax, ay), v in moveset.move_dict.items()
                    if (ax + ay + gm.turn) % 2 == gm.parity}
        off_moves = {(ax, ay): v for (ax, ay), v in moveset.move_dict.items()
                     if (ax + ay + gm.turn) % 2 != gm.parity}

        if gm.turn < 40:  # TEst hacks
            on_moves = moveset.move_dict
            off_moves = {}

        # Handle all the black squares going where they need to be
        on_origins = list(on_moves.keys())
        on_targets = list(on_moves.values())
        on_strns = [gm.strn[x, y] for (x, y) in on_origins]
        str_sort = np.argsort(on_strns)

        for i in str_sort[::-1]:
            ax, ay = on_origins[i]
            tx, ty, _ = on_targets[i]
            istrn = on_strns[i]

            if gm.close_to_combat[ax, ay] and not (ax == tx and ay == ty):
                d2c = gm.dist_from_combat[ax, ay]
                choices = []
                for i, (nx, ny) in enumerate(gm.nbrs[ax, ay]):
                    if gm.dist_from_combat[nx, ny] < d2c and not gm.wall[nx, ny]:
                        choices.append((nx, ny, i + 1))

                if len(choices) == 2:
                    (px1, py1, d1), (px2, py2, d2) = choices[0], choices[1]
                elif len(choices):
                    (px1, py1, d1), (px2, py2, d2) = choices[0], (None, None, None)
                else:
                    (px1, py1, d1), (px2, py2, d2) = (ax, ay, 0), (None, None, None)

                # logging.debug(((ax, ay), choices))
            else:
                (px1, py1, d1), (px2, py2, d2) = find_pref_next(ax, ay, tx, ty, gm)

            if (istrn + pstrn_map[px1, py1]) <= 255:  # and \
                    #  ((gm.strn[px1, py1] + gm.prod[px1, py1]) < istrn or
                    #    gm.owned[px1, py1] == 0):
                moveset.add_move(ax, ay, ax, ay, d1)
                pstrn_map[px1, py1] += istrn
                # logging.debug(((ax, ay), 'to', (d1), 'firstpick'))
            elif px2 is not None and (istrn + pstrn_map[px2, py2]) <= 255:  # and \
                    #  ((gm.strn[px2, py2] + gm.prod[px2, py2]) < istrn or
                    #    gm.owned[px2, py2] == 0):
                moveset.add_move(ax, ay, ax, ay, d2)
                pstrn_map[px2, py2] += istrn
                # logging.debug(((ax, ay), 'to', (d2), 'secpick'))
            elif gm.melee_mat[ax, ay]:
                nbrs = gm.nbrs[(ax, ay)]
                scores = np.array([
                    gm.combat_heur[nx, ny] * ((pstrn_map[nx, ny] + istrn) < 255)
                    for (nx, ny) in nbrs
                ])

                if scores.max() > 0:
                    nx, ny = nbrs[scores.argmax()]
                    dir_ = self.nxny_to_cardinal(gm, ax, ay, nx, ny)
                    moveset.add_move(ax, ay, ax, ay, dir_)
                    pstrn_map[nx, ny] += istrn + gm.prod[ax, ay]
                else:
                    moveset.add_move(ax, ay, ax, ay, 0)
                    pstrn_map[ax, ay] += istrn + gm.prod[ax, ay]

            else:
                # moveset.add_move(ax, ay, ax, ay, 0)
                # pstrn_map[ax, ay] += istrn + gm.prod[ax, ay]
                off_moves[ax, ay] = tx, ty
                # logging.debug(((ax, ay), 'to', (0), 'dodgeroo'))

        # Handle all the white squares getting the heck out of the way
        # Not iterating in any particular order!
        for (ax, ay) in off_moves.keys():
            istrn = gm.strn[ax, ay]
            iprod = gm.prod[ax, ay]
            if pstrn_map[ax, ay] == 0:
                moveset.add_move(ax, ay, ax, ay, 0)
                pstrn_map[ax, ay] += istrn + iprod

            elif (pstrn_map[ax, ay] + istrn + iprod) <= 255:
                moveset.add_move(ax, ay, ax, ay, 0)
                pstrn_map[ax, ay] += istrn + iprod

            else:  # Dodge this!
                # Check if it's better to just hang out
                addable = 255 - pstrn_map[ax, ay] - istrn
                if addable > istrn:
                    moveset.add_move(ax, ay, ax, ay, 0)
                    pstrn_map[ax, ay] += istrn + iprod
                    continue

                nbrs = gm.nbrs[ax, ay]

                # Find somewhere to fit!
                # can_fit = np.array([
                #     gm.owned[nx, ny] and (pstrn_map[nx, ny] + istrn) <= 255
                #     for (nx, ny) in nbrs
                # ])

                # Find an enemy to hit!
                # Can technically lose to cap here since I skip checking pstrn
                enemy_strn = np.array([
                    gm.enemy[nnx, nny] * gm.strn[nnx, nny]
                    for (nnx, nny) in nbrs
                ])
                if enemy_strn.max() > 1:
                    dir_ = enemy_strn.argmax() + 1
                    moveset.add_move(ax, ay, ax, ay, dir_)
                    nx, ny = nbrs[enemy_strn.argmax()]
                    pstrn_map[nx, ny] += istrn
                    continue

                # Find a blank square to damage!
                blank_strn = np.array([
                    gm.blank[nnx, nny] * gm.strnc[nnx, nny] * (gm.strnc[nnx, nny] < istrn)
                    for (nnx, nny) in nbrs
                ])

                if blank_strn.max() > 0.5:
                    dir_ = blank_strn.argmax() + 1
                    moveset.add_move(ax, ay, ax, ay, dir_)
                    nx, ny = nbrs[blank_strn.argmax()]
                    pstrn_map[nx, ny] += istrn
                    continue

                # Go to the weakest remaining square
                owned_strn = np.array([
                    # gm.owned[nx, ny] * gm.strn[nx, ny]
                    gm.owned[nnx, nny] * (pstrn_map[nnx, nny] + gm.strn[nnx, nny])
                    for (nnx, nny) in nbrs
                ])
                owned_strn[owned_strn == 0] = 999

                dir_ = owned_strn.argmin() + 1
                moveset.add_move(ax, ay, ax, ay, dir_)
                nx, ny = nbrs[owned_strn.argmin()]
                pstrn_map[nx, ny] += istrn
                continue

        return moveset

    def set_implicit_stays(self, gm, moveset):
        implicit_stays = set((x, y) for x, y in gm.owned_locs) - \
            moveset.move_dict.keys()
        for ix, iy in implicit_stays:
            moveset.add_move(ix, iy, ix, iy)

    @staticmethod
    def nxny_to_cardinal(gm, x, y, nx, ny):
        dx, dy = (nx - x), (ny - y)
        if dx == gm.width - 1:
            dx = -1
        if dx == -1 * (gm.width - 1):
            dx = 1
        if dy == gm.height - 1:
            dy = -1
        if dy == -1 * (gm.height - 1):
            dy = 1

        if (dx, dy) == (0, 0):
            return 0
        elif (dx, dy) == (0, -1):
            return 1
        elif (dx, dy) == (1, 0):
            return 2
        elif (dx, dy) == (0, 1):
            return 3
        elif (dx, dy) == (-1, 0):
            return 4
        else:
            return 0

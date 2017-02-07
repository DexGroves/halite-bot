import numpy as np


class Moveset:
    """A mutable move manager!"""

    def __init__(self, gm):
        self.to_move = set(gm.owned_locs)
        self.move_dict = {}
        self.move_matrix = np.zeros_like(gm.owned, dtype=bool)

    def add_move(self, ax, ay, tx, ty, dir_=None):
        """Register a move."""
        self.move_dict[(ax, ay)] = tx, ty, dir_
        self.move_matrix[ax, ay] = True
        if (ax, ay) in self.to_move:
            to_move.remove((ax, ay))

    def iter_remaining(self):
        """Iterate over all remaining moves."""
        for ax, ay in self.to_move:
            yield ax, ay


class Combatant:
    """Handle all the moves for combat zones."""

    def __init__(self, combat_wait):
        self.combat_wait = combat_wait

    def decide_combat_moves(self, gm, moveset):
        self.decide_melee_moves(gm, moveset)
        self.decide_close_moves(gm, moveset)
        return moveset

    def decide_melee_moves(self, gm):
        locs = np.transpose(np.nonzero(gm.melee_mat))
        strns = [gm.strn[x, y] for (x, y) in locs]

        for ci in np.argsort(strns)[::-1]:
            cx, cy = locs[ci]
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            nbrs = gm.nbrs[(cx, cy)]
            scores = [gm.combat_heur[nx, ny] for (nx, ny) in nbrs]

            nx, ny = nbrs[np.argmax(scores)]
            gm.combat_heur[nx, ny] /= 10000

            moveset.add_move(cx, cy, nx, ny)

    def decide_close_moves(self, gm):
        locs = np.transpose(np.nonzero(gm.close_to_combat))
        for cx, cy in locs:
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            dmat = np.divide(gm.melee_mat, gm.dists[cx, cy])
            tx, ty = np.unravel_index(dmat.argmax(), dmat.shape)

            if gm.dists[cx, cy, tx, ty] < 4 and \
                    gm.strnc[cx, cy] < (gm.prodc[cx, cy] * (self.combat_wait + 1.5)):
                moveset.add_move(cx, cy, cx, cy)

            else:
                moveset.add_move(cx, cy, tx, ty)

    def dump_moves(self, gm):
        return self.moves


class MoveMaker:
    """Evaluate the value of border squares and coordinate moves.
    Values are taken for each x, y, s, where s is the degree to which
    to hunt for teamups.
    """
    def __init__(self, gm, wait, glob_k):
        self.glob_k = glob_k
        self.bulk_mvmt_off = 10
        self.wait = wait

    def decide_noncombat_moves(self, gm, moveset):
        working_strn = gm.strn.copy()

        motile = ((gm.strnc >= gm.prodc * self.wait) * gm.owned).astype(bool)
        motile[np.nonzero(gm.gte_nbr)] = True
        motile[np.nonzero(moveset.move_matrix)] = False
        strn_avail = gm.ostrn * motile

        Vloc, Vmid, Vglob = self.get_cell_value(gm)
        Vmid *= gm.safe_to_take
        Vglob *= gm.safe_to_take

        Vtot = Vloc + Vmid + Vglob

        self.desired_d1_moves = {}
        d1_conquered = np.ones_like(Vtot, dtype=bool)
        fully_alloc = np.zeros_like(Vtot, dtype=bool)

        to_move_locs = np.transpose(np.nonzero(motile))
        to_move_strn = [gm.strn[x, y] for (x, y) in to_move_locs]
        for ai in np.argsort(to_move_strn)[::-1]:
            ax, ay = to_move_locs[ai]
            t2c = np.maximum(0, (working_strn - gm.strn[ax, ay]) / gm.prodc)

            prox_value = np.divide(Vmid, (gm.dists[ax, ay] + t2c)) * d1_conquered + \
                np.divide(Vglob, (gm.dists[ax, ay] + self.bulk_mvmt_off))
            tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)

            moveset.add_move(ax, ay, tx, ty)

            # Add to a postprocessing queue for later
            if gm.dists[ax, ay, tx, ty] == 1:
                self.desired_d1_moves.setdefault((tx, ty), []).append((ax, ay))
                if gm.strn[ax, ay] > gm.strn[tx, ty]:
                    # No one else can erroneously target this cell
                    d1_conquered[tx, ty] = 0

        self.process_d1_teamups(gm)
        return moveset

    def get_cell_value(self, gm):
        # local_value = gm.prodc * gm.ubrdr
        # Should set this to ignore my strn and prod
        mid_value = gaussian_filter(
            (gm.prodc ** 2 / gm.original_strn), 1.2, mode='wrap'
        ) * gm.ubrdr
        local_value = np.maximum(mid_value, (gm.prodc ** 2 / gm.strnc)) * gm.ubrdr
        global_value = gm.Mbval

        return local_value, mid_value, global_value * self.glob_k

    def process_d1_teamups(self, gm):
        """This is megagrizzle hacks. If two pieces want to occupy
        the same cell 1-distance away, that is too strong for either
        of them, set the gm.strn variable to 0 so that the
        pathfinder is tricked into allowing the moves.
        """
        for (tx, ty), locs in self.desired_d1_moves.items():
            if len(locs) < 2:
                continue
            else:
                total_strn = np.array([
                    gm.strn[ax, ay] for ax, ay in locs
                ])
                if total_strn.sum() > gm.strn[tx, ty] and \
                        total_strn.max() <= gm.strn[tx, ty]:
                    gm.strn[tx, ty] = 0


class Resolver:
    """Handle str cap avoiding, patch mechanics, etc."""

    def __init__(self, gm):
        pass

    def resolve(self, gm, moveset):
        # I don't do anything about over-growing the cap, but can I even.
        self.set_implicit_stays(gm, moveset)
        pstrn_map = np.zeros_like(gm.strn)

        on_moves = {(ax, ay): v for (ax, ay), v in moveset.move_dict.items()
                    if (ax + ay + gm.turn) % 2 == gm.parity}  # or
                    # (gm.melee_mat[ax, ay] + gm.close_to_combat[ax, ay] == 0)}
        off_moves = {(ax, ay): v for (ax, ay), v in moveset.move_dict.items()
                     if (ax + ay + gm.turn) % 2 != gm.parity} #  and
                     #  (gm.melee_mat[ax, ay] + gm.close_to_combat[ax, ay] != 0)}

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
            tx, ty = on_targets[i]
            istrn = on_strns[i]

            (px1, py1, d1), (px2, py2, d2) = find_pref_next(ax, ay, tx, ty, gm)
            if (istrn + pstrn_map[px1, py1]) <= 255: #  and \
                    #  ((gm.strn[px1, py1] + gm.prod[px1, py1]) < istrn or
                    #    gm.owned[px1, py1] == 0):
                moveset.add_move(ax, ay, ax, ay, d1)
                pstrn_map[px1, py1] += istrn
                # logging.debug(((ax, ay), 'to', (d1), 'firstpick'))
            elif px2 is not None and (istrn + pstrn_map[px2, py2]) <= 255: #  and \
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
                can_fit = np.array([
                    gm.owned[nx, ny] and (pstrn_map[nx, ny] + istrn) <= 255
                    for (nx, ny) in nbrs
                ])

                # if can_fit.max() > 0:
                #     dir_ = can_fit.argmax() + 1
                #     moveset.add_move(ax, ay, ax, ay, dir_)
                #     nx, ny = nbrs[can_fit.argmax()]
                #     pstrn_map[nx, ny] += istrn
                #     continue
                # if can_fit.max() > 0:
                #     dir_ = random.choice(np.nonzero(can_fit)) + 1
                #     moveset.add_move(ax, ay, ax, ay, dir_)
                #     nx, ny = nbrs[can_fit.argmax()]
                #     pstrn_map[nx, ny] += istrn

                # Find an enemy to hit!
                # Can technically lose to cap here since I skip checking pstrn
                enemy_strn = np.array([
                    gm.enemy[nx, ny] * gm.strn[nx, ny]
                    for (nx, ny) in nbrs
                ])
                if enemy_strn.max() > 1:
                    dir_ = enemy_strn.argmax() + 1
                    moveset.add_move(ax, ay, ax, ay, dir_)
                    nx, ny = nbrs[enemy_strn.argmax()]
                    pstrn_map[nx, ny] += istrn
                    continue

                # Find a blank square to damage!
                blank_strn = np.array([
                    gm.blank[nx, ny] * gm.strnc[nx, ny] * (gm.strnc[nx, ny] < istrn)
                    for (nx, ny) in nbrs
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
                    gm.owned[nx, ny] * (pstrn_map[nx, ny]+gm.strn[nx, ny])
                    for (nx, ny) in nbrs
                ])
                owned_strn[owned_strn == 0] = 999

                dir_ = owned_strn.argmin() + 1
                moveset.add_move(ax, ay, ax, ay, dir_)
                nx, ny = nbrs[owned_strn.argmin()]
                pstrn_map[nx, ny] += istrn
                continue

        return output

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

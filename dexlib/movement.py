import random
import logging
import numpy as np
import dexlib.nphlt as hlt
from scipy.ndimage.filters import gaussian_filter


logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class Moveset:
    """A mutable move manager!"""

    def __init__(self, gm):
        self.to_move = set(((x, y) for (x, y) in gm.owned_locs))
        self.move_dict = {}
        self.move_matrix = np.zeros_like(gm.owned, dtype=bool)

    def add_move(self, ax, ay, tx, ty, dir_=None):
        """Register a move."""
        self.move_dict[(ax, ay)] = tx, ty, dir_
        self.move_matrix[ax, ay] = True
        if (ax, ay) in self.to_move:
            self.to_move.remove((ax, ay))

    def process_moves(self):
        """Convert everything to what the hlt.py expects."""
        return [hlt.Move(ax, ay, dir_)
                for (ax, ay), (_, _, dir_) in self.move_dict.items()]


class Combatant:

    def __init__(self, combat_wait):
        self.combat_wait = combat_wait

    def decide_combat_moves(self, gm, moveset):
        self.update_projection(gm)
        self.decide_melee_moves(gm, moveset)
        self.decide_close_moves(gm, moveset)
        return moveset

    def update_projection(self, gm):
        """Move enemy pieces TOTALLY AT RANDOM."""
        enemy_strn = gm.enemy * gm.strn
        self.enemy_proj = np.zeros_like(enemy_strn)

        enemy_locs = [(x, y) for (x, y) in np.transpose(np.nonzero(enemy_strn))]
        random.shuffle(enemy_locs)

        for ex, ey in enemy_locs:
            nbrs = [(nx, ny) for (nx, ny) in gm.nbrs[(ex, ey)]
                    if gm.target_cells[nx, ny]]
            if not len(nbrs):
                nbrs.append((ex, ey))
            nx, ny = random.choice(nbrs)
            self.enemy_proj[nx, ny] += enemy_strn[ex, ey]

        self.damage = gm.plus_filter(self.enemy_proj, sum)

    def decide_melee_moves(self, gm, moveset):
        locs = np.transpose(np.nonzero(gm.melee_mat))
        strns = [gm.strn[x, y] for (x, y) in locs]

        for ci in np.argsort(strns)[::-1]:
            strn = strns[ci]
            ax, ay = locs[ci]
            nbrs = gm.nbrs[ax, ay]

            dmg_output = np.zeros(5)
            dmg_recvd = np.zeros(5)
            dmg_recvd[0] = min(strn, self.damage[ax, ay])
            for i, (nx, ny) in enumerate(nbrs):
                dmg_recvd[i + 1] = min(strn, self.damage[nx, ny])
                dmg_output[0] += min(strn, self.enemy_proj[nx, ny])
                dmg_output[i + 1] = np.sum([
                    min(strn, self.enemy_proj[nnx, nny])
                    for nnx, nny in gm.nbrs[nx, ny]
                ]) + gm.deny_prod[nx, ny] + self.enemy_proj[nx, ny]
                if gm.blank[nx, ny] and gm.strn[nx, ny] > 0:
                    dmg_recvd[i + 1] += 9999  # Lol hacks. FF7 in this.

            combat_scores = (dmg_output * 1.2) - dmg_recvd
            target = np.argmax(combat_scores)
            if target == 0:
                tx, ty = ax, ay
            else:
                tx, ty = nbrs[target - 1]

            # logging.debug(((ax, ay), list(dmg_output), list(dmg_recvd), [gm.deny_prod[nx, ny] for (nx, ny) in nbrs]))
            # NB: I should only update representation if patchworked
            for nnx, nny in gm.nbrs[tx, ty]:
                self.enemy_proj[nnx, nny] = \
                    max(0, self.enemy_proj[nnx, nny] - strn)

            moveset.add_move(ax, ay, tx, ty)

    def decide_close_moves(self, gm, moveset):
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

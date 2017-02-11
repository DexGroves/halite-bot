import random
import numpy as np
import dexlib.nphlt as hlt
from scipy.ndimage.filters import gaussian_filter

# import logging
# logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class Moveset:
    """A mutable move manager!"""

    def __init__(self, gm):
        self.to_move = set(((x, y) for (x, y) in gm.owned_locs))
        self.move_dict = {}
        self.move_matrix = np.zeros_like(gm.owned, dtype=bool)
        self.moved_into = np.zeros_like(gm.owned, dtype=bool)

    def add_move(self, ax, ay, tx, ty, dir_=None):
        """Register a move."""
        self.move_dict[(ax, ay)] = tx, ty, dir_
        self.move_matrix[ax, ay] = True
        if (ax, ay) in self.to_move:
            self.to_move.remove((ax, ay))

    def iter_remaining(self):
        """Iterate over all remaining moves."""
        for ax, ay in self.to_move:
            yield ax, ay

    def iter_all(self):
        """Iterate over all remaining moves."""
        for ax, ay in self.move_dict.keys():
            yield ax, ay

    def process_moves(self):
        """Convert everything to what the hlt.py expects."""
        return [hlt.Move(ax, ay, dir_)
                for (ax, ay), (_, _, dir_) in self.move_dict.items()]


class Combatant:
    """Handle all the moves for combat zones."""

    def __init__(self, combat_wait):
        self.combat_wait = combat_wait

    def decide_combat_moves(self, gm, moveset):
        self.decide_melee_moves(gm, moveset)
        self.decide_close_moves(gm, moveset)
        return moveset

    def decide_melee_moves(self, gm, moveset):
        locs = np.transpose(np.nonzero(gm.melee_mat))
        strns = [gm.strn[x, y] for (x, y) in locs]

        for ci in np.argsort(strns)[::-1]:
            cx, cy = locs[ci]
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            nbrs = gm.nbrs[(cx, cy)]
            scores = [gm.combat_heur[nx, ny] - (gm.wall[nx, ny] * 100000)
                      for (nx, ny) in nbrs]

            nx, ny = nbrs[np.argmax(scores)]
            gm.combat_heur[nx, ny] /= 10000

            # logging.debug(('combat', (cx, cy), 'to', (nx, ny)))
            moveset.add_move(cx, cy, nx, ny)

    def decide_close_moves(self, gm, moveset):
        locs = np.transpose(np.nonzero(gm.close_to_combat))
        for cx, cy in locs:
            # d2c = gm.dist_from_combat[cx, cy]
            # nbrs = [n for n in gm.nbrs[cx, cy] if
            #         gm.dist_from_combat[n[0], n[1]] < d2c]
            # tx, ty = random.choice(nbrs)
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            if gm.dist_from_combat[cx, cy] > 6:
                continue

            dmat = np.divide(gm.melee_mat, gm.dists[cx, cy])
            tx, ty = np.unravel_index(dmat.argmax(), dmat.shape)

            if gm.dists[cx, cy, tx, ty] < 4 and \
                    gm.strnc[cx, cy] < (gm.prodc[cx, cy] * (self.combat_wait + 1.5)):
                moveset.add_move(cx, cy, cx, cy)
                # logging.debug(('closewait', (cx, cy), 'stay'))
            else:
                moveset.add_move(cx, cy, tx, ty)
                # logging.debug(('closemove', (cx, cy), 'to', (tx, ty)))


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

        Vloc, Vmid, Vglob = self.get_cell_value(gm)
        Vmid *= gm.safe_to_take
        Vglob *= gm.safe_to_take

        Vtot = Vloc + Vmid + Vglob

        self.desired_d1_moves = {}
        d1_conquered = np.ones_like(Vtot, dtype=bool)

        to_move_locs = np.transpose(np.nonzero(motile))
        to_move_strn = [gm.strn[x, y] for (x, y) in to_move_locs]
        for ai in np.argsort(to_move_strn)[::-1]:
            ax, ay = to_move_locs[ai]
            t2c = np.maximum(0, (working_strn - gm.strn[ax, ay]) / gm.prodc)

            prox_value = np.divide(Vmid, (gm.dists[ax, ay] + t2c)) * d1_conquered + \
                np.divide(Vglob, (gm.dists[ax, ay] + self.bulk_mvmt_off))
            tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)

            if gm.total_strn < gm.strn[tx, ty]:
                moveset.add_move(ax, ay, ax, ay)
            else:
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


class Amalgamator:
    """Union pieces together if it makes sense to do so."""
    def __init__(self, strlim=80, mvlim=2):
        self.strlim = strlim
        self.mvinto_strlim = 80
        self.mvlim = mvlim

    def process_moves(self, gm, moveset):
        for (ax, ay), (tx, ty, _) in moveset.move_dict.items():
            if ax == tx and ay == tx:
                continue
            if gm.strn[ax, ay] >= self.strlim:
                continue
            d2t = gm.dists[ax, ay, tx, ty]
            for nx, ny in gm.oneaways[ax, ay]:
                if gm.owned[nx, ny] and gm.strn[nx, ny] < self.strlim:
                    try:
                        ntx, nty, _ = moveset.move_dict[nx, ny]
                    except:
                        continue
                    dist_targs = gm.dists[ntx, nty, tx, ty]
                    if dist_targs * self.mvlim < d2t:
                        moveset.add_move(ax, ay, nx, ny)
                        moveset.add_move(nx, ny, ax, ay)

        return moveset

    def process_moved_into(self, gm, moveset):
        iter_pieces = set()
        moved_into = np.zeros_like(gm.owned)
        for (ax, ay), (tx, ty, _) in moveset.move_dict.items():
            if gm.strn[ax, ay] <= self.mvinto_strlim:
                moved_into[tx, ty] = True
                iter_pieces.add((ax, ay))

        for ax, ay in iter_pieces:
            if moved_into[ax, ay]:
                moveset.add_move(ax, ay, ax, ay, 0)

        return moveset


import numpy as np
from copy import copy
# from copy import copy
# from scipy.ndimage.filters import gaussian_filter, maximum_filter, generic_filter
# from stats import percentileofscore
import logging
logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


class QMove:
    def __init__(self, x, y, tx, ty, priority, score):
        self.x = x
        self.y = y
        self.tx = tx
        self.ty = ty
        self.priority = priority
        self.score = score

    def __repr__(self):
        repr_ = [self.x, self.y, self.tx, self.ty, self.priority, self.score]
        return '\t'.join([str(x) for x in repr_])


class MoveFinder:
    """Find moves for pieces to make!"""

    def __init__(self, ms, config):
        self.assumed_cstrn = 80
        self.wait_ratio = 5
        self.set_terroir(ms)

    def update(self, ms):
        # self.set_accessibility(ms)
        self.set_value(ms)
        self.set_map(ms)

    def get_moves(self, ms, mr):
        moves = {}
        t2r = np.divide(ms.prodfl, ms.strnc)
        terroir_mask = np.multiply(self.terroir, ms.unclaimed)

        for x, y in ms.owned_locs:
            if ms.strn[x, y] <= (self.wait_ratio * ms.prod[x, y]):
                moves[(x, y)] = QMove(x, y, x, y, 2, 0)
                continue

            str_bonus = 1  # np.sqrt(np.maximum(1, ms.strn[x, y] / ms.strnc))
            t2a = ms.dists[x, y, :, :]
            t2c = np.divide(np.maximum(0, ms.strn - ms.strn[x, y]),
                            max(0.01, ms.prod[x, y]))
            value_dist = np.divide(
                np.multiply(str_bonus, self.value),
                (t2a ** 2) + t2c + t2r
            ) * 0
            terroir_dist = np.divide(
                terroir_mask,
                self.bs2o + (t2a * 5) + 10
            )
            heur_dist = value_dist + terroir_dist
            tx, ty = np.unravel_index(heur_dist.argmax(), value_dist.shape)
            mx, my = self.map[(tx, ty)]
            moves[(x, y)] = QMove(x, y, mx, my, 1, value_dist[tx, ty])
            logging.debug((ms.turn, (x, y), (tx, ty), (mx, my)))
            # np.savetxt("value.txt", self.value)
            # np.savetxt("valuedist.txt", value_dist)
            #  np.savetxt("vcn.txt", np.maximum(0, ms.strn - ms.strn[x, y]))
            # np.savetxt("vcd.txt", max(0.01, ms.prodfl[x, y]))
            # np.savetxt("vc.txt", t2c)

        for k, v in moves.items():
            mr.add_move(v)

    def set_value(self, ms):
        combat_strn = ms.strnc
        combat_strn[np.nonzero(ms.combat)] = np.maximum(
            self.assumed_cstrn, ms.strnc[np.nonzero(ms.combat)])
        # self.value = np.divide(ms.prodfl ** 2, ms.strn)
        self.value = copy(ms.prod)  # + self.terroir * 1000
        self.value[np.nonzero(ms.owned)] = 0

    def set_terroir(self, ms):
        self.terroir = np.zeros_like(ms.prod, dtype=float)
        for x in range(ms.width):
            for y in range(ms.height):
                terroir = np.divide(ms.prod_2, ms.str_to[x, y, :, :])
                terroir[x, y] = 0
                terroir.sort()
                self.terroir[x, y] = np.sum(terroir)
        np.savetxt("terroir.txt", self.terroir)

    def set_map(self, ms):
        self.map = {(x, y): (x, y)
                    for x in range(ms.width) for y in range(ms.height)}
        self.bs2o = np.zeros_like(ms.prod)
        self.bs2o.fill(np.inf)
        Os = np.transpose(np.nonzero(ms.unclaimed))
        Bs = ms.border_locs
        Os_vs = [ms.sp.get_vertex(ox, oy) for (ox, oy) in Os]
        Bs_vs = [ms.sp.get_vertex(bx, by) for (bx, by) in Bs]

        for i, Os_v in enumerate(Os_vs):
            best = np.argmin(ms.sp.path[Os_v, Bs_vs])
            ox, oy = Os[i]
            bx, by = Bs[best]
            self.map[(ox, oy)] = (bx, by)
            self.bs2o[ox, oy] = ms.sp.path[Os_v, Bs_vs][best] + ms.strnc[bx, by]

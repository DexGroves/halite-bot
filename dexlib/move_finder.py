import numpy as np
from copy import copy
# from copy import copy
# from scipy.ndimage.filters import gaussian_filter, maximum_filter, generic_filter
# from stats import percentileofscore
# import logging
# logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


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

    def update(self, ms):
        # self.set_accessibility(ms)
        self.set_value(ms)

    def get_moves(self, ms, mr):
        moves = {}
        t2r = np.divide(ms.prodfl, ms.strnc)
        for x, y in ms.owned_locs:
            if ms.strn[x, y] <= (self.wait_ratio * ms.prod[x, y]):
                moves[(x, y)] = QMove(x, y, x, y, 2, 0)
                continue

            t2a = ms.dists[x, y, :, :]
            t2a[x, y] = 1
            t2c = np.divide(np.maximum(0, ms.strn - ms.strn[x, y]),
                            max(0.01, ms.prod[x, y]))
            value_dist = np.divide(self.value, t2a + t2c + t2r)
            tx, ty = np.unravel_index(value_dist.argmax(), value_dist.shape)

            moves[(x, y)] = QMove(x, y, tx, ty, 1, value_dist[tx, ty])

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
        self.value = copy(ms.prod)
        self.value[np.nonzero(ms.owned)] = 0

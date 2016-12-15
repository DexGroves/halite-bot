import numpy as np
from copy import copy
from scipy.ndimage.filters import gaussian_filter, maximum_filter, generic_filter
from collections import namedtuple
# from stats import percentileofscore
import logging
logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


QMove = namedtuple('Move', 'x y tx ty priority score')


class MoveFinder:
    """Find moves for pieces to make!"""

    def __init__(self, ms, config):
        self.warmongery = config['warmongery']
        self.assumed_combat = config['assumed_combat']
        self.dist_lim = config['dist_lim']

        self.combat_wait = config['combat_wait']
        self.noncombat_wait = config['noncombat_wait']
        self.max_wait = config['max_wait']

        self.globality = 0# 1
        self.min_util = 0.2

        self.min_dpdt = config['min_dpdt']
        self.roi_skew = config['roi_skew']

        self.blur_sigma = config['blur_sigma']

        self.global_exponent = config['global_exponent']

        self.set_base_locality(ms)

    def update(self, ms):
        self.set_locality(ms)
        # self.roi = np.divide(ms.strn + (ms.combat * self.assumed_combat),
        #                      np.maximum(1, ms.prod))
        # self.roi[np.nonzero(mine)] = np.inf

    def get_moves(self, ms, mr):
        moves = {}

        wait_ratio = np.divide(ms.strn, np.maximum(ms.prod, 0.001))
        open_borders = copy(ms.border_mat)

        active_gradient = np.zeros_like(ms.owned, dtype=float)
        assigned_str = np.zeros_like(active_gradient)
        assigned_prod = np.zeros_like(active_gradient)
        assigned_prod.fill(0.0001)

        t2r = np.divide(ms.strn, ms.prodfl)

        Cs = [loc for loc in ms.owned_locs if wait_ratio[loc[0], loc[1]] >= self.noncombat_wait]
        Bs = ms.border_locs
        ret = np.zeros((len(Cs), len(Bs)))

        for i, (x, y) in enumerate(Cs):
            # Gradient for unclaimed border squares
            t2a = ms.dists[x, y, :, :]
            t2c = np.maximum(0, ms.strn - ms.strn[x, y]) / ms.prodfl[x, y]

            gradient = np.divide(ms.prod, (t2a + t2c + t2r))
            gradient = np.multiply(gradient, open_borders)

            # str_bonus = np.maximum(1, ms.strn[x, y] / np.maximum(1, ms.strn)) ** 0.5
            # utilisation = np.divide(np.minimum(1, ms.strn / ms.strn[x, y]), t2a)
            # utilisation = np.minimum(self.min_util, utilisation)
            # gradient *= 1utilisation  # Penalty for not being able to hit 0.1 util.
            # gradient *= str_bonus    # Bonus for having leftover capacity

            # border_infl = np.divide(self.brdr_global, ms.dists[x, y, :, :])
            # gradient += border_infl

            # Assuming order is gucci here
            ret[i, :] = gradient[ms.border_idx].flatten()

        np.savetxt("ret.txt", ret)

        for i in range(len(Cs)):
            ci, bi = np.unravel_index(ret.argmax(), ret.shape)
            cx, cy = Cs[ci]
            tx, ty = Bs[bi]
            moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret[ci, bi]))

            active_gradient[tx, ty] = ret[ci, bi]
            assigned_str[tx, ty] = ms.strn[cx, cy]
            assigned_prod[tx, ty] = ms.prodfl[cx, cy]

            ret[ci, :] = 0
            ret[:, bi] = 0

        # Make a second pass and overwrite any made moves with better ones
        for i, (x, y) in enumerate(Cs):
            # Gradient for unclaimed border squares
            t2a = ms.dists[x, y, :, :]
            t2c = np.divide(np.maximum(0, (ms.strn - assigned_str) - ms.strn[x, y]),
                            assigned_prod)

            gradient = np.divide(ms.prod, (t2a + t2c + t2r))

            # str_bonus = np.maximum(1, ms.strn[x, y] / np.maximum(1, ms.strn)) ** 0.5
            # utilisation = np.divide(np.minimum(1, ms.strn / ms.strn[x, y]), t2a)
            # utilisation = np.minimum(self.min_util, utilisation)
            # gradient *= 1utilisation  # Penalty for not being able to hit 0.1 util.
            # gradient *= str_bonus    # Bonus for having leftover capacity

            # border_infl = np.divide(self.brdr_global, ms.dists[x, y, :, :])
            # gradient += border_infl

            gradient = gradient - active_gradient
            gradient = np.multiply(gradient, active_gradient > 0)
            if (x, y) in moves.keys():
                m = moves[(x, y)]
                gradient[m.tx, m.ty] = 0

            # Assuming order is gucci here
            ret[i, :] = gradient[ms.border_idx].flatten()

        np.savetxt("gret.txt", ret)

        for i in range(len(Cs)):
            ci, bi = np.unravel_index(ret.argmax(), ret.shape)
            cx, cy = Cs[ci]
            tx, ty = Bs[bi]
            if (cx, cy) not in moves.keys() or \
                    ret[ci, bi] > moves[(cx, cy)].score:
                ret[:, bi] = 0
                moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret[ci, bi]))
            ret[ci, :] = 0

        # Assign moves
        for k, v in moves.items():
            mr.add_move(v)

    def set_base_locality(self, ms):
        size = (5, 5)
        origin = (2, 2)
        volume = size[0] * size[1]
        arr_c = 5

        mu_strn = generic_filter(ms.strn, lambda a: a.mean(),
                                 size=size, origin=origin, mode="wrap")
        mu_prod = generic_filter(ms.prod, lambda a: a.mean(),
                                 size=size, origin=origin, mode="wrap")

        self.Pg = volume * mu_prod
        self.t2c = mu_prod - np.divide(arr_c * mu_strn, self.Pg)
        self.base_locality = np.divide(mu_prod, mu_strn)

        data_max = maximum_filter(self.base_locality, 5, mode="wrap")
        self.maxima = (self.base_locality == data_max)

    def set_locality(self, ms):
        """Find the border squares with the best access to production maxima
        and boost them.
        """
        self.brdr_global_num = np.zeros_like(ms.prod, dtype=float)
        self.brdr_global_denom = np.zeros_like(ms.prod, dtype=float)
        self.brdr_global_denom.fill(np.inf)

        self.gateways = []
        maxima = copy(self.maxima)
        maxima[np.nonzero(ms.owned)] = False
        maxima[np.nonzero(ms.enemy)] = False

        # probably a better numpy way to do this
        for mx, my in np.transpose(np.nonzero(maxima)):
            dists = [ms.str_to[mx, my, bx, by] for (bx, by) in ms.border_locs]
            bestx, besty = ms.border_locs[np.argmin(dists)]
            self.brdr_global_num[bestx, besty] += \
                self.base_locality[bestx, besty] * self.globality * ms.capacity  # * c
            self.brdr_global_denom[bestx, besty] = min(
                self.brdr_global_denom[bestx, besty], min(dists))
            self.gateways.append((bestx, besty))

        self.brdr_global = np.divide(self.brdr_global_num, self.brdr_global_denom)
        # self.brdr_global = np.zeros_like(self.brdr_global)
        np.savetxt("mats/brdr_global%i.txt" % ms.turn, self.brdr_global)



#     def set_base_locality(self, ms):
#         """Get the inherent value of squares on the map based on
#         their access to production.
#         """
#         locality_value = np.zeros((ms.width, ms.height))
#         for x in range(ms.width):
#             for y in range(ms.height):
#                 map_value = np.divide(ms.prod, ms.str_to[x, y, :, :])
#                 map_value[x, y] = 0
#                 locality_value[x, y] = np.sum(map_value)
#
#         data_max = maximum_filter(locality_value, 4, mode="wrap")
#
#         self.maxima = (locality_value == data_max)
#         self.base_locality = locality_value
#
#     def set_locality(self, ms):
#         """Find the border squares with the best access to production maxima
#         and boost them.
#         """
#         self.brdr_global = np.zeros_like(ms.prod, dtype=float)
#         self.gateways = []
#         maxima = copy(self.maxima)
#         maxima[np.nonzero(ms.owned)] = False
#         maxima[np.nonzero(ms.enemy)] = False
#
#         # probably a better numpy way to do this
#         for mx, my in np.transpose(np.nonzero(maxima)):
#             dists = [ms.str_to[mx, my, bx, by] for (bx, by) in ms.border_locs]
#             bestx, besty = ms.border_locs[np.argmin(dists)]
#             self.brdr_global[bestx, besty] += \
#                 self.base_locality[mx, my] * np.sqrt(ms.capacity) * \
#                 self.globality  # / np.min(dists)
#             self.gateways.append((bestx, besty))
#         #  np.savetxt("mats/brdr_global%i.txt" % ms.turn, self.brdr_global)

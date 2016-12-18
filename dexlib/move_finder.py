import numpy as np
from copy import copy
from scipy.ndimage.filters import gaussian_filter, maximum_filter, generic_filter
from collections import namedtuple
# from stats import percentileofscore
import logging
logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


# QMove = namedtuple('Move', 'x y tx ty priority score')

class QMove:
    def __init__(self, x, y, tx, ty, priority, score):
        self.x = x
        self.y = y
        self.tx = tx
        self.ty = ty
        self.priority = priority
        self.score = score


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
        moves = {(x, y): QMove(x, y, x, y, 1000, 0)
                 for (x, y) in ms.owned_locs}
        wait_ratio = np.divide(ms.strn, np.maximum(ms.prod, 0.001))

        Cs = [loc for loc in ms.owned_locs
              if wait_ratio[loc[0], loc[1]] >= self.noncombat_wait]
        Bs = ms.border_locs

        cstrn = np.fromiter((ms.strn[x, y] for (x, y) in Cs), int)
        cprod = np.fromiter((ms.prodfl[x, y] for (x, y) in Cs), float)
        bstrn = np.fromiter((ms.strn[bx, by] for (bx, by) in Bs), int)
        bprod = np.fromiter((ms.prodfl[bx, by] for (bx, by) in Bs), float)

        available = np.ones((len(Cs), len(Bs)), dtype=bool)
        ret = np.zeros((len(Cs), len(Bs)))
        t2c = np.zeros((len(Cs), len(Bs)))
        t2a = np.zeros((len(Cs), len(Bs)))
        t2rd = np.zeros((len(Cs), len(Bs)))
        t2r = np.divide(bstrn, bprod)

        assign_id = np.zeros(len(Bs), dtype=int)
        assign_grad = np.zeros(len(Bs))
        assign_str = np.zeros(len(Bs))
        assign_prod = np.zeros(len(Bs))
        assign_prod = np.zeros(len(Bs))
        assign_prod.fill(0.0001)
        # t2a = [ms.dists[x, y, a, b] for (x, y) in Cs for (a, b) in Bs]

        # First pass
        for i, (x, y) in enumerate(Cs):
            t2a[i, ] = ms.dists[x, y, :, :][ms.border_idx].flatten()
            t2c[i, ] = np.maximum(0, bstrn - cstrn[i]) / cprod[i]
            t2rd[i, ] = np.divide(ms.prod_mu * t2a[i, ], bprod)
            ret[i, :] = np.divide(
                bprod,
                (np.maximum(t2a[i, :], t2c[i, :]) + t2r + t2rd[i, :])
            )
        # np.savetxt("mats/cstrn%i.txt" % ms.turn, cstrn)
        # np.savetxt("mats/bstrn%i.txt" % ms.turn, bstrn)
        np.savetxt("mats/ret%i.txt" % ms.turn, ret)
        # np.savetxt("mats/brod%i.txt" % ms.turn, bprod)
        # np.savetxt("mats/t2c%i.txt" % ms.turn, np.maximum(t2a, t2c) + t2r)

        for i in range(len(Cs)):
            ci, bi = np.unravel_index(ret.argmax(), ret.shape)
            if ret[ci, bi] == 0:
                break

            cx, cy = Cs[ci]
            tx, ty = Bs[bi]
            moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret[ci, bi]))

            # if ms.turn > 130:
            #     logging.debug(((cx, cy), (tx, ty), ret[ci, bi], t2a[ci, bi]))

            assign_id[bi] = ci
            assign_grad[bi] = ret[ci, bi]
            assign_str[bi] = cstrn[ci]
            assign_prod[bi] = cprod[ci]
            available[ci, bi] = False  # Mark as impossible for teamups

            ret[ci, :] = 0
            ret[:, bi] = 0

        # Second pass for teamups
        nt2c = np.zeros((len(Cs), len(Bs)))
        for i, (x, y) in enumerate(Cs):
            nt2c[i, ] = np.maximum(0, bstrn - cstrn[i] - assign_str) / assign_prod
            ret[i, :] = np.multiply(
                np.divide(
                    bprod,
                    (np.maximum(t2a[i, :], nt2c[i, :]) + t2r + t2rd[i, :])
                ) - assign_grad,
                available[i, :]
            )

        # np.savetxt("mats/ag%i.txt" % ms.turn, assign_grad)
        # np.savetxt("mats/ap%i.txt" % ms.turn, assign_prod)
        # np.savetxt("mats/gpre%i.txt" % ms.turn, np.divide(bprod, (np.maximum(t2a, nt2c) + t2r)))
        # np.savetxt("mats/gret%i.txt" % ms.turn, ret)
        # np.savetxt("mats/gt2c%i.txt" % ms.turn, np.maximum(t2a, nt2c) + t2r)

        for i in range(len(Cs)):
            # Can I solve better with argpartition?
            ci, bi = np.unravel_index(ret.argmax(), ret.shape)
            if ret[ci, bi] == 0:
                break
            cx, cy = Cs[ci]
            tx, ty = Bs[bi]
            # logging.debug((ms.turn, ret[ci, bi], moves[cx, cy].score))

            if ret[ci, bi] > moves[(cx, cy)].score:
                moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret[ci, bi]))

                hi = assign_id[bi]
                hx, hy = Cs[hi]

                ret[hi, :] = 0  # The helpee can't reassign
                if t2a[hi, bi] == 1 and t2a[ci, bi] == 1:
                    moves[(hx, hy)].priority = -2
                    moves[(cx, cy)].priority = -2

                logging.debug((ms.turn, (cx, cy), (hx, hy), (tx, ty),
                               ret[ci, bi], t2a[ci, bi]))

                ret[:, bi] = 0

            ret[ci, :] = 0

        # Assign moves
        for k, v in moves.items():
            mr.add_move(v)

    def set_base_locality(self, ms):
        pass
        # size = (5, 5)
        # origin = (2, 2)
        # volume = size[0] * size[1]
        # arr_c = 5

        # mu_strn = generic_filter(ms.strn, lambda a: a.mean(),
        #                          size=size, origin=origin, mode="wrap")
        # mu_prod = generic_filter(ms.prod, lambda a: a.mean(),
        #                          size=size, origin=origin, mode="wrap")

        # self.Pg = volume * mu_prod
        # self.t2c = mu_prod - np.divide(arr_c * mu_strn, self.Pg)
        # self.base_locality = np.divide(mu_prod, mu_strn)

        # data_max = maximum_filter(self.base_locality, 5, mode="wrap")
        # self.maxima = (self.base_locality == data_max)

    def set_locality(self, ms):
        """Find the border squares with the best access to production maxima
        and boost them.
        """
        pass
        # self.brdr_global_num = np.zeros_like(ms.prod, dtype=float)
        # self.brdr_global_denom = np.zeros_like(ms.prod, dtype=float)
        # self.brdr_global_denom.fill(np.inf)

        # self.gateways = []
        # maxima = copy(self.maxima)
        # maxima[np.nonzero(ms.owned)] = False
        # maxima[np.nonzero(ms.enemy)] = False

        # # probably a better numpy way to do this
        # for mx, my in np.transpose(np.nonzero(maxima)):
        #     dists = [ms.str_to[mx, my, bx, by] for (bx, by) in ms.border_locs]
        #     bestx, besty = ms.border_locs[np.argmin(dists)]
        #     self.brdr_global_num[bestx, besty] += \
        #         self.base_locality[bestx, besty] * self.globality * ms.capacity  # * c
        #     self.brdr_global_denom[bestx, besty] = min(
        #         self.brdr_global_denom[bestx, besty], min(dists))
        #     self.gateways.append((bestx, besty))

        # self.brdr_global = np.divide(self.brdr_global_num, self.brdr_global_denom)
        # # self.brdr_global = np.zeros_like(self.brdr_global)
        # # np.savetxt("mats/brdr_global%i.txt" % ms.turn, self.brdr_global)



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
         # np.savetxt("mats/mats/brdr_global%i.txt" % ms.turn, self.brdr_global)

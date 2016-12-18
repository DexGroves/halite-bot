import numpy as np
from scipy.ndimage.filters import gaussian_filter, maximum_filter
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

    def __repr__(self):
        repr_ = [self.x, self.y, self.tx, self.ty, self.priority, self.score]
        return '\t'.join([str(x) for x in repr_])


class MoveFinder:
    """Find moves for pieces to make!"""

    def __init__(self, ms, config):
        self.combat_wait = config['combat_wait']
        self.noncombat_wait = config['noncombat_wait']
        self.max_wait = config['max_wait']

        self.globality = 0  # 1
        self.min_util = 0.2
        self.mr_range = 15
        self.mr_k = 0.81
        self.mr_c = 1

        self.assumed_combat = 80

        self.min_dpdt = config['min_dpdt']
        self.roi_skew = config['roi_skew']

        self.blur_sigma = config['blur_sigma']

        self.global_exponent = config['global_exponent']

        self.set_base_locality(ms)

    def update(self, ms):
        self.set_locality(ms)
        self.set_midrange_value(ms)

    def get_combat_moves(self, ms, mr):
        moves = {(x, y): QMove(x, y, x, y, 1000, 0)
                 for (x, y) in ms.owned_combat_locs}

        for x, y in ms.owned_combat_locs:
            if ms.strn[x, y] / ms.prodfl[x, y] <= self.noncombat_wait:
                continue

            comb_val = self.get_combat_values(x, y, ms)
            if comb_val.max() == 0:
                continue

            tx, ty = np.unravel_index(comb_val.argmax(), comb_val.shape)

            moves[(x, y)] = QMove(x, y, tx, ty, 0, comb_val.max())

        # Assign moves
        for k, v in moves.items():
            mr.add_move(v)

    def get_combat_values(self, x, y, ms):
        val = np.zeros((ms.width, ms.height), dtype=int)
        strn = ms.strn[x, y]
        local_area = np.multiply(ms.warzones, ms.dists[x, y, :, :] < 3)

        for cx, cy in np.transpose(np.nonzero(local_area)):
            val[cx, cy] = np.sum([min(s, strn) for s in ms.splash[:, cx, cy]])
            val[cx, cy] += np.sum([p for i, p in enumerate(ms.prod_deny[:, cx, cy])
                                   if strn >= ms.splash[i, cx, cy]])
        return val

    def get_moves(self, ms, mr):
        moves = {(x, y): QMove(x, y, x, y, 1000, 0)
                 for (x, y) in ms.owned_noncombat_locs}
        wait_ratio = np.divide(ms.strn, np.maximum(ms.prod, 0.001))

        Cs = [loc for loc in ms.owned_noncombat_locs
              if wait_ratio[loc[0], loc[1]] >= self.noncombat_wait]
        if len(ms.in_combat_locs) == 0:
            Bs = ms.unclaimed_border_locs
        else:
            Bs = np.vstack([ms.unclaimed_border_locs, ms.in_combat_locs])

        in_combat = np.ones(len(Bs), dtype=bool)
        in_combat[0:len(ms.unclaimed_border_locs)] = False

        cstrn = np.fromiter((ms.strn[x, y] for (x, y) in Cs), int)
        cprod = np.fromiter((ms.prodfl[x, y] for (x, y) in Cs), float)
        bstrn = np.fromiter((ms.strn[bx, by] for (bx, by) in Bs), int)
        bprod = np.fromiter((ms.prodfl[bx, by] for (bx, by) in Bs), float)

        bstrn[in_combat] = np.maximum(self.assumed_combat,
                                      bstrn[in_combat])

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
        assign_id.fill(-1)
        assign_prod.fill(0.0001)

        c_issued = np.zeros(len(Cs), dtype=bool)
        b_taken = np.zeros(len(Bs), dtype=bool)

        bonus = self.mrv[ms.border_idx]
        # t2a = [ms.dists[x, y, a, b] for (x, y) in Cs for (a, b) in Bs]

        # First pass ##########################################################
        for i, (x, y) in enumerate(Cs):
            t2a[i, ] = ms.dists[x, y, :, :][ms.border_idx].flatten()
            t2c[i, ] = np.maximum(0, bstrn - cstrn[i]) / cprod[i]
            t2rd[i, ] = np.divide(ms.prod_mu * t2a[i, ], bprod)
            ret[i, :] = np.divide(
                bprod,
                (np.maximum(t2a[i, :], t2c[i, :]) + t2r + t2rd[i, :])
            ) + bonus
        # np.savetxt("mats/cstrn%i.txt" % ms.turn, cstrn)
        # np.savetxt("mats/bstrn%i.txt" % ms.turn, bstrn)
        # np.savetxt("mats/ret%i.txt" % ms.turn, ret)
        # np.savetxt("mats/brod%i.txt" % ms.turn, bprod)
        # np.savetxt("mats/t2c%i.txt" % ms.turn, np.maximum(t2a, t2c) + t2r)

        for i in range(len(Cs)):
            ci, bi = np.unravel_index(ret.argmax(), ret.shape)
            if ret[ci, bi] == 0:
                break

            cx, cy = Cs[ci]
            tx, ty = Bs[bi]
            moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret[ci, bi]))

            c_issued[ci] = True
            if cstrn[ci] >= bstrn[bi]:
                b_taken[bi] = True
            # if ms.turn > 130:
            #     logging.debug(((cx, cy), (tx, ty), ret[ci, bi], t2a[ci, bi]))

            assign_grad[bi] = ret[ci, bi]
            assign_str[bi] = cstrn[ci]
            assign_prod[bi] = cprod[ci]
            available[ci, bi] = False  # Mark as impossible for teamups

            ret[ci, :] = 0
            ret[:, bi] = 0
            # if assign_id[bi] == -1:
            #     ret[:, bi] = bonus[bi]
            assign_id[bi] = ci

        # Second pass over unassigned cells and new borders ###################
        if len(Cs) == 1:
            nCs = []
        else:
            nCs = [loc for (i, loc) in enumerate(Cs) if not c_issued[i]]

        new_borders = np.zeros_like(ms.border_mat, dtype=bool)
        for bi in range(len(Bs)):
            if b_taken[bi]:
                bx, by = Bs[bi]
                for (nx, ny) in ms.nbrs[bx, by]:
                    new_borders[nx, ny] = True

        new_borders = np.multiply(new_borders, ms.owned == 0)
        new_borders[ms.border_idx] = False
        nB_idx = np.nonzero(new_borders)
        nBs = np.transpose(nB_idx)

        cstrn_sec = np.fromiter((ms.strn[x, y] for (x, y) in nCs), int)
        cprod_sec = np.fromiter((ms.prodfl[x, y] for (x, y) in nCs), float)
        bstrn_sec = np.fromiter((ms.strn[bx, by] for (bx, by) in nBs), int)
        bprod_sec = np.fromiter((ms.prodfl[bx, by] for (bx, by) in nBs), float)

        ret_sec = np.zeros((len(nCs), len(nBs)))
        t2c_sec = np.zeros((len(nCs), len(nBs)))
        t2a_sec = np.zeros((len(nCs), len(nBs)))
        t2rd_sec = np.zeros((len(nCs), len(nBs)))
        t2r_sec = np.divide(bstrn_sec, bprod_sec)

        bonus_sec = self.mrv[nB_idx]

        for i, (x, y) in enumerate(nCs):
            t2a_sec[i, ] = ms.dists[x, y, :, :][nB_idx].flatten()
            t2c_sec[i, ] = np.maximum(0, bstrn_sec - cstrn_sec[i]) / cprod_sec[i]
            t2rd_sec[i, ] = np.divide(ms.prod_mu * t2a_sec[i, ], bprod_sec)
            ret_sec[i, :] = np.divide(
                bprod_sec,
                (np.maximum(t2a_sec[i, :], t2c_sec[i, :]) + t2r_sec + t2rd_sec[i, :])
            ) + bonus_sec

        for i in range(len(nCs)):
            if ret_sec.shape[0] == 0 or ret_sec.shape[1] == 0:
                break

            ci, bi = np.unravel_index(ret_sec.argmax(), ret_sec.shape)
            if ret_sec[ci, bi] == 0:
                break

            cx, cy = nCs[ci]
            tx, ty = nBs[bi]
            moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret_sec[ci, bi]))

            ret_sec[ci, :] = 0
            ret_sec[:, bi] = 0

        # Third pass for teamups ##############################################
        nt2c = np.zeros((len(Cs), len(Bs)))
        for i, (x, y) in enumerate(Cs):
            nt2c[i, ] = np.maximum(0, bstrn - cstrn[i] - assign_str) / assign_prod
            ret[i, :] = np.multiply(
                np.divide(
                    bprod,
                    (np.maximum(t2a[i, :], nt2c[i, :]) + t2r + t2rd[i, :])
                ) - assign_grad + bonus,
                available[i, :]
            )

        # np.savetxt("mats/ag%i.txt" % ms.turn, assign_grad)
        # np.savetxt("mats/ap%i.txt" % ms.turn, assign_prod)
        # np.savetxt("mats/gpre%i.txt" % ms.turn, np.divide(bprod, (np.maximum(t2a, nt2c) + t2r)))
        # np.savetxt("mats/gret%i.txt" % ms.turn, ret)
        # np.savetxt("mats/Cs%i.txt" % ms.turn, Cs)
        # np.savetxt("mats/gt2c%i.txt" % ms.turn, np.maximum(t2a, nt2c) + t2r)

        for i in range(len(Cs)):
            # Can I solve better with argpartition?
            ci, bi = np.unravel_index(ret.argmax(), ret.shape)
            if ret[ci, bi] == 0:
                break
            cx, cy = Cs[ci]
            tx, ty = Bs[bi]
            # logging.debug((ms.turn, ret[ci, bi], moves[cx, cy].score))

            # Note: not handling people getting reassigned in earlier loop here
            # Can probably do this with ret[hi, :] == 0
            if ret[ci, bi] > moves[(cx, cy)].score:
                hi = assign_id[bi]
                hx, hy = Cs[hi]

                if t2a[hi, bi] == 1 and t2a[ci, bi] == 1:
                    moves[(cx, cy)] = (QMove(cx, cy, tx, ty, -2, ret[ci, bi]))
                    moves[(hx, hy)] = (QMove(hx, hy, tx, ty, -2, ret[ci, bi]))
                else:
                    moves[(cx, cy)] = (QMove(cx, cy, tx, ty, 0, ret[ci, bi]))

                ret[hi, :] = 0  # The helpee can't reassign
                # logging.debug((ms.turn, (cx, cy), (hx, hy), (tx, ty),
                #                ret[ci, bi], t2a[ci, bi]))

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

    def set_midrange_value(self, ms):
        # self.Vk = np.zeros((ms.width, ms.height, self.mr_range))
        # self.mrv = np.zeros((ms.width, ms.height))

        # self.Vk[:, :, 0] = np.divide(ms.prod ** 2, ms.strn)
        # self.Vk[:, :, 0][np.where(ms.unclaimed == 0)] = 0
        # # self.mrv += self.Vk[:, :, 0]

        # for k in range(1, self.mr_range):
        #     self.Vk[:, :, k] = max_in_plus(self.Vk[:, :, k - 1])
        #     self.mrv += self.mr_k * self.Vk[:, :, 0]

        # self.mrv *= self.mr_c
        self.mrv = gaussian_filter(np.divide(ms.prod ** 2, ms.strnc),
                                   self.mr_range,
                                   mode="wrap")
        self.mrv *= self.mr_c
        np.savetxt("mrv.txt", self.mrv)


plus_arr = np.array(
    [[False, True, False],
     [True, False, True],
     [False, True, False]]
)


def max_in_plus(a):
    return maximum_filter(a, footprint=plus_arr, origin=(1, 1), mode='wrap')


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
#         np.savetxt("mats/mats/brdr_global%i.txt" % ms.turn, self.brdr_global)

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
        self.assumed_cstrn = config['assumed_cstrn']
        self.wait_ratio = config['wait_ratio']

        self.value_t2a_exp = config['value_t2a_exp']

        self.terr_multi = config['terr_multi']
        self.terr_t2a_multi = config['terr_t2a_multi']
        self.terr_intercept = config['terr_intercept']
        self.enemy_multi = config['enemy_multi']
        self.danger_close_multi = config['danger_close_multi']

        self.set_terroir(ms)

    def update(self, ms):
        # self.set_accessibility(ms)
        self.set_value(ms)
        self.set_map(ms)

    def get_moves(self, ms, mr):
        moves = {}
        t2r = np.divide(ms.prodfl, ms.strnc)
        terroir_mask = self.terroir  # np.multiply(self.terroir, ms.unclaimed)

        for x, y in ms.owned_locs:
            if ms.strn[x, y] <= (self.wait_ratio * ms.prod[x, y]):
                moves[(x, y)] = QMove(x, y, x, y, 2, 0)
                continue

            if ms.warzones[x, y]:
                move = self.get_combat_move(x, y, ms, mr)
                if move.score > 0:
                    moves[(x, y)] = move
                    continue

            str_bonus = 1  # np.sqrt(np.maximum(1, ms.strn[x, y] / ms.strnc))
            t2a = ms.dists[x, y, :, :]
            t2c = np.divide(np.maximum(0, self.combat_strn - ms.strn[x, y]),
                            ms.prodfl[x, y])
            value_dist = np.divide(
                np.multiply(str_bonus, self.value),
                (t2a ** self.value_t2a_exp) + t2c + t2r
            )

            terroir_dist = np.divide(
                terroir_mask,
                self.bs2o + (t2a * self.terr_t2a_multi) + self.terr_intercept
            ) * self.terr_multi

            heur_dist = value_dist + terroir_dist

            combat_bonus = max(1, ms.strn[x, y] / 96) * self.danger_close_multi
            heur_dist[np.nonzero(ms.combat)] *= \
                np.maximum(1, combat_bonus / (8 + ms.dists[x, y, :, :]))[np.nonzero(ms.combat)]

            tx, ty = np.unravel_index(heur_dist.argmax(), value_dist.shape)
            # if ms.dists[x, y, tx, ty] > 3:
            mx, my = self.map[(tx, ty)]
            moves[(x, y)] = QMove(x, y, mx, my, 1, value_dist[tx, ty])
            # else:
            #     moves[(x, y)] = QMove(x, y, tx, tx, 1, value_dist[tx, ty])
            # logging.debug((ms.turn, (x, y), (tx, ty), (mx, my)))

        for k, v in moves.items():
            mr.add_move(v)

    def get_combat_move(self, x, y, ms, mr):
        comb_val = self.get_combat_values(x, y, ms)
        tx, ty = np.unravel_index(comb_val.argmax(), comb_val.shape)
        return QMove(x, y, tx, ty, 0, comb_val.max())

    def get_combat_values(self, x, y, ms):
        val = np.zeros((ms.width, ms.height), dtype=int)
        strn = ms.strn[x, y]
        local_area = np.multiply(ms.warzones, ms.dists[x, y, :, :] < 2)

        for cx, cy in np.transpose(np.nonzero(local_area)):
            val[cx, cy] = np.sum([min(s, strn) for s in ms.splash[:, cx, cy]])
            val[cx, cy] += np.sum([p for i, p in enumerate(ms.prod_deny[:, cx, cy])
                                   if strn >= ms.splash[i, cx, cy]])
        return val

    def set_value(self, ms):
        self.combat_strn = copy(ms.strnc)
        self.combat_strn[np.nonzero(ms.combat)] = np.maximum(
            self.assumed_cstrn, ms.strnc[np.nonzero(ms.combat)])
        # self.value = np.divide(ms.prodfl ** 2, ms.strn)
        self.value = copy(ms.prod)
        self.value[np.nonzero(ms.owned)] = 0
        self.value = self.value.astype(float)

        # self.value[np.nonzero(ms.enemy)] *= self.enemy_multi

    def set_terroir(self, ms):
        self.terroir = np.zeros_like(ms.prod, dtype=float)
        for x in range(ms.width):
            for y in range(ms.height):
                terroir = np.divide(ms.prod_2, ms.str_to[x, y, :, :])
                terroir[x, y] = 0
                terroir.sort()
                self.terroir[x, y] = np.sum(terroir)
        self.terroir[np.where(ms.prod < 3)] = 0
        # self.terroir[np.nonzero(ms.enemy)] *= self.enemy_multi
        #  np.savetxt("terroir.txt", self.terroir)

    def set_map(self, ms):
        self.map = {(x, y): (x, y)
                    for x in range(ms.width) for y in range(ms.height)}
        self.bs2o = np.zeros_like(ms.prod)
        self.bs2o.fill(np.inf)
        Os = np.transpose(np.where(ms.owned == 0))
        Bs = ms.border_locs
        Os_vs = [ms.sp.get_vertex(ox, oy) for (ox, oy) in Os]
        Bs_vs = [ms.sp.get_vertex(bx, by) for (bx, by) in Bs]

        for i, Os_v in enumerate(Os_vs):
            best = np.argmin(ms.sp.path[Os_v, Bs_vs])
            ox, oy = Os[i]
            bx, by = Bs[best]
            self.map[(ox, oy)] = (bx, by)
            self.bs2o[ox, oy] = ms.sp.path[Os_v, Bs_vs][best] + ms.strnc[bx, by]

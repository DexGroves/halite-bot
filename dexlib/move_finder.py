import numpy as np
from copy import copy
from scipy.ndimage.filters import gaussian_filter, maximum_filter
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

        self.globality = 1

        self.min_dpdt = config['min_dpdt']
        self.roi_skew = config['roi_skew']

        self.blur_sigma = config['blur_sigma']

        self.global_exponent = config['global_exponent']

        self.locality_value = self.get_locality_value(ms)

    def update(self, ms):
        pass
        # self.roi = np.divide(ms.strn + (ms.combat * self.assumed_combat),
        #                      np.maximum(1, ms.prod))
        # self.roi[np.nonzero(mine)] = np.inf

    def get_moves(self, ms, mr):
        moves = {}

        locs = ms.owned_locs
        loc_priorities = [-1 * ms.strn[x, y] + ms.dist_from_brdr[x, y] * 1000
                          for (x, y) in locs]
        locs = locs[np.argsort(loc_priorities)]

        wait_ratio = np.divide(ms.strn, np.maximum(ms.prod, 0.001))

        open_borders = copy(ms.border_mat)

        active_set = np.zeros_like(ms.owned)
        active_gradient = np.zeros_like(ms.owned, dtype=float)
        assigned_str = np.zeros_like(active_gradient)
        assigned_prod = np.zeros_like(active_gradient)
        assigned_prod.fill(0.0001)

        t2r = np.divide(ms.strn, ms.prod)

        # Note: do combat here
        # Just move to the best location, but handle teamups here
        for x, y in locs:
            if wait_ratio[x, y] < self.noncombat_wait:
                moves[(x, y)] = (QMove(x, y, x, y, 100, 0))
                continue

            # Gradient for unclaimed border squares
            t2a = ms.dists[x, y, :, :]
            t2c = np.maximum(0, ms.strn - ms.strn[x, y]) / max(0.01, ms.prod[x, y])

            str_bonus = np.maximum(1, ms.strn / ms.strn[x, y]) ** 0.5

            gradient = np.divide(ms.prod, (t2a + t2c + t2r))
            gradient = np.multiply(gradient, open_borders)

            utilisation = np.divide(np.maximum(1, ms.strn / ms.strn[x, y]), t2a)
            utilisation = np.maximum(0.1, utilisation)

            gradient *= utilisation  # Penalty for not being able to hit 0.1 util.
            gradient *= str_bonus    # Bonus for having leftover capacity
            gradient += self.brdr_global

            tx, ty = np.unravel_index(gradient.argmax(), gradient.shape)

            if t2c[tx, ty] > t2a[tx, ty]:  # Don't move if you don't have to
                moves[(x, y)] = (QMove(x, y, x, y, 100, gradient[tx, ty]))
            else:
                moves[(x, y)] = (QMove(x, y, tx, ty, 0, gradient[tx, ty]))

            # Register everything for delta calculations
            active_set[tx, ty] = 1
            open_borders[tx, ty] = 0
            active_gradient[tx, ty] = gradient[tx, ty]
            # active_ttc[tx, ty] = t2c[tx, ty]
            assigned_str[tx, ty] = ms.strn[x, y]
            assigned_prod[tx, ty] = ms.prod[x, y]

        # Make a second pass and overwrite any made moves with better ones
        for x, y in locs:
            if wait_ratio[x, y] < self.noncombat_wait:
                continue

            # Gradient for unclaimed border squares
            t2a = ms.dists[x, y, :, :]
            t2c = np.maximum(0, ms.strn - ms.strn[x, y]) / max(0.01, ms.prod[x, y])

            str_bonus = np.maximum(1, ms.strn / ms.strn[x, y]) ** 0.5

            gradient = np.divide(ms.prod, (t2a + t2c + t2r))
            gradient = np.multiply(gradient, open_borders)

            utilisation = np.divide(np.maximum(1, ms.strn / ms.strn[x, y]), t2a)
            utilisation = np.maximum(0.1, utilisation)

            gradient *= utilisation  # Penalty for not being able to hit 0.1 util.
            gradient *= str_bonus    # Bonus for having leftover capacity
            gradient += self.brdr_global

            # Gradient for active border squares
            new_t2c = np.divide(np.maximum(1, (ms.strn - assigned_str) - ms.strn[x, y]),
                                assigned_prod)
            new_t2c[np.where(new_t2c > t2a)] = np.inf
            # new_t2c[np.where(active_set == 0)] = np.inf
            new_gradient = np.divide(ms.prod, (t2a + new_t2c))
            delta_gradient = new_gradient - gradient
            gradient[active_set] = delta_gradient[np.nonzero(active_set)]

            gradient *= utilisation
            tx, ty = np.unravel_index(gradient.argmax(), gradient.shape)

            # Overwrite moves if better
            if moves[(x, y)].score < gradient[tx, ty]:
                if min(t2c[tx, ty], new_t2c[tx, ty]) > t2a[tx, ty]:
                    moves[(x, y)] = QMove(x, y, x, y, 100, gradient[tx, ty])
                else:
                    moves[(x, y)] = QMove(x, y, tx, ty, 0, gradient[tx, ty])

                # Register everything for delta calculations
                active_set[tx, ty] = 1
                open_borders[tx, ty] = 0
                active_gradient[tx, ty] = gradient[tx, ty]
                # active_ttc[tx, ty] = t2c[tx, ty]
                assigned_str[tx, ty] = ms.strn[x, y]
                assigned_prod[tx, ty] = ms.prod[x, y]

        # Assign moves
        for k, v in moves.items():
            mr.add_move(v)

    def set_base_locality(self, ms):
        """Get the inherent value of squares on the map based on
        their access to production.
        """
        locality_value = np.zeros((ms.width, ms.height))
        for x in range(ms.width):
            for y in range(ms.height):
                map_value = np.divide(ms.prod, ms.str_to[x, y, :, :])
                map_value[x, y] = 0
                locality_value[x, y] = np.sum(map_value)

        data_max = maximum_filter(locality_value, 4, mode="wrap")

        self.maxima = (locality_value == data_max)
        self.base_locality = locality_value

    def set_locality(self, ms):
        """Find the border squares with the best access to production maxima
        and boost them.
        """
        self.brdr_global = np.zeros_like(ms.prod, dtype=float)

        maxima = copy(self.maxima)
        maxima[np.nonzero(ms.owned)] = False
        maxima[np.nonzero(ms.enemy)] = False

        # probably a better numpy way to do this
        for mx, my in np.transpose(np.nonzero(maxima)):
            dists = [ms.str_to[mx, my, bx, by] for (bx, by) in ms.border_locs]
            bestx, besty = ms.border_locs[np.argmin(dists)]
            self.brdr_global[bestx, besty] += \
                self.base_locality[mx, my] * np.sqrt(ms.capacity) * \
                self.globality / np.min(dists)

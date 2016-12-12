import numpy as np
from scipy.ndimage.filters import gaussian_filter, maximum_filter
from collections import namedtuple
# from stats import percentileofscore
# import logging
# logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


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

        self.min_dpdt = config['min_dpdt']
        self.roi_skew = config['roi_skew']

        self.blur_sigma = config['blur_sigma']

        self.global_exponent = config['global_exponent']

        # self.locality_value = self.get_locality_value(ms)

    def update(self, ms):
        pass
        # self.roi = np.divide(ms.strn + (ms.combat * self.assumed_combat),
        #                      np.maximum(1, ms.prod))
        # self.roi[np.nonzero(mine)] = np.inf

    def get_moves(self, ms, mr):
        locs = ms.owned_locs
        loc_priorities = [-1 * ms.strn[x, y] + ms.dist_from_brdr[x, y] * 1000
                          for (x, y) in locs]
        locs = locs[np.argsort(loc_priorities)]

        active_set = ms.border_mat

        wait_ratio = np.divide(ms.strn, np.maximum(ms.prod, 0.001))
        # Note: do combat here
        # Just move to the best location, but handle teamups here
        for x, y in locs:
            if wait_ratio[x, y] < self.noncombat_wait:
                mr.add_move(QMove(x, y, x, y, 100, 0))
                continue

            t2a = ms.dists[x, y, :, :]
            t2c = np.maximum(0, ms.strn - ms.strn[x, y]) / max(0.01, ms.prod[x, y])
            troi = t2a + t2c
            gradient = np.divide(ms.prod_2, ms.strn + ms.prod * troi)
            gradient = np.multiply(gradient, active_set)
            tx, ty = np.unravel_index(gradient.argmax(), gradient.shape)

            mr.add_move(QMove(x, y, tx, ty, 0, gradient.max()))

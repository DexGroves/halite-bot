import numpy as np
from dexbot.routing import AllPather
# from scipy.ndimage.filters import gaussian_filter
from dexbot.matrix_tools import DistanceCalculator as dc


class Evaluator(object):
    """Evaluate the worth of blocks on the map."""
    def __init__(self, config, ms):
        self.config = config

        self.blur_val = 3

        self.turn_offset = 0
        self.turn_exponent = 1
        self.turn_severity = 0.1

        self.prod_imped = 5
        self.strn_exponent = 0.7

        self.min_wait = 5
        self.path_lim = 3

        self.base_dist = dc.get_distance_matrix(ms.width, ms.height,
                                                self.turn_exponent) + \
            self.turn_offset

        self.pather = AllPather(self.prod_imped * np.multiply(ms.prod, ms.mine == 1),
                                np.multiply(ms.strn, ms.mine == 0),
                                self.path_lim * ms.total_prod)

    def update(self, ms):
        self.value = ms.value_prod + ms.value_blur * self.blur_val
        self.pather.update(self.prod_imped * np.multiply(ms.prod, ms.mine == 1),
                           np.multiply(ms.strn, ms.mine == 0),
                           ms.border_mat,
                           self.path_lim * ms.total_prod)
        # self.value[np.where(ms.dist_from_mine != 1)] = 0

    def get_move(self, x, y, ms):
        if ms.strn[x, y] <= (ms.prod[x, y] * self.min_wait):
            return x, y

        path_cost = self.pather.get_movement_costs(x, y)
        path_cost[np.where(path_cost == 0)] = np.inf
        path_cost = path_cost ** self.strn_exponent

        turn_cost = self.base_dist[x, y, :, :] * self.turn_severity

        movement_cost = path_cost + turn_cost

        value_prox = np.divide(self.value, movement_cost)
        np.savetxt("mats/valu.txt", self.value)
        np.savetxt("mats/vprox.txt", value_prox)
        np.savetxt("mats/mcost.txt", movement_cost)
        tx, ty = np.unravel_index(value_prox.argmax(), value_prox.shape)

        # return tx, ty
        self.pather.update_xy(tx, ty, self.path_lim * ms.total_prod)
        nx, ny = self.pather.get_path_step(x, y, tx, ty)
        return nx, ny

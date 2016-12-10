import numpy as np
from scipy.ndimage.filters import gaussian_filter

# import logging
# logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


class MoveFinder:
    """Find moves for pieces to make!"""

    def __init__(self, ms):
        self.locality_value = np.zeros((ms.width, ms.height))
        for x in range(ms.width):
            for y in range(ms.height):
                map_value = np.divide(ms.prod, ms.str_to[x, y, :, :])
                map_value[x, y] = 0
                self.locality_value[x, y] = np.sum(map_value)

        np.savetxt("local.txt", self.locality_value)
        self.locality_value = gaussian_filter(self.locality_value, 3, mode="wrap")
        np.savetxt("localblur.txt", self.locality_value)
        print("", file=open('values.txt', 'w'))

    def update(self, ms):
        self.roi_time = np.divide(ms.strn, np.maximum(1, ms.prod))

    def get_target(self, x, y, ms):
        # Simple. Take the block with the minimum time to pay itself back.
        wait_ratio = ms.strn[x, y] / max(ms.prod[x, y], 0.001)
        if wait_ratio < 3:
            return x, y

        cap_time = np.maximum(0, ms.strn + (ms.combat * 80) - ms.strn[x, y]) / \
            max(0.01, ms.prod[x, y])
        arrival_time = ms.dists[x, y, :, :]
        recoup_time = np.divide(ms.prod_mu * ms.dists[x, y, :, :],
                                np.maximum(ms.prod, 0.01))
        total_time = cap_time + arrival_time + recoup_time

        roi_targ = self.roi_time + total_time

        roi_targ = np.multiply(roi_targ, ms.dist_from_owned == 1)
        roi_targ[np.where(roi_targ == 0)] = np.inf

        # value = (1 / roi_targ)
        # np.savetxt("value.txt", value)
        # print(value.max(), file=open('values.txt', 'a'))

        tx, ty = np.unravel_index(roi_targ.argmin(), roi_targ.shape)

        dpdt = (ms.prod[tx, ty] / roi_targ.argmin()) / \
            np.sum(ms.prod[np.nonzero(ms.owned)])
        print(dpdt, file=open('values.txt', 'a'))

        if dpdt < 1e-4 and wait_ratio > 5:
            return self.get_global_target(x, y, ms)

        if wait_ratio < 8 and \
                (cap_time[tx, ty] > ms.dists[x, y, tx, ty] or cap_time[tx, ty] > 5):
            return x, y  # Stay if we may as well not move
        return tx, ty  # Else goooo

    def get_global_target(self, x, y, ms):
        """Get the best target NOT on the border."""
        locality_here = np.divide(self.locality_value, ms.dists[x, y, :, :] ** 1)
        # locality_here[np.nonzero(ms.owned)] = 0
        tx, ty = np.unravel_index(locality_here.argmax(), locality_here.shape)
        return tx, ty

import numpy as np
from scipy.ndimage.filters import gaussian_filter, maximum_filter
# from stats import percentileofscore
# import logging
# logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


class MoveFinder:
    """Find moves for pieces to make!"""

    def __init__(self, ms):
        self.locality_value = self.get_locality_value(ms)
        self.maxima = self.get_maxima(self.locality_value, ms)

        print(np.transpose(np.where(self.maxima)), file=open('values.txt', 'w'))

    def update(self, ms):
        self.roi_time = np.divide(ms.strn, np.maximum(1, ms.prod))
        roi_vals = self.roi_time[np.where(ms.dist_from_owned == 1)]
        self.roi_cutoff = np.percentile(roi_vals, 0.6)
        # print(self.roi_cutoff, file=open("roic.txt", "a"))

        self.maxima = self.get_maxima(self.locality_value, ms)

        print("Turn\t", ms.turn, file=open('values.txt', 'a'))
        print(np.transpose(np.where(self.maxima)), file=open('values.txt', 'a'))

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

        tx, ty = np.unravel_index(roi_targ.argmin(), roi_targ.shape)

        dpdt = (ms.prod[tx, ty] / roi_targ.argmin()) / \
            np.sum(ms.prod[np.nonzero(ms.owned)])
        # print(dpdt, file=open('values.txt', 'a'))

        if dpdt < 1e-4 and wait_ratio > 5 and \
                self.roi_time[tx, ty] > (np.min(self.roi_time) * 1.3) and \
                np.sum(self.maxima) > 0:
                #         self.roi_time[tx, ty] > self.roi_cutoff and \
            return self.get_global_target(x, y, ms)

        if wait_ratio < 8 and \
                (cap_time[tx, ty] > ms.dists[x, y, tx, ty] or cap_time[tx, ty] > 5):
            return x, y  # Stay if we may as well not move
        return tx, ty  # Else goooo

    def get_global_target(self, x, y, ms):
        """Get the best target NOT on the border."""
        locality_here = np.divide(np.multiply(self.locality_value, self.maxima),
                                  ms.dists[x, y, :, :]**0.5)
        locality_here[np.nonzero(ms.owned)] = 0
        tx, ty = np.unravel_index(locality_here.argmax(), locality_here.shape)
        return tx, ty

    def get_locality_value(self, ms):
        """Get the inherent value of squares on the map based on
        their access to production.
        """
        locality_value = np.zeros((ms.width, ms.height))
        for x in range(ms.width):
            for y in range(ms.height):
                map_value = np.divide(ms.prod, ms.str_to[x, y, :, :])
                map_value[x, y] = 0
                locality_value[x, y] = np.sum(map_value)

        np.savetxt("local.txt", locality_value)
        locality_value = gaussian_filter(locality_value, 5, mode="wrap")
        np.savetxt("localblur.txt", locality_value)

        return locality_value

    # def get_locality_value(self, ms):
    #     """Get the inherent value of squares on the map based on
    #     their access to production.
    #     """
    #     roi_time = np.divide(ms.strn, np.maximum(1, ms.prod))

    #     np.savetxt("local.txt", roi_time)
    #     locality_value = gaussian_filter(1 / roi_time, 3, mode="wrap")
    #     np.savetxt("localblur.txt", locality_value)

    #     return locality_value

    def get_maxima(self, value, ms):
        """Get the local maxima of a value matrix where unowned."""
        data_max = maximum_filter(
            np.multiply(value, 1 - ms.owned), 5, mode="wrap")

        maxima = (value == data_max)
        maxima[np.nonzero(ms.owned)] = False
        maxima[np.where(ms.dist_from_owned < 2)] = False

        return maxima

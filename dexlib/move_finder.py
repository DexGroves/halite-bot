import numpy as np

# import logging
# logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


class MoveFinder:
    """Find moves for pieces to make!"""

    def __init__(self):
        pass

    def update(self, ms):
        self.roi_time = np.divide(ms.strn, np.maximum(1, ms.prod))

    def get_target(self, x, y, ms):
        # Simple. Take the block with the minimum time to pay itself back.
        cap_time = np.maximum(0, ms.strn + (ms.combat * 80) - ms.strn[x, y]) / \
            max(1, ms.prod[x, y])
        roi_targ = self.roi_time + \
            (ms.dists[x, y, :, :] * (1 + ms.prod_mu)) + \
            cap_time

        roi_targ = np.multiply(roi_targ, ms.dist_from_owned == 1)
        roi_targ[np.where(roi_targ == 0)] = np.inf

        tx, ty = np.unravel_index(roi_targ.argmin(),
                                  roi_targ.shape)
        if cap_time[tx, ty] > ms.dists[x, y, tx, ty] or \
                cap_time[tx, ty] > 5:
            return x, y  # Stay if we may as well not move
        return tx, ty  # Else goooo

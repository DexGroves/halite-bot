"""Handle the routing from x, y to nx, ny."""


import numpy as np


class Pathfinder(object):

    def __init__(self, map_state):
        self.width = map_state.width
        self.height = map_state.height

    def find_path(self, x, y, nx, ny):
        dists = np.array([
            (y - ny) % self.height,
            (nx - x) % self.width,
            (ny - y) % self.height,
            (x - nx) % self.width
        ])
        dists[dists == 0] = 999
        return np.argmin(dists) + 1

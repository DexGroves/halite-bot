"""Handle the routing from x, y to nx, ny."""


import numpy as np
import random


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
        dist_sort = np.argsort(dists)
        return np.argmin(dists) + 1

    def find_path(self, x, y, nx, ny, map_state):
        dist_north = (y - ny) % self.height
        dist_east = (nx - x) % self.width
        dist_south = (ny - y) % self.height
        dist_west = (x - nx) % self.width

        if dist_north < dist_south:
            ypref, ydist = 1, dist_north
        elif (dist_north == 0):
            ypref, ydist = None, 0
        else:
            ypref, ydist = 3, dist_south

        if dist_east < dist_west:
            xpref, xdist = 2, dist_east
        elif (dist_east == 0):
            xpref, xdist = None, 0
        else:
            xpref, xdist = 4, dist_west

        if random.random() > 0.5:
            if xdist > 0 and map_state.can_move_safely(x, y, xpref):
                return xpref
            elif ydist > 0 and map_state.can_move_safely(x, y, ypref):
                return ypref
            else:
                return 0
        else:
            if ydist > 0 and map_state.can_move_safely(x, y, ypref):
                return ypref
            elif xdist > 0 and map_state.can_move_safely(x, y, xpref):
                return xpref
            else:
                return 0

"""Evaluate the value of capturing each point on the map.
Really this should prioritise weaker (?) opponents. Maybe.
"""

import random
import numpy as np
from hlt import *
from networking import *


class MapEvaluator(object):

    def __init__(self, myID, map):
        self.myID = myID
        self.mapheight = map.height
        self.mapwidth = map.width
        self.nsquares = map.height * map.width
        self.D = self.get_distance_matrix()

        self.values = np.zeros((self.mapwidth, self.mapheight), dtype=int)
        self.strengths = np.zeros((self.mapwidth, self.mapheight), dtype=int)
        self.mine = np.zeros((self.mapwidth, self.mapheight), dtype=int)

    def set_evaluation(self, map):
        """Assess the absolute, reference-independent value of
        capturing a spot."""
        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                site = map.getSite(Location(x, y))

                if site.owner == self.myID:
                    self.strengths[y, x] = 0
                    self.values[y, x] = 0 # min(site.production - site.strength, 30)
                    self.mine[y, x] = 1
                elif site.owner == 0:
                    self.strengths[y, x] = site.strength
                    self.values[y, x] = 255 - site.production
                    self.mine[y, x] = 0
                else:
                    self.strengths[y, x] = site.strength
                    self.values[y, x] = (255 - site.production) * 2.5
                    # min((255 - site.strength), 100) + site.production
                    self.mine[y, x] = 0

    def get_best_pt(self, location, pt_strength, map):
        if pt_strength == 256:
            pt_strength = 257
        Dl = self.offset(self.D, location.x, location.y)
        val = np.divide(self.values, Dl)
        val = np.divide(val, Dl)

        val = np.multiply(val, (self.strengths < pt_strength))
        targ_x, targ_y = np.unravel_index(val.argmax(), val.shape)

        # debug_str = '\t'.join([
        #     repr((location.x, location.y)), repr(pt_strength), "\n",
        #     repr(self.values[location.x, location.y]),
        #     repr(map.getSite(Location(location.x, location.y)).strength),
        #     repr(Dl), "\n",
        #     repr(self.values),  "\n",
        #     repr(val), "\n"
        # ])
        # with open("debug.txt", "a") as f:
        #     f.write(debug_str)

        return (targ_y, targ_x), val[targ_x, targ_y]

    def get_distance_matrix(self):
        D = np.zeros((self.mapwidth, self.mapheight), dtype=float)

        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                min_x = min((x - 0) % self.mapwidth, (0 - x) % self.mapheight)
                min_y = min((y - 0) % self.mapwidth, (0 - y) % self.mapheight)
                D[x, y] = max(min_x + min_y, 1)
        D[D == 2] = 1.5
        return D

    @staticmethod
    def offset(M, x, y):
        return np.roll(np.roll(M, y, 0), x, 1)

    @staticmethod
    def sample_up_to(vec, max):
        cap = min(len(vec), 100)
        samp = random.sample(range(len(vec)), cap)
        return vec[samp]

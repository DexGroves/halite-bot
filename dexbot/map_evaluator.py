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
        max_dim = max(map.height, map.width)
        self.mapheight = map.height
        self.mapwidth = map.width
        self.D = self.get_distance_matrix()

        self.values = np.zeros((self.mapwidth, self.mapheight), dtype=int)
        self.strengths = np.zeros((self.mapwidth, self.mapheight), dtype=int)

    def set_evaluation(self, map):
        """Assess the absolute, reference-independent value of
        capturing a spot."""
        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                site = map.getSite(Location(x, y))

                if site.owner == self.myID:
                    self.strengths[x, y] = 0
                    self.values[x, y] = 0 # min(site.production - site.strength, 30)
                elif site.owner == 0:
                    self.strengths[x, y] = site.strength
                    self.values[x, y] = 255 - site.production
                else:
                    self.strengths[x, y] = site.strength
                    self.values[x, y] = (255 - site.production) * 2.5
                    # min((255 - site.strength), 100) + site.production

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

        return (targ_x, targ_y), val[targ_x, targ_y]

    def get_distance_matrix(self):
        D = np.zeros((self.mapwidth, self.mapheight), dtype=float)

        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                min_x = min((x - 0) % self.mapwidth, (0 - x) % self.mapwidth)
                min_y = min((y - 0) % self.mapheight, (0 - y) % self.mapheight)
                D[x, y] = max(min_x + min_y, 1)
        D[D == 2] = 1.5
        return D

    @staticmethod
    def offset(M, x, y):
        return np.roll(np.roll(M, x, 0), y, 1)

    @staticmethod
    def sample_up_to(vec, max):
        cap = min(len(vec), 100)
        samp = random.sample(range(len(vec)), cap)
        return vec[samp]

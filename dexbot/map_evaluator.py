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

        self.values = np.empty((self.mapwidth, self.mapheight), dtype=int)
        self.strengths = np.empty((self.mapwidth, self.mapheight), dtype=int)
        self.mine = np.zeros((self.mapwidth, self.mapheight), dtype=int)

    def set_evaluation(self, map):
        """Assess the absolute, reference-independent value of
        capturing a spot."""
        for y in range(self.mapheight):
            for x in range(self.mapwidth):
                site = map.getSite(Location(x, y))

                if site.owner == self.myID:
                    self.strengths[x, y] = 0
                    self.values[x, y] = 0 # min(site.production - site.strength, 30)
                    self.mine[x, y] = 1
                elif site.owner == 0:
                    self.strengths[x, y] = site.strength
                    self.values[x, y] = site.production
                else:
                    self.strengths[x, y] = site.strength
                    self.values[x, y] = min((255 - site.strength), 100) + site.production

    def get_best_pt(self, location, pt_strength):
        if pt_strength == 255:
            pt_strength = 256
        Dl = self.offset(self.D, location.x, location.y)
        val = np.divide(self.values, Dl)

        val = np.multiply(val, (self.strengths < pt_strength))
        targ_x, targ_y = np.unravel_index(val.argmax(), val.shape)

        return (targ_x, targ_y), val[targ_x, targ_y]

    def get_distance_matrix(self):
        D = np.zeros((self.mapwidth, self.mapheight), dtype=int)

        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                min_x = min((x - 0) % self.mapwidth, (0 - x) % self.mapheight) - 1
                min_y = min((y - 0) % self.mapwidth, (0 - y) % self.mapheight) - 1
                D[x, y] = max(min_x + min_y, 1)

        return D

    @staticmethod
    def offset(M, x, y):
        return np.roll(np.roll(M, y, 0), x, 1)

    @staticmethod
    def sample_up_to(vec, max):
        cap = min(len(vec), 100)
        samp = random.sample(range(len(vec)), cap)
        return vec[samp]

"""Evaluate the value of capturing each point on the map.
Really this should prioritise weaker (?) opponents. Maybe.
"""

import random
import numpy as np
from hlt import *
from networking import *


class MapEvaluator(object):

    def __init__(self, myID):
        self.myID = myID
        self.mapwidth = 0
        self.mapheight = 0
        self.nsquares = 0

    def set_evaluation(self, map):
        """Assess the absolute, reference-independent value of
        capturing a spot."""
        self.mapheight = map.height
        self.mapwidth = map.width
        self.nsquares = map.height * map.width

        # Filter locs to only enemy points?
        self.values = np.empty(self.nsquares, dtype=int)
        self.strengths = np.empty(self.nsquares, dtype=int)
        self.locs = np.empty(self.nsquares, dtype=tuple)
        self.mine = np.zeros(self.nsquares, dtype=int)

        i = 0
        for y in range(self.mapheight):
            for x in range(self.mapwidth):
                site = map.getSite(Location(x, y))

                self.locs[i] = (x, y)
                if site.owner == self.myID:
                    self.strengths[i] = 0
                    self.values[i] = 0
                    self.mine[i] = 1
                elif site.owner == 0:
                    self.strengths[i] = site.strength
                    self.values[i] = site.strength
                else:
                    self.strengths[i] = site.strength
                    self.values[i] = site.strength * 2
                i = i + 1

    def value_from_point(self, location, pt_strength):
        """Assess the reference-dependent value of capturing a spot."""
        ref_x, ref_y = location
        relative_values = np.zeros(self.nsquares, dtype=float)

        searchspace = np.array(range(self.nsquares))
        searchspace = searchspace[(self.mine == 0) &
                                  (self.strengths <= pt_strength)]
        # print (type(searchspace), len(searchspace), searchspace.shape)
        if len(searchspace) == 0:
            return (0, 0), -99999

        searchspace = self.sample_up_to(searchspace, 50)
        for i in searchspace:
            pt_x, pt_y = self.locs[i]
            min_x = min((pt_x - ref_x) % self.mapwidth,
                        (ref_x - pt_x) % self.mapwidth)
            min_y = min((pt_y - ref_y) % self.mapheight,
                        (ref_y - pt_y) % self.mapheight)
            distance = min_x + min_y

            # with open('err.txt', 'a') as f:
            #     f.write(repr((pt_x, pt_y)) + '\t' + repr((ref_x, ref_y)) + '\t' + repr((min_x, min_y)) + '\n')
            #     f.write(repr(self.values[i]) + '\t' + repr(distance) + '\t\t')
            #     f.write(repr(relative_values[i]) + '\t')
            #     f.write(repr(self.values[i] / distance) + '\n')

            relative_values[i] = self.values[i] / distance


        best_move = np.argmax(relative_values)

        return self.locs[i], max(relative_values)

    @staticmethod
    def sample_up_to(vec, max):
        cap = min(len(vec), 100)
        samp = random.sample(range(len(vec)), cap)
        return vec[samp]

"""Evaluate the value of capturing each point on the game_map.
Really this should prioritise weaker (?) opponents. Maybe.
"""


import numpy as np
from halitesrc.hlt import Location


class MapEvaluator(object):
    """Evaluate the value of capturing each point on the game_map.
    Really this should prioritise weaker (?) opponents. Maybe.
    """
    def __init__(self, my_id, game_map):
        self.my_id = my_id
        self.mapheight = game_map.height
        self.mapwidth = game_map.width
        self.dists = self.get_distance_matrix()

        self.values = np.zeros((self.mapwidth, self.mapheight), dtype=int)
        self.strengths = np.zeros((self.mapwidth, self.mapheight), dtype=int)

    def set_evaluation(self, game_map):
        """Assess the absolute, reference-independent value of
        capturing a spot."""
        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                site = game_map.getSite(Location(x, y))

                if site.owner == self.my_id:
                    self.strengths[x, y] = 0
                    self.values[x, y] = 0 # min(site.production - site.strength, 30)
                elif site.owner == 0:
                    self.strengths[x, y] = site.strength
                    self.values[x, y] = 255 - site.production
                else:
                    self.strengths[x, y] = site.strength
                    self.values[x, y] = (255 - site.production) * 2.5
                    # min((255 - site.strength), 100) + site.production

    def get_best_pt(self, location, pt_strength):
        """Trade board value assessment with a given location's
        distance and strength to come up with the 'optimal' spot
        to move towards.
        """
        if pt_strength == 256:
            pt_strength = 257

        dist_from = self.offset(self.dists, location.x, location.y)
        val = np.divide(self.values, dist_from)
        val = np.divide(val, dist_from)
        val = np.multiply(val, (self.strengths < pt_strength))
        targ_x, targ_y = np.unravel_index(val.argmax(), val.shape)

        # debug_str = '\t'.join([
        #     repr((location.x, location.y)), repr(pt_strength), "\n",
        #     repr(self.values[location.x, location.y]),
        #     repr(game_map.getSite(Location(location.x, location.y)).strength),
        #     repr(dist_from), "\n",
        #     repr(self.values),  "\n",
        #     repr(val), "\n"
        # ])
        # with open("debug.txt", "a") as f:
        #     f.write(debug_str)

        return (targ_x, targ_y), val[targ_x, targ_y]

    def get_distance_matrix(self):
        """Populate initial distance matrix centred at 0, 0.
        This matrix informs the number of moves to get to a square
        with awareness of wraparound.
        """
        dists = np.zeros((self.mapwidth, self.mapheight), dtype=float)

        for x in range(self.mapwidth):
            for y in range(self.mapheight):
                min_x = min((x - 0) % self.mapwidth, (0 - x) % self.mapwidth)
                min_y = min((y - 0) % self.mapheight, (0 - y) % self.mapheight)
                dists[x, y] = max(min_x + min_y, 1)
        dists[dists == 2] = 1.5
        return dists

    @staticmethod
    def offset(M, x, y):
        """Offset a matrix by x and y with wraparound.
        Used to position self.dists for other points.
        """
        return np.roll(np.roll(M, x, 0), y, 1)

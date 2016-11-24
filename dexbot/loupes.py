"""Overlays to calculate which squares can combine to attack a border."""


import numpy as np

# east  = np.array([(1, 0),   (2, 0),   (1, 1),   (1, -1)])
# west  = np.array([(-1, 0),  (-2, 0),  (-1, 1), (-1, -1)])
# south = np.array([(0, 1),   (0, 2),   (-1, 1),   (1, 1)])
# north = np.array([(0, -1),  (0, -2),  (-1, -1),  (1, -1)])

# east  = {(1, 0): 0, (2, 0): 4,   (1, 1): 1,  (1, -1): 3}
# west  = {(-1, 0): 0,(-2, 0): 2,  (-1, 1): 1, (-1, -1): 3}
# south = {(0, 1): 0, (0, 2): 1,  (-1, 1): 2,   (1, 1): 4}
# north = {(0, -1): 0,(0, -2): 3, (-1, -1): 2,  (1, -1): 4}


class Loupe(object):

    def __init__(self, locs, dirs):
        self.locs = np.array(locs)
        self.dirs = np.array(dirs)


# east  = Loupe([(1, 0), (2, 0), (1, 1), (1, -1)],     [0, 4, 1, 3])
# west  = Loupe([(-1, 0), (-2, 0), (-1, 1), (-1, -1)], [0, 2, 1, 3])
# south = Loupe([(0, 1), (0, 2), (-1, 1), (1, 1)],     [0, 1, 2, 4])
# north = Loupe([(0, -1), (0, -2), (-1, -1), (1, -1)], [0, 3, 2, 4])

east  = Loupe([(1, 0),  (2, 0)],  [0, 4])
west  = Loupe([(-1, 0), (-2, 0)], [0, 2])
south = Loupe([(0, 1),  (0, 2)],  [0, 1])
north = Loupe([(0, -1), (0, -2)], [0, 3])

"""Overlays to calculate which squares can combine to attack a border."""


import numpy as np

east  = np.array([(1, 0),   (2, 0),   (1, 1),   (1, -1)])
west  = np.array([(-1, 0),  (-2, 0),  (-1, 1), (-1, -1)])
south = np.array([(0, 1),   (0, 2),   (-1, 1),   (1, 1)])
north = np.array([(0, -1),  (0, -2),  (-1, -1),  (1, -1)])

east_outer  = {(1, 0): 0, (2, 0): 4,   (1, 1): 1,  (1, -1): 3}
west_outer  = {(-1, 0): 0,(-2, 0): 2,  (-1, 1): 1, (-1, -1): 3}
south_outer = {(0, 1): 0, (0, 2): 1,  (-1, 1): 2,   (1, 1): 4}
north_outer = {(0, -1): 0,(0, -2): 3, (-1, -1): 2,  (1, -1): 4}

"""Handle common matrix/loupe operations."""


import numpy as np


def offset(M, x, y):
    """Offset a matrix by x and y with wraparound.
    Used to position self.dists for other points.
    """
    return np.roll(np.roll(M, x, 0), y, 1)


def roll_x(M, x):
    return np.roll(M, x, 0)


def roll_y(M, y):
    return np.roll(M, y, 1)

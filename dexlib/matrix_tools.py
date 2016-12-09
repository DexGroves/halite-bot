"""Handle complicated matrix stuff.
In particular, this module does the important task of calculating
the 4D matrix giving the distance between all points.
"""


import numpy as np
import logging
logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


def get_distance_matrix(width, height, falloff):
    """Process and return a 4D array giving the distances between
    squares. Indexed by x, y, :, :, will return a 2D array of
    distances that all points lie from the point x, y.
    """
    D = get_base_matrix(width, height, falloff)
    out = np.zeros((width, height, width, height), dtype=float)
    for x in range(width):
        for y in range(height):
            out[x, y, :, :] = offset(D, x, y)
    return out


def get_base_matrix(width, height, falloff):
    dists = np.zeros((width, height), dtype=float)

    for x in range(width):
        for y in range(height):
            min_x = min((x - 0) % width, (0 - x) % width)
            min_y = min((y - 0) % height, (0 - y) % height)
            dists[x, y] = max(min_x + min_y, 1)

    return dists ** falloff


def offset(M, x, y):
    """Offset a matrix by x and y with wraparound.
    Used to position self.dists for other points.
    """
    return np.roll(np.roll(M, x, 0), y, 1)


def distance_from_owned(M, mine):
    """Return the minimum distance to get to any point if already
    at all points in xys using 4D array M.
    """
    return np.apply_along_axis(np.min, 0, M[np.nonzero(mine)])


def subtile(M, x, y, Dmax):
    xs = range(x - Dmax, x + Dmax + 1)
    ys = range(y - Dmax, y + Dmax + 1)
    return M.take(xs, mode='wrap', axis=0).take(ys, mode='wrap', axis=1)


def roll_x(M, x):
    return np.roll(M, x, 0)


def roll_y(M, y):
    return np.roll(M, y, 1)

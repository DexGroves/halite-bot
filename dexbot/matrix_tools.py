import numpy as np


class DistanceCalculator(object):
    """Process and return a 4D array giving the distances between
    squares. Indexed by x, y, :, :, will return a 2D array of
    distances that all points lie from the point x, y.
    """

    @classmethod
    def get_distance_matrix(cls, width, height, falloff):
        D = cls.get_base_matrix(width, height, falloff)
        out = np.zeros((width, height, width, height), dtype=float)
        for x in range(width):
            for y in range(height):
                out[x, y, :, :] = cls.offset(D, x, y)
        return out

    @staticmethod
    def get_base_matrix(width, height, falloff):
        dists = np.zeros((width, height), dtype=float)

        for x in range(width):
            for y in range(height):
                min_x = min((x - 0) % width, (0 - x) % width)
                min_y = min((y - 0) % height, (0 - y) % height)
                dists[x, y] = max(min_x + min_y, 1)

        return dists ** falloff

    @staticmethod
    def offset(M, x, y):
        """Offset a matrix by x and y with wraparound.
        Used to position self.dists for other points.
        """
        return np.roll(np.roll(M, x, 0), y, 1)

    @staticmethod
    def distance_from_owned(M, mine):
        """Return the minimum distance to get to any point if already
        at all points in xys using 4D array M.
        """
        return np.apply_along_axis(np.min, 0, M[np.nonzero(mine)])

    @staticmethod
    def subtile(M, x, y, Dmax):
        xs = range(x - Dmax, x + Dmax + 1)
        ys = range(y - Dmax, y + Dmax + 1)
        return M.take(xs, mode='wrap', axis=0).take(ys, mode='wrap', axis=1)

    @staticmethod
    def roll_x(M, x):
        return np.roll(M, x, 0)

    @staticmethod
    def roll_y(M, y):
        return np.roll(M, y, 1)

import numpy as np


class DistanceCalculator(object):
    """Process and return a 4D array giving the distances between
    squares. Indexed by x, y, :, :, will return a 2D array of
    distances that all points lie from the point x, y.
    """

    @classmethod
    def get_distance_matrix(cls, width, height, falloff):
        D = cls._get_base_matrix(width, height, falloff)
        out = np.zeros((width, height, width, height), dtype=float)
        for x in range(width):
            for y in range(height):
                out[x, y, :, :] = cls._offset(D, x, y)
        return out

    @staticmethod
    def _get_base_matrix(width, height, falloff):
        dists = np.zeros((width, height), dtype=float)

        for x in range(width):
            for y in range(height):
                min_x = min((x - 0) % width, (0 - x) % width)
                min_y = min((y - 0) % height, (0 - y) % height)
                dists[x, y] = max(min_x + min_y, 1)

        return dists ** falloff

    @staticmethod
    def _offset(M, x, y):
        """Offset a matrix by x and y with wraparound.
        Used to position self.dists for other points.
        """
        return np.roll(np.roll(M, x, 0), y, 1)

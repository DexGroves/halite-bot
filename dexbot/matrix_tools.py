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


class StrToCalculator(object):
    """Orchestrate the calculation of how hard to reach blank squares are."""

    @classmethod
    def get_str_to(cls, strn, dists, Dmax):
        """Calculate the amount of strength that must be battled through
        tor reach all unowned points.
        """
        brdr_idx = np.where(dists == 1)

        str_to = np.zeros_like(strn)
        str_to.fill(9999999)

        # Need to think about meaning of this more
        str_to[brdr_idx] = np.maximum(strn[brdr_idx], 1)

        for D in range(2, Dmax):
            D_idx = np.where(dists == D)
            str_dist = np.zeros_like(str_to)
            str_dist[D_idx] = str_to[D_idx]
            str_to[D_idx] = strn[D_idx] + cls.jitter(str_dist)[D_idx]

        return str_to

    @classmethod
    def update_str_to(cls, x, y, strn, dists, Dmax, base_str_to):
        sub_str = cls.subtile(base_str_to, x, y, Dmax)

    @staticmethod
    def jitter(M):
        """Turn the external border squares of a matrix into their lowest
        valued neighbour.
        """
        return np.apply_along_axis(
            np.min, 0,
            np.stack(
                [
                    np.roll(M, 1, 0),
                    np.roll(M, -1, 0),
                    np.roll(M, 1, 1),
                    np.roll(M, -1, 1)
                ]
            )
        )

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


def offset(M, x, y):
    """Offset a matrix by x and y with wraparound.
    Used to position self.dists for other points.
    """
    return np.roll(np.roll(M, x, 0), y, 1)


def roll_x(M, x):
    return np.roll(M, x, 0)


def roll_y(M, y):
    return np.roll(M, y, 1)


# test = np.zeros((50, 50), dtype=int)
# %timeit test
# test.fill(10)

# test[25, 25] = 0


# tj = jitter(test)


# tj[23:27, 23:27]


# dm
# coords = np.array([1,1])
# %timeit dm[[1, 1, slice(None), slice(None)]]
# %timeit dm[1, 1]
# dm[(1, 1), :, :]
# dm[1, 1]
# :
# dm[1, 1, None, None].shape

# coords = [[1, 1], [5, 10]]
# coords
# dm[coords]

# %timeit np.stack([dm[x[0], x[1], :, :] for x in coords], 0)


# dm = DistanceCalculator.get_distance_matrix(8, 8, 1)
# test = np.zeros((8, 8))
# test[(1,2)] = 1
# test[(1, 3)] = 1
# test[(1, 4)] = 1
# test[(5, 5)] = 1


# min_dist_by_coord(dm, [(1,2), (1, 3), (1, 4), (5, 5)])

# test = np.zeros((5, 5))

# test[np.array([[1,1],[1,2],[2,2],[2,3]])] = 0


# test = np.zeros((5, 5))
# test[(4, 4)] = 1
# test[(2, 3)] = 1
# test[(1, 4)] = 1

# test
# test[np.nonzero(test)] = 5
# test

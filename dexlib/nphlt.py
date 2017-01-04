"""
A Python-based Halite starter-bot framework.
A barebones, numpy-inspired fork of erdman's hlt.py that focuses on
assembling prod, strn and owner numpy matrices as quickly as possible.
Moves are tuples of x, y and dir, where dir behaves as in the
base starter.

GameMap.prod and GameMap.strn are the production and strength respectively.
GameMap.owner contains each cell's owner.
"""

import sys
import numpy as np
from collections import namedtuple
from scipy.ndimage.filters import generic_filter


Move = namedtuple('Move', 'x y dir')


class GameMap:
    """Hold prod, strn and owners as separate x*y numpy matrices
    and update on each new frame.
    """

    def __init__(self):
        self.my_id = int(get_string())
        size_string = get_string()
        prod_string = get_string()

        self.width, self.height = tuple(map(int, size_string.split()))

        prod = [int(p) for p in prod_string.split()]
        self.prod = np.array(prod, dtype=int).reshape((self.height, self.width)).T

        self.get_frame()

    def get_frame(self, map_string=None):
        if map_string is None:
            map_string = get_string()

        split_string = map_string.split()
        owners = np.zeros(self.width * self.height, dtype=int)

        ctr, strloc = 0, 0
        while ctr < self.width * self.height:
            increment = int(split_string[strloc])
            owner_id = int(split_string[strloc + 1])
            owners[ctr:(ctr + increment)] = owner_id
            ctr += increment
            strloc += 2
        self.owners = owners.reshape((self.height, self.width)).T

        strn = [int(s) for s in split_string[strloc:]]
        self.strn = np.array(strn, dtype=int).reshape((self.height, self.width)).T


def send_string(s):
    sys.stdout.write(s)
    sys.stdout.write('\n')
    sys.stdout.flush()


def get_string():
    return sys.stdin.readline().rstrip('\n')


def send_init(name):
    send_string(name)


def send_frame(moves):
    send_string(' '.join(str(move.x) + ' ' + str(move.y) + ' ' + str(move.dir)
                         for move in moves))


BIGINT = 99999


class ImprovedGameMap(GameMap):
    """Extend the base GameMap with extra information."""
    def __init__(self):
        super().__init__()
        self.dists = self.get_distances(self.width, self.height)
        self.nbrs = self.get_neighbours(self.width, self.height)

    def update(self):
        """Derive everything that changes per frame."""
        self.owned = self.owners == self.my_id
        self.blank = self.owners == 0
        self.enemy = np.ones_like(self.owned) - self.owned - self.blank

        self.splash_dmg = self.plus_filter(self.strn * self.enemy, sum)
        self.heuristic = self.prod / np.maximum(1, self.strn)
        self.heuristic += self.splash_dmg
        self.heuristic[self.owned] = -1

        # self.border = self.plus_filter(self.enemy + self.blank, max) * self.owned
        # Unowned border cells
        self.ubrdr = self.plus_filter(self.owned, max) - self.owned

        # Owned prod and strn
        self.ostrn = self.strn * self.owned
        self.oprod = self.prod * self.owned

        # Lower capped prod and strn
        self.strnc = np.maximum(1, self.strn)
        self.prodc = np.maximum(1, self.prod)

        self.owned_locs = np.transpose(np.nonzero(self.owned))
        self.ubrdr_locs = np.transpose(np.nonzero(self.ubrdr))

    def path_towards(self, x, y, tx, ty):
        """For an owned cell at x, y, and a target cell at tx, ty,
        return the cardinal direction to move along.
        Moves along the shortest nonzero cardinal first.
        """
        dists = np.array([
            (y - ty) % self.height,
            (tx - x) % self.width,
            (ty - y) % self.height,
            (x - tx) % self.width
        ])
        dists[dists == 0] = BIGINT
        distorder = np.argsort(dists)
        return distorder[0] + 1

    @staticmethod
    def get_distances(w, h):
        """Populate a 4-dimensional np.ndarray where:
            arr[x, y, a, b]
        yields the shortest distance between (x, y) and (a, b).
        Indexing as:
            arr[x, y]
        yields a 2D array of the distances from (x, y) to every
        other cell.
        """
        base_dists = np.zeros((w, h), dtype=int)
        all_dists = np.zeros((w, h, w, h), dtype=int)

        for x in range(w):
            for y in range(h):
                min_x = min((x - 0) % w, (0 - x) % w)
                min_y = min((y - 0) % h, (0 - y) % h)
                base_dists[x, y] = max(min_x + min_y, 1)

        for x in range(w):
            for y in range(h):
                all_dists[x, y] = np.roll(np.roll(base_dists, x, 0), y, 1)

        return all_dists

    @staticmethod
    def get_neighbours(w, h):
        """Populate a dictionary keyed by all (x, y) where the
        elements are the neighbours of that cell ordered N, E, S, W.
        """
        def get_local_nbrs(x, y):
            return [(x, (y - 1) % h),
                    ((x + 1) % w, y),
                    (x, (y + 1) % h),
                    ((x - 1) % w, y)]

        nbrs = {(x, y): get_local_nbrs(x, y)
                for x in range(w) for y in range(h)}

        return nbrs

    @staticmethod
    def plus_filter(X, f):
        """Scans a +-shaped filter over the input matrix X, applies
        the reducer function f and returns a new matrix with the same
        dimensions of X containing the reduced values.
        """
        footprint = np.array([[0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0]])
        proc = generic_filter(X, f, footprint=footprint, mode='wrap')
        return proc

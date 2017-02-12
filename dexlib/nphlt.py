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
from scipy.ndimage.filters import generic_filter, maximum_filter
from dexlib.dijkstra import ShortestPather
from dexlib.floodfill import friendly_to


# import logging

# logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")

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
    def __init__(self, com_radius):
        super().__init__()
        self.dists = self.get_distances(self.width, self.height)
        self.nbrs = self.get_neighbours(self.width, self.height)
        self.oneaways = self.get_oneaways(self.width, self.height)
        self.turn = -1

        self.sp = ShortestPather(self.strn, self.prod)
        self.str_to = self.sp.get_dist_matrix()
        self.str_to = np.maximum(self.strn, self.str_to)

        self.original_strn = self.strn.copy()

        self.parity = 0
        self.com_radius = com_radius

        self.last_turn = np.ceil(np.sqrt(self.width * self.height) * 10)

    def update(self):
        """Derive everything that changes per frame."""
        self.turn += 1
        self.owned = (self.owners == self.my_id).astype(int)
        self.blank = self.owners == 0
        self.enemy = np.ones_like(self.owned) - self.owned - self.blank

        # Owned prod and strn
        self.ostrn = self.strn * self.owned
        self.oprod = self.prod * self.owned

        # Lower capped prod and strn
        self.strnc = np.maximum(1, self.strn)
        self.prodc = np.maximum(1, self.prod)

        self.wall = self.blank * (self.strn > 0)

        self.splash_dmg = self.plus_filter(self.strn * self.enemy, sum)
        self.splash_prod = self.plus_filter(self.prod * self.enemy * (self.strn == 0),
                                            sum)
        self.combat_heur = self.splash_dmg + \
            (self.prodc * self.blank * (self.strn == 0)) + \
            (self.prodc * self.enemy * 2) + \
            (self.enemy * 2) + (self.blank * (self.strn == 0)) + \
            self.splash_prod

        # Unowned border cells
        self.ubrdr = self.plus_filter(self.owned, max) - self.owned
        self.obrdr = self.plus_filter(self.ubrdr, max) - self.ubrdr
        self.str_brdr = self.plus_filter(
            (self.strn > 200) * self.owned, max
        ) * self.owned
        self.havens = np.maximum(self.str_brdr, self.obrdr)

        self.owned_locs = np.transpose(np.nonzero(self.owned))
        self.ubrdr_locs = np.transpose(np.nonzero(self.ubrdr))

        # Combat cells
        self.target_cells = self.enemy + (self.blank * (self.strn == 0))
        self.ubrdr_combat = self.ubrdr * self.target_cells
        self.melee_mat = self.plus_filter(self.ubrdr_combat, max) * self.owned

        self.close_to_combat = self.melee_mat.copy()
        for i in range(self.com_radius):
            self.close_to_combat = np.maximum(
                self.close_to_combat, self.plus_filter(self.close_to_combat, max)
            )
        self.close_to_combat -= self.melee_mat
        self.close_to_combat *= self.owned

        if self.target_cells.max() > 0:
            self.dist_from_combat = friendly_to(
                self,
                np.transpose(np.nonzero(self.ubrdr_combat))
            )
        else:
            self.dist_from_combat = np.zeros_like(self.target_cells)

        self.close_to_combat[self.dist_from_combat > self.com_radius] = False
        self.noncombat = self.owned - self.close_to_combat - self.melee_mat

        # Whether cells are stronger than their weakest neighbour
        targets = self.strn * self.blank
        targets[targets == 0] = 256
        self.weakest_nbr = self.plus_filter(targets, min)
        self.gte_nbr = self.ostrn > self.weakest_nbr

        self.calc_bval()
        self.calc_aggs()

    def calc_aggs(self):
        self.total_strn = self.ostrn.sum() + (self.oprod.sum() / 2)
        self.num_enemies = max(1, len(np.unique(self.owners)) - 2)
        self.total_enemy_strn = (self.strn * self.enemy).sum()
        self.ave_enemy_strn = self.total_enemy_strn / self.num_enemies

        self.enemy_walls = (self.blank * (self.strn > 0)) * \
            self.plus_filter(self.enemy, max)
            # maximum_filter(self.enemy, size=3, mode='wrap')

        self.safe_to_take = 1 - self.enemy_walls

        if self.turn == self.last_turn:
            self.safe_to_take.fill(True)
        # if self.total_strn < (200 * self.ave_enemy_strn):
        #     self.safe_to_take = 1 - self.enemy_walls
        # else:
        #     self.safe_to_take = np.ones_like(self.enemy_walls)

    def calc_bval(self):
        """Docstring this because it's complicated."""
        blank_valuable = self.blank * (((self.prodc ** 2) / self.strnc) > 0.0) * \
            (self.strn > 0)
        Bis = self.ubrdr.flatten().nonzero()[0]
        Uis = blank_valuable.flatten().nonzero()[0]
        Uprod = self.prodc.flatten()[Uis]
        Ustrn = self.strnc.flatten()[Uis]
        Ustrn[Ustrn == 0] = 20  # Quick hack

        Bvals = np.zeros(len(Bis), dtype=float)
        self.Mbval = np.zeros_like(self.prod, dtype=float)

        D_BU = self.sp.path[Bis][:, Uis]
        # D_BU_argmin = D_BU.argmin(axis=0)  # Index of closest Bi per Ui

        # Wish I had a clever matrix way to do this. Will come back.
        # for i, amin in enumerate(D_BU_argmin):
        #     dist_bu = D_BU[amin, i] + Ustrn[i]
        #     Bvals[amin] += Uprod[i] / dist_bu
        #     NatB[amin] += 1

        D_BU_min = D_BU.min(axis=0)
        for i, min_ in enumerate(D_BU_min):
            dist_bu = D_BU[:, i][np.where(D_BU[:, i] == min_)] + Ustrn[i] / Uprod[i] + 1

            Bvals[np.where(D_BU[:, i] == min_)] += ((Uprod[i] ** 2) / Ustrn[i]) / dist_bu

        # Bvals /= np.sqrt(NatB)

        for i, Bi in enumerate(Bis):
            bx, by = self.sp.vertices[Bi]
            self.Mbval[bx, by] += Bvals[i]

        # np.savetxt("mats/mbval%i" % self.turn, self.Mbval)

        # np.savetxt("mats/mbval%i" % self.turn, self.Mbval)

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
    def get_oneaways(w, h):
        """Populate a dictionary keyed by all (x, y) where the
        elements are the neighbours of that cell ordered N, E, S, W.
        """
        def get_local_nbrs(x, y):
            return [(x, (y - 2) % h),
                    ((x + 2) % w, y),
                    (x, (y + 2) % h),
                    ((x - 2) % w, y)]

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

    @staticmethod
    def square_filter(X, f):
        """Scans a square-shaped filter over the input matrix X, applies
        the reducer function f and returns a new matrix with the same
        dimensions of X containing the reduced values.
        """
        footprint = np.array([[1, 1, 1],
                              [1, 1, 1],
                              [1, 1, 1]])
        proc = generic_filter(X, f, footprint=footprint, mode='wrap')
        return proc

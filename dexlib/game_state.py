import sys
import numpy as np
from collections import namedtuple
from dexlib.nphlt import GameMap
from dexlib.matrix_tools import get_distance_matrix, distance_from_owned
from dexlib.dijkstra import ShortestPather


Move = namedtuple('Move', 'x y dir')


class GameState(GameMap):
    """Extend GameMap to contain everything we need to make money."""

    def __init__(self, size_string, prod_string, my_id):
        super().__init__(size_string, prod_string, my_id)
        self.dists = get_distance_matrix(self.width, self.height, 1)
        self.dists_inv = 1 / self.dists  # Faster to mult by this

        self.str_to = ShortestPather(self.strn).get_dist_matrix()

    def update(self):
        self._set_id_matrices()
        self._set_distances()  # This is expensiveish
        self._set_globals()

    def _set_id_matrices(self):
        self.blank = np.zeros((self.width, self.height), dtype=bool)
        self.enemy = np.zeros((self.width, self.height), dtype=bool)
        self.owned = np.zeros((self.width, self.height), dtype=bool)

        self.blank[np.where(self.owners == 0)] = True
        self.owned[np.where(self.owners == self.my_id)] = True
        self.enemy[np.where((self.owners != 0) * (self.owners != self.my_id))] = True

        self.owned_locs = np.transpose(np.nonzero(self.owned))

        self.combat = (self.enemy) | (self.strn <= 1)

    def _set_distances(self):
        self.dist_from_owned = distance_from_owned(self.dists, self.owned)
        self.dist_from_owned[np.nonzero(self.owned)] = 0

        self.border_mat = self.dist_from_owned == 1
        self.border_idx = np.where(self.dist_from_owned == 1)
        self.border_locs = np.transpose(self.border_idx)

    def _set_globals(self):
        self.capacity = np.sum(self.prod[np.nonzero(self.owned)])
        self.size = np.sum(self.owned)
        self.prod_mu = self.capacity / self.size


def send_string(s):
    sys.stdout.write(s)
    sys.stdout.write('\n')
    sys.stdout.flush()


def get_string():
    return sys.stdin.readline().rstrip('\n')


def get_init():
    my_id = int(get_string())
    m = GameState(get_string(), get_string(), my_id)
    return my_id, m


def send_init(name):
    send_string(name)


def send_frame(moves):
    send_string(' '.join(str(move.x) + ' ' + str(move.y) + ' ' + str(move.dir)
                         for move in moves))

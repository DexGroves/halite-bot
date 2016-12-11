import sys
import numpy as np
from collections import namedtuple
from dexlib.nphlt import GameMap
from dexlib.dijkstra import ShortestPather
from dexlib.matrix_tools import get_distance_matrix, distance_from_owned
from dexlib.matrix_tools import roll_x, roll_y


Move = namedtuple('Move', 'x y dir')


class GameState(GameMap):
    """Extend GameMap to contain everything we need to make money."""

    def __init__(self, size_string, prod_string, my_id):
        super().__init__(size_string, prod_string, my_id)
        self.dists = get_distance_matrix(self.width, self.height, 1)
        # self.dists_inv = 1 / self.dists  # Faster to mult by this

        self.str_to = ShortestPather(self.strn).get_dist_matrix()
        self.turn = -1

    def update(self):
        self._set_id_matrices()
        self._set_distances()  # This is expensiveish
        self._set_splashes()
        self._set_globals()
        self.turn += 1

    def _set_id_matrices(self):
        self.blank = np.zeros((self.width, self.height), dtype=bool)
        self.enemy = np.zeros((self.width, self.height), dtype=bool)
        self.owned = np.zeros((self.width, self.height), dtype=bool)

        self.blank[np.where(self.owners == 0)] = True
        self.owned[np.where(self.owners == self.my_id)] = True
        self.enemy[np.where((self.owners != 0) * (self.owners != self.my_id))] = True

        self.owned_locs = np.transpose(np.nonzero(self.owned))

    def _set_distances(self):
        """Set self.dist_from_owned, a 2D array of the number of
        moves required to reach the target block from _any_ owned.
        """
        self.dist_from_owned = distance_from_owned(self.dists, self.owned)
        self.dist_from_owned[np.nonzero(self.owned)] = 0

        self.border_mat = self.dist_from_owned == 1
        self.border_idx = np.where(self.dist_from_owned == 1)
        self.border_locs = np.transpose(self.border_idx)

        self.combat = (self.enemy) | (self.strn <= 1)
        self.in_combat = np.multiply(self.combat, self.dist_from_owned == 1)

    def _set_splashes(self):
        """Get splash damage possibilities. self.splash is a 3D
        array where the z-axis is splash on different axes,
        (NESW, still). Total splash damage is:
            [min(strn_attacker, axis) for axis in splash[:, x, y]]
        prod_deny is a similar affair of how much production can be denied
        by a move.
        """
        enemy_strn = np.multiply(self.enemy, self.strn)
        # Strictly this info is one turn out of date, = bad decisions
        self.splash = np.stack([
            enemy_strn,
            roll_x(enemy_strn, 1),
            roll_x(enemy_strn, -1),
            roll_y(enemy_strn, 1),
            roll_y(enemy_strn, -1),
        ])

        enemy_prod = np.multiply(self.blank + self.enemy, self.prod)
        self.prod_deny = np.stack([
            enemy_prod,
            roll_x(enemy_prod, 1),
            roll_x(enemy_prod, -1),
            roll_y(enemy_prod, 1),
            roll_y(enemy_prod, -1),

        ])

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

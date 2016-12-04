import itertools
import numpy as np
from copy import copy
from scipy.ndimage.filters import gaussian_filter
from dexbot.matrix_tools import DistanceCalculator as dc


class MapState(object):
    """Hold the state of the map, and derive important features."""
    def __init__(self, my_id, game_map, config):
        self.width = game_map.width
        self.height = game_map.height
        self.my_id = my_id

        self.blur_sigma = 4  # Config these
        self.blur_exponent = 1

        self.base_dist = dc.get_distance_matrix(self.width, self.height, 1)

        self.turn = 0

        self.set_production(game_map)
        self.set_map_parameters(game_map)
        self.set_unowned()
        self.nbrs = self.get_all_neighbours_dict()

    def update(self, game_map):
        self.set_map_parameters(game_map)
        self.set_unowned()
        self.turn += 1

    def set_production(self, game_map):
        self.prod = np.zeros((self.width, self.height), dtype=int)
        for x in range(game_map.width):
            for y in range(game_map.height):
                self.prod[x, y] = game_map.contents[y][x].production

    def set_map_parameters(self, game_map):
        """Update all the internal numpy matrices."""
        self.mine = np.zeros((self.width, self.height), dtype=bool)
        self.enemy = np.zeros((self.width, self.height), dtype=bool)
        self.blank = np.zeros((self.width, self.height), dtype=bool)

        self.strn = np.zeros((self.width, self.height), dtype=int)

        for x in range(game_map.width):
            for y in range(game_map.height):
                self.strn[x, y] = game_map.contents[y][x].strength

                owner = game_map.contents[y][x].owner
                if owner == 0:
                    self.blank[x, y] = True
                elif owner == self.my_id:
                    self.mine[x, y] = True
                else:
                    self.enemy[x, y] = True

        self.dist_from_mine = dc.distance_from_owned(self.base_dist, self.mine)
        self.dist_from_mine[np.nonzero(self.mine)] = 0

        self.border_mat = self.dist_from_mine == 1
        self.border_idx = np.where(self.dist_from_mine == 1)
        self.border_locs = np.transpose(self.border_idx)

        self.mine_strn = np.zeros_like(self.mine)
        self.mine_strn[np.nonzero(self.mine)] = self.strn[np.nonzero(self.mine)]

        self.blank_strn = copy(self.strn)
        self.blank_strn[np.where(self.blank == 0)] = 99999
        self.blank_strn[np.where(self.strn == 0)] = 99999

        self.total_prod = np.sum(np.multiply(self.mine, self.prod))

    def set_unowned(self):
        self.value_prod = copy(self.prod)
        self.value_prod[np.where(self.blank == 0)] = 0
        self.value_prod[np.where(self.strn == 0)] = 0

        self.value_prod = np.divide((self.value_prod ** self.blur_exponent),
                                    self.blank_strn)
        self.value_blur = gaussian_filter(self.value_prod, self.blur_sigma,
                                          mode="wrap")
        self.value_blur[np.where(self.blank == 0)] = 0
        self.value_blur[np.where(self.strn == 0)] = 0

        np.savetxt("mats/bstrn%i.txt" % self.turn, self.blank_strn)
        np.savetxt("mats/vblur%i.txt" % self.turn, self.value_blur)
        np.savetxt("mats/vprod%i.txt" % self.turn, self.value_prod)

    def get_self_locs(self):
        return np.transpose(np.where(self.mine == 1))

    def can_move_safely(self, x, y, cardinal):
        nx, ny = self.cardinal_to_nxny(cardinal, x, y)

        return self.can_occupy_safely(x, y, nx, ny)

    def can_occupy_safely(self, x, y, nx, ny):
        if self.mine[nx, ny]:
            return True

        if self.strn[x, y] >= 255:
            return True

        if self.strn[nx, ny] < self.strn[x, y]:
            return True

        return False

    def cardinal_to_nxny(self, x, y, cardinal):
        if cardinal == 1:
            return x, (y - 1) % self.height
        elif cardinal == 2:
            return (x + 1) % self.width, y
        elif cardinal == 3:
            return x, (y + 1) % self.height
        elif cardinal == 4:
            return (x - 1) % self.width, y
        return x, y

    def nxny_to_cardinal(self, x, y, nx, ny):
        dx, dy = (nx - x), (ny - y)
        if dx == self.width - 1:
            dx = -1
        if dx == -1 * (self.width - 1):
            dx = 1
        if dy == self.height - 1:
            dy = -1
        if dy == -1 * (self.height - 1):
            dy = 1

        if (dx, dy) == (0, 0):
            return 0
        elif (dx, dy) == (0, -1):
            return 1
        elif (dx, dy) == (1, 0):
            return 2
        elif (dx, dy) == (0, 1):
            return 3
        elif (dx, dy) == (-1, 0):
            return 4
        else:
            print("FUCK", x, y, nx, ny)
            # raise CardinalityError

    def get_neighbours(self, x, y):
        return [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]

    def get_allied_neighbours(self, x, y):
        nbrs = [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]
        return [n for n in nbrs if self.mine[n[0], n[1]]]

    def get_all_neighbours_dict(self):
        allxy = itertools.product(range(self.width), range(self.height))
        return {(x, y): self.get_neighbours(x, y) for (x, y) in allxy}


class CardinalityError(ValueError):
    """What did you do?!"""
    pass

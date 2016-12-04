"""Hold the state of the map, and derive important features."""

import numpy as np
import itertools
from copy import copy
from dexbot.matrix_tools import DistanceCalculator as dc
from dexbot.matrix_tools import StrToCalculator as stc
from dexbot.pathing import StrPather, InternalPather


class MapState(object):

    def __init__(self, my_id, game_map, config):
        self.width = game_map.width
        self.height = game_map.height
        self.my_id = my_id

        self.base_dist = dc.get_distance_matrix(self.width, self.height, 1)

        self.set_production(game_map)
        self.set_map_parameters(game_map)

        # self.sp = StrPather(self.unowned_strn, self.prod)
        self.sp = StrPather(self.blank_strn, self.prod)
        self.ip = InternalPather(self.prod, self.mine, self.border_mat)

        self.nbrs = self.get_all_neighbours_dict()

        self.orig_strn = copy(self.strn)

    def update(self, game_map):
        self.set_map_parameters(game_map)
        self.sp.update(self.blank_strn, self.mine, self.border_mat)
        # self.sp.update(self.unowned_strn, self.mine, self.border_mat)
        self.ip.update(self.prod, self.mine, self.border_mat)

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

        self.dist_from_mine = stc.distance_from_owned(self.base_dist, self.mine)
        self.dist_from_mine[np.nonzero(self.mine)] = 0

        self.border_mat = self.dist_from_mine == 1
        self.border_idx = np.where(self.dist_from_mine == 1)
        self.border_locs = np.transpose(self.border_idx)

        self.border_strn = np.zeros((self.width, self.height), dtype=int)
        self.border_strn.fill(np.inf)
        self.border_strn[self.border_idx] = self.strn[self.border_idx]

        self.mine_strn = np.zeros_like(self.strn)
        self.mine_strn[np.nonzero(self.mine)] = self.strn[np.nonzero(self.mine)]

        self.blank_strn = np.zeros_like(self.strn)
        self.blank_strn[np.nonzero(self.blank)] = self.strn[np.nonzero(self.blank)]

        self.unowned_strn = np.zeros_like(self.strn)
        self.unowned_strn[np.nonzero(self.blank)] = self.strn[np.nonzero(self.blank)]
        self.unowned_strn[np.nonzero(self.enemy)] = self.strn[np.nonzero(self.enemy)]

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

        # if self.prod[nx, ny] == 0 and self.strn[x, y] < 200 and self.strn[nx, ny] > 25:
        #     return False

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

    def get_splash_from(self, x, y):
        nbrs = [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]
        return np.sum([self.prod[nx, ny]
                       for (nx, ny) in nbrs if self.enemy[nx, ny]])

    def get_all_neighbours_dict(self):
        allxy = itertools.product(range(self.width), range(self.height))
        return {(x, y): self.get_neighbours(x, y) for (x, y) in allxy}


class CardinalityError(ValueError):
    """What did you do?!"""
    pass

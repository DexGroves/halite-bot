"""Hold the state of the map, and derive important features."""


import numpy as np
import dexbot.matrix_roller as mr
from dexbot.distance_calculator import DistanceCalculator as dc


class MapState(object):

    def __init__(self, game_map):
        self.width = game_map.width
        self.height = game_map.height

        self._set_production(game_map)
        self.update(game_map)

    def update(self, game_map):
        self._set_map_parameters(game_map)
        self._set_border_squares()

    def register_move(self, x, y, cardinal):
        self.mine[x, y] = 0
        self.strn[x, y] = 0

    def get_self_locs(self):
        return np.transpose(np.where(self.mine == 1))

    def get_border_locs(self):
        return np.transpose(np.where(self.border == 1))

    def can_move_safely(self, x, y, cardinal):
        if cardinal == 1:
            nx, ny = x, (y-1) % self.height
        elif cardinal == 2:
            nx, ny = (x+1) % self.width , y
        elif cardinal == 3:
            nx, ny = x, (y+1) % self.height
        elif cardinal == 4:
            nx, ny = (x-1) % self.width, y

        if self.mine[nx, ny]:
            return True

        stronger = self.strn[nx, ny] < self.strn[x, y]
        if stronger | (self.strn[x, y] >= 255):
            return True

        return False

    def _set_production(self, game_map):
        self.prod = np.zeros((self.width, self.height), dtype=int)
        for x in range(game_map.width):
            for y in range(game_map.height):
                self.prod[x, y] = game_map.contents[y][x].production

    def _set_map_parameters(self, game_map):
        """Update all the internal numpy matrices."""
        self.mine = np.zeros((self.width, self.height), dtype=int)
        self.enemy = np.zeros((self.width, self.height), dtype=int)
        self.blank = np.zeros((self.width, self.height), dtype=int)
        self.strn = np.zeros((self.width, self.height), dtype=int)
        self.mine_strn = np.zeros((self.width, self.height), dtype=int)

        for x in range(game_map.width):
            for y in range(game_map.height):
                self.strn[x, y] = game_map.contents[y][x].strength

                owner = game_map.contents[y][x].owner
                if owner == 0:
                    self.blank[x, y] = 1
                    self.mine_strn[x, y] = 0
                elif owner == 1:
                    self.mine[x, y] = 1
                    self.mine_strn[x, y] = game_map.contents[y][x].strength
                else:
                    self.enemy[x, y] = 1
                    self.mine_strn[x, y] = 0

    def _set_border_squares(self):
        self.border = np.zeros((self.width, self.height), dtype=int)

        self.border += mr.roll_x(self.mine, 1)
        self.border += mr.roll_x(self.mine, -1)
        self.border += mr.roll_y(self.mine, 1)
        self.border += mr.roll_y(self.mine, -1)
        self.border += self.mine

        self.border = np.minimum(self.border, 1)
        self.border -= self.mine

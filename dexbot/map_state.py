"""Hold the state of the map, and derive important features."""


import numpy as np
import dexbot.matrix_roller as mr


class MapState(object):

    def __init__(self, my_id, game_map):
        self.width = game_map.width
        self.height = game_map.height
        self.my_id = my_id

        self._set_production(game_map)
        self.update(game_map)

    def update(self, game_map):
        self._set_map_parameters(game_map)
        self._set_border_squares()
        self._set_danger_close()
        self._set_combat_zones()
        self._set_aggregate_stats()

    def register_move(self, x, y, cardinal):
        nx, ny = self.cardinal_to_nxny(x, y, cardinal)
        self.strn[nx, ny] = min(self.strn[nx, ny] + self.strn[x, y], 255)

        self.mine[x, y] = 0  # This is a hack to save some unnecessary searches
        self.strn[x, y] = 0

    def get_self_locs(self):
        return np.transpose(np.where(self.mine == 1))

    def get_border_locs(self):
        #  return np.transpose(np.where((self.border - self.combat) == 1))
        return np.transpose(np.where(self.border == 1))

    def get_combat_locs(self):
        if np.sum(self.combat) == 0:
            return []
        return np.transpose(np.where(np.multiply(self.combat, self.mine == 1)))

    def can_move_safely(self, x, y, cardinal):
        nx, ny = self.cardinal_to_nxny(cardinal, x, y)

        return self.can_occupy_safely(x, y, nx, ny)

    def can_occupy_safely(self, x, y, nx, ny):
        # if self.originally_mine[nx, ny] and (self.strn[nx, ny] + self.strn[x, y]) > 350:
        #    return False

        if self.mine[nx, ny]:
            return True

        if self.danger_close[nx, ny]:
            return False

        if self.strn[x, y] >= 255:
            return True

        if self.prod[nx, ny] == 0 and self.strn[x, y] < 200 and self.strn[nx, ny] > 25:
            return False

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
            print(repr((x, y)) + '\t' + repr((nx, ny)) + '\t' + repr((dx, dy)) + repr((self.width, self.height)))
            raise CardinalityError

    def get_neighbours(self, x, y):
        return [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]

    def get_allied_neighbours(self, x, y):
        nbrs = [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]
        return [n for n in nbrs if self.mine[n[0], n[1]]]

    def _set_production(self, game_map):
        self.prod = np.zeros((self.width, self.height), dtype=int)
        for x in range(game_map.width):
            for y in range(game_map.height):
                self.prod[x, y] = game_map.contents[y][x].production

    def _set_map_parameters(self, game_map):
        """Update all the internal numpy matrices."""
        self.mine = np.zeros((self.width, self.height), dtype=int)
        self.enemy = np.zeros((self.width, self.height), dtype=int)
        self.eid = np.zeros((self.width, self.height), dtype=int)
        self.blank = np.zeros((self.width, self.height), dtype=int)
        self.strn = np.zeros((self.width, self.height), dtype=int)
        self.mine_strn = np.zeros((self.width, self.height), dtype=int)

        # self.originally_mine = copy(self.mine)

        for x in range(game_map.width):
            for y in range(game_map.height):
                self.strn[x, y] = game_map.contents[y][x].strength

                owner = game_map.contents[y][x].owner
                if owner == 0:
                    self.blank[x, y] = 1
                elif owner == self.my_id:
                    self.mine[x, y] = 1
                    self.mine_strn[x, y] = game_map.contents[y][x].strength
                else:
                    self.enemy[x, y] = 1
                    self.eid[x, y] = owner
        self.num_enemy = len(np.unique(self.eid)) - 1

    def _set_aggregate_stats(self):
        self.mine_area = np.sum(self.mine)
        self.mine_sum_strn = np.sum(self.mine_strn)
        self.ideal_radius = np.sqrt(self.mine_area / np.pi)
        self.density = self.mine_sum_strn / self.mine_area

        self.enemy_strn = np.sum(self.strn) - self.mine_sum_strn
        self.enemy_mean_strn = self.enemy_strn / self.num_enemy

        self.enemies_close = np.sum(np.multiply(self.border, self.enemy_border)) > 0

    def _set_border_squares(self):
        self.border = np.zeros((self.width, self.height), dtype=int)

        self.border += mr.roll_x(self.mine, 1)
        self.border += mr.roll_x(self.mine, -1)
        self.border += mr.roll_y(self.mine, 1)
        self.border += mr.roll_y(self.mine, -1)
        self.border += self.mine

        self.border = np.minimum(self.border, 1)

        self.mine_border = np.multiply(self.border, self.mine)

        self.border -= self.mine
        self.all_border = self.border
        self.border = self.border - self.enemy

        self.enemy_border = np.zeros((self.width, self.height), dtype=int)
        self.enemy_border += mr.roll_x(self.enemy, 1)
        self.enemy_border += mr.roll_x(self.enemy, -1)
        self.enemy_border += mr.roll_y(self.enemy, 1)
        self.enemy_border += mr.roll_y(self.enemy, -1)
        self.enemy_border += self.enemy
        self.enemy_border = np.minimum(self.enemy_border, 1)
        self.enemy_border -= self.enemy

    def _set_combat_zones(self):
        enemies = np.zeros((self.width, self.height), dtype=int)

        enemies += self.enemy
        enemies += mr.roll_x(self.enemy, 1)
        enemies += mr.roll_x(self.enemy, 2)
        enemies += mr.roll_x(self.enemy, 3)
        enemies += mr.roll_x(self.enemy, -1)
        enemies += mr.roll_x(self.enemy, -2)
        enemies += mr.roll_x(self.enemy, -3)
        enemies += mr.roll_y(self.enemy, 1)
        enemies += mr.roll_y(self.enemy, 2)
        enemies += mr.roll_y(self.enemy, 3)
        enemies += mr.roll_y(self.enemy, -1)
        enemies += mr.roll_y(self.enemy, -2)
        enemies += mr.roll_y(self.enemy, -3)
        enemies = np.minimum(enemies, 1)

        blanks_base = np.multiply(self.blank, self.strn < 5)
        blanks = np.zeros((self.width, self.height), dtype=int)
        blanks += mr.roll_x(blanks_base, 1)
        # blanks += mr.roll_x(blanks_base, 2)
        # blanks += mr.roll_x(blanks_base, 3)
        blanks += mr.roll_x(blanks_base, -1)
        # blanks += mr.roll_x(blanks_base, -2)
        # blanks += mr.roll_x(blanks_base, -3)

        blanks += mr.roll_y(blanks_base, 1)
        # blanks += mr.roll_y(blanks_base, 2)
        # blanks += mr.roll_y(blanks_base, 3)
        blanks += mr.roll_y(blanks_base, -1)
        # blanks += mr.roll_y(blanks_base, -2)
        # blanks += mr.roll_y(blanks_base, -3)
        blanks = np.minimum(blanks, 1)

        self.combat = (blanks + enemies) == 2

        enemy_strn = np.multiply(self.enemy, self.strn)
        self.enemy_1brd = np.zeros((self.width, self.height), dtype=int)
        self.enemy_2brd = np.zeros((self.width, self.height), dtype=int)

        self.enemy_1brd += mr.roll_x(enemy_strn, 1)
        self.enemy_1brd += mr.roll_x(enemy_strn, -1)
        self.enemy_1brd += mr.roll_y(enemy_strn, 1)
        self.enemy_1brd += mr.roll_y(enemy_strn, -1)

        self.enemy_2brd += mr.roll_x(self.enemy_1brd, 1)
        self.enemy_2brd += mr.roll_x(self.enemy_1brd, -1)
        self.enemy_2brd += mr.roll_y(self.enemy_1brd, 1)
        self.enemy_2brd += mr.roll_y(self.enemy_1brd, -1)

    def _set_danger_close(self):
        self.danger_close = np.zeros((self.width, self.height), dtype=int)
        # if self.enemy_mean_strn > self.mine_sum_strn:
        #     self.danger_close += mr.roll_x(self.enemy, 1)
        #     self.danger_close += mr.roll_x(self.enemy, -1)
        #     self.danger_close += mr.roll_y(self.enemy, 1)
        #     self.danger_close += mr.roll_y(self.enemy, -1)
        #     self.danger_close += mr.roll_x(self.enemy, 2)
        #     self.danger_close += mr.roll_x(self.enemy, -2)
        #     self.danger_close += mr.roll_y(self.enemy, 2)
        #     self.danger_close += mr.roll_y(self.enemy, -2)
        #     self.danger_close += self.enemy

        #     self.danger_close = np.minimum(self.danger_close, 1)
        #     self.danger_close = np.multiply(self.danger_close, self.blank)
        #     self.danger_close = np.multiply(self.danger_close, self.strn > 80)


class CardinalityError(ValueError):
    """What did you do?!"""
    pass

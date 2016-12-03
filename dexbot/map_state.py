"""Hold the state of the map, and derive important features."""


import itertools
import numpy as np
from scipy.sparse import dok_matrix
from scipy.sparse.csgraph import dijkstra
from dexbot.matrix_tools import DistanceCalculator as dc
from dexbot.matrix_tools import StrToCalculator as stc


class MapState(object):

    def __init__(self, my_id, game_map, config):
        self.width = game_map.width
        self.height = game_map.height
        self.my_id = my_id

        self.base_dist = dc.get_distance_matrix(self.width, self.height, 1)

        self.set_production(game_map)
        self.set_map_parameters(game_map)

        self.sp = ShortestPather(self.blank_strn)

    def update(self, game_map):
        self.set_map_parameters(game_map)
        self.sp.update(self.blank_strn)

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

        self.border_idx = np.where(self.dist_from_mine == 1)
        self.border_locs = np.transpose(self.border_idx)

        self.border_strn = np.zeros((self.width, self.height), dtype=int)
        self.border_strn.fill(np.inf)
        self.border_strn[self.border_idx] = self.strn[self.border_idx]

        self.mine_strn = np.zeros_like(self.strn)
        self.mine_strn[np.nonzero(self.mine)] = self.strn[np.nonzero(self.mine)]

        self.blank_strn = np.zeros_like(self.strn)
        self.blank_strn[np.nonzero(self.blank)] = self.strn[np.nonzero(self.blank)]

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
            raise CardinalityError

    def get_neighbours(self, x, y):
        return [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]

    def get_allied_neighbours(self, x, y):
        nbrs = [self.cardinal_to_nxny(x, y, cardinal) for cardinal in [1, 2, 3, 4]]
        return [n for n in nbrs if self.mine[n[0], n[1]]]


class ShortestPather(object):
    """Calculate shortest paths about the place.
    Too slow to update fully each iteration, so will only be updated in part.
    Might be worth upgrading to Anytime Dynamic A* since it seems to
    solve this problem exactly.
    """

    def __init__(self, strn, strn_lim=1000, update_d=5):
        # Can consider setting harder searches for smaller maps.
        self.strn_lim = strn_lim
        self.update_d = update_d

        self.w, self.h = strn.shape
        self.vertices = itertools.product(range(self.w), range(self.h))

        self.dist = self.get_dist(strn)
        self.path = dijkstra(self.dist, False, limit=strn_lim)

        self.prior_strn = strn

    def update(self, strn):
        """Recompute distances and (niamhly) update self.path for a
        set of changed vertices.
        """
        self.dist = self.get_dist(strn)
        d_strn = np.transpose(np.nonzero(self.prior_strn - strn))

        vis = [self.get_vertex(x, y) for (x, y) in d_strn]
        self.path[vis] = dijkstra(self.dist, False, indices=vis,
                                  limit=self.strn_lim)

        self.prior_strn = strn

    def get_dist(self, costs):
        """Set the x*y distance matrix."""
        dist = dok_matrix((self.w * self.h, self.w * self.h), dtype=int)

        for x, y in self.vertices:
            nbrs = self.get_neighbours_and_costs(x, y, costs)
            orig_i = self.get_vertex(x, y)

            for (nx, ny), cost in nbrs.items():
                targ_i = self.get_vertex(nx, ny)
                dist[orig_i, targ_i] = cost

        return dist

    def update_path_acquisition(self, x, y):
        """Niamhly update the path for one, hypothetical block acquisition."""
        # Mock the strn in place
        orig_strn = self.prior_strn[x, y]
        self.prior_strn[x, y] = 0
        hypo_dist = self.get_dist(self.prior_strn)
        self.prior_strn[x, y] = orig_strn

        return dijkstra(hypo_dist, False, indices=self.get_vertex(x, y),
                        limit=self.strn_lim)

    def get_neighbours_and_costs(self, x, y, cost):
        """Return a dictionary of the neighbours and cost of x, y."""
        neighbours = [((x + 1) % self.w, y), ((x - 1) % self.w, y),
                      (x, (y + 1) % self.h), (x, (y - 1) % self.h)]
        with open("debug.txt", "w") as f:
            f.write(repr((x, y)) + '\t' + repr(neighbours) + '\n' + repr(cost))
        return {(nx, ny): cost[nx, ny] for (nx, ny) in neighbours}

    def get_vertex(self, x, y):
        """Return the index of vertices containing the pt x, y."""
        return (x * self.h) + y


class CardinalityError(ValueError):
    """What did you do?!"""
    pass

"""Classes to help with playing the earlygame."""


import numpy as np
from dexbot.distance_calculator import DistanceCalculator as dc


class EarlyTactician(object):

    """Expose a move that returns moves based on the earlygame state."""

    def __init__(self, map_state, order, max_t):
        self.order = order
        self.max_t = max_t

        self.centre = map_state.get_self_locs()[0]

        self.base = dc.get_base_matrix(map_state.width, map_state.height, 1)
        self.base[0, 0] = 0
        self.dists = dc.offset(self.base, self.centre[0], self.centre[1])

        self.handover = False

    def update(self, map_state):
        self.max_t -= 1
        locs = map_state.get_self_locs()
        for loc in locs:
            new_dist = dc.offset(self.base, loc[0], loc[1])
            self.dists = np.minimum(self.dists, new_dist)

        if self.max_t <= 1:
            self.handover = True

    def find_optimal_move(self, x, y, map_state):
        """Loop over all indices up to order in order to determine
        the best move. Inefficient, can probably do something better
        with recursion starting at the outside, but for now f it.
        x, y unused but required for future multi piece logic.
        """
        moves, value = self._find_best_move_value(x, y, 0,
                                                  self.max_t, map_state)

        return moves[0]

    def _find_best_move_value(self, x, y, cur_order, rem_time, map_state):
        hons = self._find_higher_order_neigbours(x, y, map_state)

        if cur_order == self.order:  # Reached the last step!
            vals = np.zeros(len(hons), dtype=float)
            for i, (nx, ny) in enumerate(hons):
                ttc = self._time_to_cap(x, y, nx, ny, map_state)
                if ttc <= rem_time:
                    vals[i] = map_state.prod[nx, ny]

            best_move = np.argmax(vals)
            return [[hons[best_move]], vals[best_move]]

        else:
            vals = np.zeros(len(hons), dtype=float)
            moves = np.zeros(len(hons), dtype=list)
            for i, (nx, ny) in enumerate(hons):
                ttc = self._time_to_cap(x, y, nx, ny, map_state)
                if ttc <= rem_time:
                    nm, nval = self._find_best_move_value(nx, ny, cur_order + 1,
                                                          rem_time - ttc, map_state)
                    moves[i] = nm
                    vals[i] = map_state.prod[nx, ny] + nval

            best_move = np.argmax(vals)
            return [[hons[best_move]] + [moves[best_move]], vals[best_move]]

    def _find_higher_order_neigbours(self, x, y, map_state):
        order = self.dists[x, y]
        neighbours = map_state.get_neighbours(x, y)

        return [n for n in neighbours if self.dists[n[0], n[1]] == (order + 1)]

    def _time_to_cap(self, ox, oy, ux, uy, map_state):
        """Time to capture a piece."""
        own_prod = map_state.prod[ox, oy]

        if own_prod == 0:
            return 9999  # Arbitrarily large. Very big number. Wooow.

        turns = np.max(map_state.strn[ux, uy] - map_state.mine_strn[ox, oy], 0) /\
            own_prod  # In case zero

        return turns


class TeamerUpper(object):
    """Handle teaming up to capture border areas in the earlygame."""

    def __init__(self):
        pass

    def cost_to_move(self):
        pass

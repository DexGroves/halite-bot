"""Classes to help with playing the earlygame."""


import numpy as np
from dexbot.distance_calculator import DistanceCalculator as dc


class EarlyTactician(object):

    """Expose a move that returns moves based on the earlygame state."""

    def __init__(self, map_state, order, max_t):
        self.order = order
        self.max_t = max_t

        self.centre = map_state.get_self_locs()[0]

        self.dists = dc.get_base_matrix(map_state.width, map_state.height, 1)
        self.dists = dc.offset(self.dists, self.centre[0], self.centre[1])
        self.dists[self.centre[0], self.centre[1]] = 0

        with open('hon.txt', 'w') as f:
            f.write('\n')
        with open('vd.txt', 'w') as f:
            f.write('\n')

    def find_optimal_move(self, x, y, map_state):
        """Loop over all indices up to order in order to determine
        the best move. Inefficient, can probably do something better
        with recursion starting at the outside, but for now f it.
        x, y unused but required for future multi piece logic.
        """
        moves, value = self._find_best_move_value(self.centre[0], self.centre[1], 0,
                                                  self.max_t, map_state)

        with open('vd.txt', 'a') as f:
            f.write(repr(moves) + '\t' + repr(value) + '\n')

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

        with open('hon.txt', 'a') as f:
            f.write(repr(order) + '\n' + repr(neighbours) + '\n'
                    )

        return [n for n in neighbours if self.dists[n[0], n[1]] == (order + 1)]

    def _time_to_cap(self, ox, oy, ux, uy, map_state):
        """Time to capture a piece."""
        own_prod = map_state.prod[ox, oy]

        if own_prod == 0:
            return 9999  # Arbitrarily large. Very big number. Wooow.

        turns = np.max(map_state.strn[ux, uy] - map_state.mine_strn[ox, oy], 0) /\
            own_prod  # In case zero

        return turns

    # def _build_val_dict(self, x, y, cur_order, map_state):
    #     if cur_order == self.order:
    #         # Need to trade this off against time to cap somehow
    #         return map_state.prod[x, y]

    #     next_locs = self._find_higher_order_neigbours(x, y, map_state)
    #     val_dict = {loc: None for loc in next_locs}
    #     for nx, ny in val_dict.keys():
    #         val = map_state.prod[x, y]
    #         dvdt_dict = self._build_val_dict(nx, ny, cur_order + 1, map_state)
    #         ttc = self.max_t - self._time_to_cap(x, y, nx, ny, map_state)

    #         # val_dict[(nx, ny)] = [(nx, ny)], val + dvdt
    #         val_dict[(nx, ny)] = {k: v}

    #     return val_dict

    # def _find_move_from_vals(self, cur_dict):
    #     for k, v in cur_dict.items():
    #         if isinstance(v, dict):
    #             cur_dict[k] = self._find_move_from_vals(v)

    #     max_val = np.max([vals for k, (locs, vals) in cur_dict.items()])
    #     max_locs = [locs + [k] for k, (locs, vals) in cur_dict.items()
    #                 if vals == max_val]

    #     return max_locs

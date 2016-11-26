"""Assess the value of squares."""


import numpy as np
import dexbot.matrix_roller as mr
from dexbot.distance_calculator import DistanceCalculator as dc


class Appraiser(object):

    def __init__(self, map_state, config):
        # self.config = config
        self.config = config
        self.dists = dc.get_distance_matrix(map_state.width,
                                            map_state.height,
                                            self.config['falloff'])

    def set_value(self, map_state):
        self.value = np.zeros((map_state.width, map_state.height), dtype=float)

        self.value = \
            np.multiply(map_state.blank, map_state.prod) + \
            np.multiply(map_state.enemy, map_state.prod) * self.config['epm'] + \
            np.multiply(map_state.blank, map_state.strn) * self.config['bsm']

        enemy_strn_value = np.multiply(map_state.enemy, map_state.strn)
        self.value += enemy_strn_value * self.config['esm']

        splash = enemy_strn_value * self.config['splash']
        self.value += mr.roll_x(splash, 1)
        self.value += mr.roll_x(splash, -1)
        self.value += mr.roll_y(splash, 1)
        self.value += mr.roll_y(splash, -1)

        self.prox_base = np.multiply(
            self.value,
            ((map_state.blank * self.config['bprox']) +
             (map_state.enemy * self.config['eprox']))
        )

        self.stay_value = np.divide(
            map_state.prod * self.config['stay_val'],
            np.maximum(map_state.strn, 0.01)
        )

        self.stay_value += (map_state.mine_border * self.config['stay_border_bonus'])

        # self.can_stay = map_state.mine_strn <= self.config['max_stay_strn']
        size_excl = ((map_state.mine_strn +
                      (map_state.ideal_radius * map_state.density)) > self.config['max_edge_str'])
        too_strn = map_state.mine_strn >= self.config['max_stay_strn']
        self.can_stay = ~(size_excl | too_strn)

        self.set_border_values(map_state)

    def value_at_point(self, x, y):
        static_value = self.value[x, y]
        prox_value = np.divide(self.prox_base, self.dists[x, y, :, :])

        return static_value + np.sum(prox_value)

    def get_best_target(self, map_state, x, y):
        if map_state.strn[x, y] == 256:
            map_state.strn[x, y] = 257

        prox_masked = np.multiply(self.prox_base,
                                  map_state.strn < map_state.strn[x, y]
                                  # map_state.all_border)
                                  # self.brdr_value_m
                                  )
        prox_value = np.divide(prox_masked, self.dists[x, y, :, :])

        targ_x, targ_y = np.unravel_index(prox_value.argmax(), prox_value.shape)

        return (targ_x, targ_y), prox_value[targ_x, targ_y]

    def set_border_values(self, map_state):
        self.brdr_locs = map_state.get_border_locs()
        self.brdr_value = np.empty(len(self.brdr_locs), dtype=float)

        self.brdr_value_m = np.zeros((map_state.width, map_state.height),
                                     dtype=float)

        for i, (x, y) in enumerate(self.brdr_locs):
            if map_state.prod[x, y] == 0 or map_state.danger_close[x, y]:
                self.brdr_value[i] = 0
            else:
                val = self.value_at_point(x, y)
                self.brdr_value[i] = val
                self.brdr_value_m[x, y] = val

    def get_stay_value(self, x, y):
        if self.can_stay[x, y]:
            return self.stay_value[x, y]
        return 0

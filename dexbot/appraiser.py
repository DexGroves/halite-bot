"""Assess the value of squares."""


import numpy as np
import dexbot.matrix_roller as mr
from dexbot.distance_calculator import DistanceCalculator as dc


class Appraiser(object):

    def __init__(self, map_state, config):
        # self.config = config
        self.config = {
            'epm':     1.10,
            'bsm':    -0.01,
            'esm':    -0.01,
            'eprox':    1.1,
            'splash':   0.1,
            'stay_val': 1.8,
            'max_edge_str': 180,
            'max_stay_strn': 140,
            'falloff' : 2.0
        }
        self.dists = dc.get_distance_matrix(map_state.width,
                                            map_state.height,
                                            self.config['falloff'])

    def set_value(self, map_state):
        self.value = np.zeros((map_state.width, map_state.height), dtype=float)

        self.value = \
            np.multiply(map_state.blank, map_state.prod) + \
            np.multiply(map_state.enemy, map_state.prod) * self.config['epm'] + \
            np.multiply(map_state.blank, map_state.strn) * self.config['bsm']

        enemy_value = np.multiply(map_state.enemy, map_state.strn)
        self.value += enemy_value * self.config['esm']

        splash = enemy_value * self.config['splash']
        self.value += mr.roll_x(splash, 1)
        self.value += mr.roll_x(splash, -1)
        self.value += mr.roll_y(splash, 1)
        self.value += mr.roll_y(splash, -1)

        self.prox_base = np.multiply(
            self.value,
            map_state.blank + (map_state.enemy * self.config['eprox'])
        )

        self.stay_value = np.divide(
            map_state.prod * self.config['stay_val'],
            np.maximum(map_state.strn, 0.01)
        )

        # self.can_stay = map_state.mine_strn <= self.config['max_stay_strn']
        size_excl = ((map_state.mine_strn + \
                      (map_state.ideal_radius * map_state.density)) > self.config['max_edge_str'])
        too_strn =  map_state.mine_strn >= self.config['max_stay_strn']
        self.can_stay = ~(size_excl | too_strn)

    def value_at_point(self, x, y):
        static_value = self.value[x, y]
        prox_value = np.divide(self.prox_base, self.dists[x, y, :, :])

        return static_value + np.sum(prox_value)

    def get_best_target(self, map_state, x, y):
        if map_state.strn[x, y] == 256:
            map_state.strn[x, y] = 257

        prox_masked = np.multiply(self.prox_base,
                                  map_state.strn < map_state.strn[x, y])
        prox_value = np.divide(prox_masked, self.dists[x, y, :, :])

        targ_x, targ_y = np.unravel_index(prox_value.argmax(), prox_value.shape)

        return (targ_x, targ_y), prox_value[targ_x, targ_y]

    def get_stay_value(self, x, y):
        if self.can_stay[x, y]:
            return self.stay_value[x, y]
        return 0


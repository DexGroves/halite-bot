import random
import numpy as np
from hlt import Move, CARDINALS, STILL


class DexBot(object):
    """The greatest Halite bot ever, in training."""

    def __init__(self, my_id):
        self.my_id = my_id
        self.map_eval = None

        self.req_value_multi = 0.2
        self.max_strength = 128

    def move(self, location, game_map):
        site = game_map.getSite(location)

        # Capture any enemy neighbours if possible
        for cardinal in random.sample(CARDINALS, 4):
            if self.can_capture(game_map, location, cardinal, site) and \
                    self.is_enemy(game_map, location, cardinal, site):
                return Move(location, cardinal)

        # Else eval value of each point
        target, value = self.map_eval.get_best_pt(location, site.strength)
        stay_value = site.production * self.req_value_multi / max(site.strength, 0.01)
        if value > stay_value or site.strength > self.max_strength:
            # Move towards!
            targ_x, targ_y = target
            dists = np.array([
                (location.y - targ_y) % self.map_eval.mapheight,
                (targ_x - location.x) % self.map_eval.mapwidth,
                (targ_y - location.y) % self.map_eval.mapheight,
                (location.x - targ_x) % self.map_eval.mapwidth
            ])
            dists[dists == 0] = 999
            cardinal = np.argmin(dists) + 1

            # with open('debug.txt', 'a') as f:
            #     f.write('\t'.join([repr(cardinal), repr((targ_x, targ_y)),
            #                        repr(site.strength), repr(dists), '\n']))

            if self.can_move_safely(game_map, location, cardinal, site):
                return Move(location, cardinal)

        # Else chill
        return Move(location, STILL)

    def can_move_safely(self, game_map, location, cardinal, site):
        # Might be worth having avoid-255 logic here
        new_site = game_map.getSite(location, cardinal)
        return (site.strength > new_site.strength) | (site.strength == 255)

    def can_capture(self, game_map, location, cardinal, site):
        new_site = game_map.getSite(location, cardinal)
        return new_site.owner != self.my_id and site.strength > new_site.strength

    def is_enemy(self, game_map, location, cardinal, site):
        new_site = game_map.getSite(location, cardinal)
        return new_site.owner != self.my_id and new_site.owner != 0

    def set_evaluator(self, map_eval):
        self.map_eval = map_eval

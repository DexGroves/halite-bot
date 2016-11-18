import numpy as np
import random
from hlt import *
from networking import *
from dexbot.map_evaluator import MapEvaluator


class DexBot(object):
    """The greatest Halite bot ever, in training."""

    def __init__(self, myID):
        self.id = myID
        self.mapeval = None
        self.req_value_multi = 0.2
        self.max_strength = 128
        self.min_strength_multiplier = 2.5

    def move(self, location, game_map):
        # site = game_map.getSite(location)
        site = game_map.getSite(location)

        # Capture any enemy neighbours if possible
        for d in random.sample(CARDINALS, 4):
            if self.can_capture(game_map, location, d, site) and \
                    self.is_enemy(game_map, location, d, site):
                return Move(location, d)

        # Capture any neighbours if possible
        # for d in random.sample(CARDINALS, 4):
        #    if self.can_capture(game_map, location, d, site):
        #        return Move(location, d)

        # Else eval value of each point
        target, value = self.map_eval.get_best_pt(location, site.strength, game_map)
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
            d = np.argmin(dists) + 1
            # with open('debug.txt', 'a') as f:
            #     f.write('\t'.join([repr(d), repr((targ_x, targ_y)), repr(site.strength), repr(dists), '\n']))

            if self.can_move_safely(game_map, location, d, site):
                return Move(location, d)

        # Else chill
        return Move(location, STILL)

    def can_move_safely(self, game_map, location, d, site):
        # Might be worth having avoid-255 logic here
        new_site = game_map.getSite(location, d)
        return (site.strength > new_site.strength) | (site.strength == 255)

    def can_capture(self, game_map, location, d, site):
        new_site = game_map.getSite(location, d)
        return new_site.owner != self.id and site.strength > new_site.strength

    def is_enemy(self, game_map, location, d, site):
        new_site = game_map.getSite(location, d)
        return new_site.owner != self.id and new_site.owner != 0 and site.strength > new_site.strength

    def set_evaluator(self, map_eval):
        self.map_eval = map_eval

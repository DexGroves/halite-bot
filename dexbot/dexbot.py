import numpy as np
from hlt import *
from networking import *
from dexbot.map_evaluator import MapEvaluator


class DexBot(object):
    """The greatest Halite bot ever, in training."""

    def __init__(self, myID):
        self.id = myID
        self.mapeval = None
        self.req_value = 10

    def move(self, location, game_map):
        # site = game_map.getSite(location)
        # Capture any enemy neighbours if possible
        for d in CARDINALS:
            if self.can_capture(game_map, location, d) and \
                    self.is_enemy(game_map, location, d):
                return Move(location, d)

        # Capture any neighbours if possible
        for d in CARDINALS:
            if self.can_capture(game_map, location, d):
                return Move(location, d)

        # Else eval value of each point
        site = game_map.getSite(location)
        target, value = self.map_eval.value_from_point((location.x, location.y),
                                                       site.strength)
        if value > self.req_value:
            # Move towards!
            targ_x, targ_y = target
            dists = [(targ_y - location.y) % self.map_eval.nsquares,
                     (targ_x - location.x) % self.map_eval.nsquares,
                     (location.y - targ_y) % self.map_eval.nsquares,
                     (location.x - targ_x) % self.map_eval.nsquares]
            d = np.argmin(dists) + 1
            return Move(location, d)

        # Else chill
        return Move(location, STILL)

    def can_capture(self, game_map, location, d):
        site = game_map.getSite(location)
        new_site = game_map.getSite(location, d)
        return new_site.owner != self.id and site.strength > new_site.strength

    def is_enemy(self, game_map, location, d):
        site = game_map.getSite(location)
        new_site = game_map.getSite(location, d)
        return new_site.owner != self.id and new_site.owner != 0 and site.strength > new_site.strength

    def set_evaluator(self, map_eval):
        self.map_eval = map_eval

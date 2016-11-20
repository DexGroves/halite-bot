import numpy as np
from halitesrc.hlt import Move, STILL


class DexBot(object):
    """The greatest Halite bot ever, in training."""

    def __init__(self, my_id, config):
        self.my_id = my_id
        self.map_eval = None

        self.stay_val_multi = config['stay_value_multiplier']
        self.max_strength = config['max_stay_strength']

    def move(self, location, game_map):
        site = game_map.contents[location.y][location.x]

        # Else eval value of each point
        target, value = self.map_eval.get_best_pt(location, site.strength)
        stay_value = site.production * self.stay_val_multi / max(site.strength, 0.01)
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

            if self.can_move_safely(game_map, location, cardinal, site):
                return Move(location, cardinal)

        # Else chill
        return Move(location, STILL)

    def can_move_safely(self, game_map, location, cardinal, site):
        # Might be worth having avoid-255 logic here
        new_site = self.shift_site(location, cardinal, game_map)
        return (site.strength > new_site.strength) | (site.strength >= 255)

    def can_capture_enemy(self, game_map, location, cardinal, site):
        new_site = self.shift_site(location, cardinal, game_map)
        out = new_site.owner != self.my_id and \
                site.strength > new_site.strength and \
                new_site.owner != 0
        return out

    def set_evaluator(self, map_eval):
        self.map_eval = map_eval

    @staticmethod
    def shift_site(location, cardinal, game_map):
        if cardinal == 1:
            new_y = (location.y - 1) % game_map.height
            return game_map.contents[new_y][location.x]
        if cardinal == 2:
            new_x = (location.x + 1) % game_map.width
            return game_map.contents[location.y][new_x]
        if cardinal == 3:
            new_y = (location.y + 1) % game_map.height
            return game_map.contents[new_y][location.x]
        if cardinal == 4:
            new_x = (location.x - 1) % game_map.width
            return game_map.contents[location.y][new_x]

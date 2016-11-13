from hlt import *
from networking import *


class DexBot(object):
    """The greatest Halite bot ever, in training."""

    def __init__(self, myID):
        self.id = myID
        self.sg = Spyglass(myID)
        self.requisite_str = 125

    def move(self, location, gameMap):
        # site = gameMap.getSite(location)
        # Capture any neighbours if possible
        for d in CARDINALS:
            if self.can_capture(gameMap, location, d):
                return Move(location, d)

        # Else, calculate the nearest front, and move towards it if
        # strength at edge > self.requisite_str
        nearest_brdr = self.sg.get_nearest_brdr(location, gameMap)
        str_to_brdr = self.sg.strength_to_brdr(location, gameMap, nearest_brdr)
        if str_to_brdr > self.requisite_str:
            new_site = gameMap.getSite(location, nearest_brdr)
            if new_site.owner == self.id:
                return Move(location, nearest_brdr)

        # Else chill
        return Move(location, STILL)

    def can_capture(self, gameMap, location, d):
        site = gameMap.getSite(location)
        new_site = gameMap.getSite(location, d)
        return new_site.owner != self.id and site.strength > new_site.strength

class Spyglass(object):
    """Scours the map for information."""

    def __init__(self, myID):
        self.id = myID

    def get_nearest_brdr(self, location, gameMap):
        border_dists = self.distance_to_brdr(location, gameMap)
        return min(border_dists, key=border_dists.get)

    def distance_to_brdr(self, location, gameMap):
        distances = {}
        for d in CARDINALS:
            distance = 0
            new_site = gameMap.getSite(location)
            while new_site.owner == self.id:
                distance += 1
                location = self.move_cursor(location, d, gameMap)
                new_site = gameMap.getSite(location)
                if distance > max(gameMap.width, gameMap.height):
                    break
            distances[d] = distance
        return distances

    def strength_to_brdr(self, location, gameMap, d):
        strength = 0
        new_site = gameMap.getSite(location)
        while new_site.owner == self.id:
            strength += new_site.strength
            location = self.move_cursor(location, d, gameMap)
            new_site = gameMap.getSite(location)
            if strength > 255:
                break
        return strength

    @staticmethod
    def move_cursor(location, direction, gameMap):
        max_x = gameMap.width
        max_y = gameMap.height
        if direction == NORTH:
            return Location(location.x, (location.y + 1) % max_y)
        if direction == EAST:
            return Location((location.x + 1) % max_x, location.y)
        if direction == SOUTH:
            return Location(location.x, (location.y - 1) % max_y)
        if direction == WEST:
            return Location((location.x - 1) % max_x, location.y)

from hlt import *
from networking import *


class DexBot(object):
    """The greatest Halite bot ever, in training."""

    def __init__(self, myID):
        self.id = myID
        self.sg = Spyglass(myID)
        self.requisite_str = 125
        self.edges = None, None, None, None

    def move(self, location, gameMap):
        # site = gameMap.getSite(location)
        # Capture any neighbours if possible
        for d in CARDINALS:
            if self.can_capture(gameMap, location, d):
                return Move(location, d)
        # Need to move away from any existing 255's
        # Else, calculate the nearest front, and move towards it if
        # strength at edge > self.requisite_str
        nearest_edge = self.sg.get_nearest_edge(location, self.edges)
        # str_to_brdr = self.sg.strength_to_brdr(location, gameMap, nearest_brdr)
        if gameMap.getSite(location).strength > self.requisite_str:
            new_site = gameMap.getSite(location, nearest_edge)
            if new_site.owner == self.id:
                return Move(location, nearest_edge)

        # Else chill
        return Move(location, STILL)

    def can_capture(self, gameMap, location, d):
        site = gameMap.getSite(location)
        new_site = gameMap.getSite(location, d)
        return new_site.owner != self.id and site.strength > new_site.strength

    def set_edges(self, gameMap):
        owned_locs = []
        for y in range(gameMap.height):
            for x in range(gameMap.width):
                location = Location(x, y)
                if gameMap.getSite(location).owner == self.id:
                    owned_locs.append(location)
        xs = [loc.x for loc in owned_locs]
        ys = [loc.y for loc in owned_locs]
        self.edges = min(xs), max(xs), min(ys), max(ys)

class Spyglass(object):
    """Scours the map for information."""

    def __init__(self, myID):
        self.id = myID

    def get_nearest_brdr(self, location, gameMap):
        border_dists = self.distance_to_brdr(location, gameMap)
        return min(border_dists, key=border_dists.get)

    def distance_to_brdr(self, start_loc, gameMap):
        distances = {}
        for d in CARDINALS:
            distance = 0
            location = start_loc
            new_site = gameMap.getSite(start_loc)
            while new_site.owner == self.id:
                distance += 1
                location = self.move_cursor(location, d, gameMap)
                new_site = gameMap.getSite(location)
                if distance > gameMap.width:
                    break
            distances[d] = distance
        return distances

    def strength_to_brdr(self, location, gameMap, d):
        new_site = gameMap.getSite(location)
        strength = new_site.strength
        while new_site.owner == self.id:
            location = self.move_cursor(location, d, gameMap)
            new_site = gameMap.getSite(location)
            strength += new_site.strength
            if strength > 255:
                break
        return strength

    @staticmethod
    def get_nearest_edge(location, edges):
        ld = location.x - edges[0]
        rd = edges[1] - location.x
        ud = location.y - edges[2]
        dd = edges[3] - location.y
        edge_d = [ud, rd, dd, ld]
        return edge_d.index(min(edge_d)) + 1

    @staticmethod
    def move_cursor(location, direction, gameMap):
        max_x = gameMap.width
        max_y = gameMap.height
        if direction == NORTH:
            return Location(location.x, (location.y - 1) % max_y)  #-????????
        if direction == EAST:
            return Location((location.x + 1) % max_x, location.y)
        if direction == SOUTH:
            return Location(location.x, (location.y + 1) % max_y)  # +????
        if direction == WEST:
            return Location((location.x - 1) % max_x, location.y)

from hlt import *
from networking import *


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

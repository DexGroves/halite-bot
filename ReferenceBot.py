from hlt import *
from networking import *

myID, gameMap = getInit()
sendInit("MyPythonBot")


PRODUCTION_MULTI = 5


def move(location):
    site = gameMap.getSite(location)
    for d in CARDINALS:
        neighbour_site = gameMap.getSite(location, d)
        if neighbour_site.owner != myID and \
                neighbour_site.strength < site.strength:
            return Move(location, d)
    if site.strength < site.production * PRODUCTION_MULTI:
        return Move(location, STILL)
    return Move(location, NORTH if random.random() > 0.5 else WEST)


while True:
    moves = []
    gameMap = getFrame()
    for y in range(gameMap.height):
        for x in range(gameMap.width):
            location = Location(x, y)
            if gameMap.getSite(location).owner == myID:
                moves.append(move(location))
    sendFrame(moves)

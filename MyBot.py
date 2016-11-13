from hlt import *
from networking import *

myID, gameMap = getInit()
sendInit("DexBot")


PRODUCTION_MULTI = 5


def move(location):
    site = gameMap.getSite(location)
    for d in CARDINALS:
        neighbour_site = gameMap.getSite(location, d)
        if neighbour_site.owner != myID and \
                neighbour_site.strength < site.strength:
            return Move(location, d)
    if site.strength > 250:
        return Move(location, random.choice(DIRECTIONS))
    return Move(location, STILL)


while True:
    moves = []
    gameMap = getFrame()
    for y in range(gameMap.height):
        for x in range(gameMap.width):
            location = Location(x, y)
            if gameMap.getSite(location).owner == myID:
                moves.append(move(location))
    sendFrame(moves)

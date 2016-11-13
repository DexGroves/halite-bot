from hlt import *
from networking import *
from dexbot.dexbot import DexBot


myID, gameMap = getInit()
sendInit("DexBot")
db = DexBot(myID)


while True:
    moves = []
    gameMap = getFrame()

    db.set_edges(gameMap)

    for y in range(gameMap.height):
        for x in range(gameMap.width):
            location = Location(x, y)
            if gameMap.getSite(location).owner == myID:
                moves.append(db.move(location, gameMap))
    sendFrame(moves)

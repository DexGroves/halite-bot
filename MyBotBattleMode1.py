from hlt import *
from networking import *
from UntidyLogicHahaBattleModeIncludes0StrBlocks import UntidyLogicHaha
import timeit
import gc
import logging

myID, gameMap = getInit()
sendInit("BIGBALLERSHOTCALLERHAHA")
bot = UntidyLogicHaha(myID, gameMap)
productionRate = 5
strengthToMove = 20
logging.basicConfig(filename='example.log', level=logging.DEBUG)

while True:
	start_time = timeit.default_timer()
	maxTime = .95
	#numberOfSquares = len(myShit)
	moves = []
	gameMap = getFrame()
	#myShit = bot.myShit(gameMap)
	capturedLines = bot.capturedLines(gameMap)
	
	goQuick=False #if time is nearly up	
	numSquares = 0
	for y in range(gameMap.height):
		for x in range(gameMap.width):
			if (capturedLines[0][x] == False or capturedLines[1][y] == False):
				if goQuick != True:
					location = Location(x, y)
					site = gameMap.getSite(location)
					if site.owner == myID:
						numSquares+=1
						if productionRate == 0:
							reachedProductionRate = site.strength>=strengthToMove
						else:
							reachedProductionRate = site.strength>=site.production*productionRate
						direction = bot.getClosestFreeEdge(location, gameMap, reachedProductionRate, capturedLines[0][x], capturedLines[1][y])
						moves.append(Move(location, direction))
				else: #times up lets make everything stay still
					moves.append(Move(location, STILL))
				if goQuick == False and (x + y) % 50 == 0:
					if timeit.default_timer() - start_time > maxTime:
						goQuick=True
				
	sendFrame(moves)
	
	if goQuick == True and strengthToMove<235:							
		strengthToMove+=20
		productionRate = 0
	elif goQuick == False and strengthToMove==20:
		productionRate = 5
	elif goQuick == False and strengthToMove>40:
		strengthToMove-=20
		productionRate = 0
	logging.debug(str(myID) + " numSq: " + str(numSquares) + "\n")
	logging.debug(str(myID) + " timeL: " + str(timeit.default_timer() - start_time))
	gc.collect()

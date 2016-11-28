from __future__ import division
import numpy as np
from hlt import Move, WEST, EAST, NORTH, SOUTH, STILL, Location
#import logging


class EdgeWeight:
	def __init__(self, loc=0, weight=255):
		self.loc = loc
		self.weight = weight


class UntidyLogicHaha(object):

	def __init__(self, myID, gameMap):
		self.myID = myID
		self.gameMap = gameMap
	
	#def move(self):
	
	
	def myShit(self, gameMap):
		i=0	
		myShit=[]
		for y in range(gameMap.height):
			for x in range(gameMap.width):
				location = Location(x, y)
				if gameMap.getSite(location).owner == self.myID:
					myShit.append(Location(x,y))
					i+=1
		return i

	def getNextXLocation(self, increment, location):
		newX = location.x + increment
		if newX >= self.gameMap.width:
			return Location(newX - self.gameMap.width, location.y)
		elif newX < 0:
			return Location(self.gameMap.width+newX, location.y)
		return Location(newX, location.y)
	
	def getNextYLocation(self, increment, location):
		newY = location.y + increment
		if newY >= self.gameMap.height:
			return Location(location.x, newY - self.gameMap.height)
		elif newY < 0:
			return Location(location.x, self.gameMap.height + newY)
		return Location(location.x, newY)
		
	def canTake(self, gameMap, myLocation, prospectiveLocation):
		return (gameMap.getSite(myLocation).strength > prospectiveLocation.strength)
		
	def capturedLines(self, gameMap):
		capturedLines = np.zeros((2, max(gameMap.width, gameMap.height)), dtype=bool)
		#for x in range(gameMap.width):
		#	for y in range(gameMap.height):
		#		if gameMap.getSite(Location(x,y)).owner != self.myID:
		#			capturedLines[0,x] = False
		#			capturedLines[1,y] = False
		return capturedLines
				
	def getClosestFreeEdge(self, location, gameMap, reachedProductionRate, xMine, yMine):
		###
		#logging.basicConfig(filename='example.log',level=logging.DEBUG)
		###
		if reachedProductionRate == False:
			return STILL
		gm = gameMap
		x = location.x
		y = location.y
		xDistance = 1
		yDistance = 1
		yFound=0
		xFound=0
		eWeight = 500000.0
		wWeight = 500000.0
		nWeight = 500000.0
		sWeight = 500000.0
		
		eastLocation = self.getNextXLocation(xDistance, location)
		westLocation = self.getNextXLocation(-xDistance, location)
		northLocation = self.getNextYLocation(yDistance, location)
		southLocation = self.getNextYLocation(-yDistance, location)
		
		eastSite = gm.contents[eastLocation.y][eastLocation.x]
		westSite = gm.contents[westLocation.y][westLocation.x]
		northSite = gm.contents[northLocation.y][northLocation.x]
		southSite = gm.contents[southLocation.y][southLocation.x]
		
		#BATTLE MODE
		if sum([(eastSite.owner != self.myID and eastSite.owner != 0) or (eastSite.strength == 0 and eastSite.owner == 0),
			(westSite.owner != self.myID and westSite.owner != 0) or (westSite.strength == 0 and westSite.owner == 0),
			(northSite.owner != self.myID and northSite.owner != 0) or (northSite.strength == 0 and northSite.owner == 0),
			(southSite.owner != self.myID and southSite.owner != 0) or (southSite.strength == 0 and southSite.owner == 0)]) > 0: 
			
			#Get NE/NW/SE/SW
			neastLocation = self.getNextXLocation(xDistance, self.getNextYLocation(-yDistance, location))
			nwestLocation = self.getNextXLocation(-xDistance, self.getNextYLocation(-yDistance, location))
			seastLocation = self.getNextXLocation(xDistance, self.getNextYLocation(yDistance, location))
			swestLocation = self.getNextXLocation(-xDistance, self.getNextYLocation(yDistance, location))
			neastSite = gm.contents[neastLocation.y][neastLocation.x]
			nwestSite = gm.contents[nwestLocation.y][nwestLocation.x]
			seastSite = gm.contents[seastLocation.y][seastLocation.x]
			swestSite = gm.contents[swestLocation.y][swestLocation.x]
			
			#Get NN/NNE/NNW
			nnLocation = self.getNextYLocation(yDistance+1, location)
			nneLocation = self.getNextXLocation(xDistance, nnLocation)
			nnwLocation = self.getNextXLocation(-xDistance, nnLocation)
			nnSite = gm.contents[nnLocation.y][nnLocation.x]
			nneSite = gm.contents[nneLocation.y][nneLocation.x]
			nnwSite = gm.contents[nnwLocation.y][nnwLocation.x]
			
			#Get EE/EEN/EES
			eeLocation = self.getNextXLocation(xDistance+1, location)
			eenLocation = self.getNextYLocation(yDistance, eeLocation)
			eewLocation = self.getNextYLocation(-yDistance, eeLocation)
			eeSite = gm.contents[eeLocation.y][eeLocation.x]
			eenSite = gm.contents[eenLocation.y][eenLocation.x]
			eewSite = gm.contents[eewLocation.y][eewLocation.x]
			
			#Get SS/SSE/SSW
			ssLocation = self.getNextYLocation(-yDistance-1, location)
			sseLocation = self.getNextXLocation(-xDistance, ssLocation)
			sswLocation = self.getNextXLocation(xDistance, ssLocation)
			ssSite = gm.contents[ssLocation.y][ssLocation.x]
			sseSite = gm.contents[sseLocation.y][sseLocation.x]
			sswSite = gm.contents[sswLocation.y][sswLocation.x]
			
			#Get WW/WWN/WWS
			wwLocation = self.getNextXLocation(-xDistance-1, location)
			wwnLocation = self.getNextYLocation(-yDistance, wwLocation)
			wwsLocation = self.getNextYLocation(yDistance, wwLocation)
			wwSite = gm.contents[wwLocation.y][wwLocation.x]
			wwnSite = gm.contents[wwnLocation.y][wwnLocation.x]
			wwsSite = gm.contents[wwsLocation.y][wwsLocation.x]
			
			nBlocks = sum([(northSite.owner != self.myID and northSite.owner != 0) or (northSite.strength == 0 and northSite.owner == 0),
				(seastSite.owner != self.myID and seastSite.owner != 0) or (seastSite.strength == 0 and seastSite.owner == 0),
				(swestSite.owner != self.myID and swestSite.owner != 0) or (swestSite.strength == 0 and swestSite.owner == 0),
				(nnSite.owner != self.myID and nnSite.owner != 0) or (nnSite.strength == 0 and nnSite.owner == 0),
				(nneSite.owner != self.myID and nneSite.owner != 0) or (nneSite.strength == 0 and nneSite.owner == 0),
				(nnwSite.owner != self.myID and nnwSite.owner != 0) or (nnwSite.strength == 0 and nnwSite.owner == 0),])
		
			sBlocks = sum([(southSite.owner != self.myID and southSite.owner != 0) or (southSite.strength == 0 and southSite.owner == 0),
				(neastSite.owner != self.myID and neastSite.owner != 0) or (neastSite.strength == 0 and neastSite.owner == 0),
				(nwestSite.owner != self.myID and nwestSite.owner != 0) or (nwestSite.strength == 0 and nwestSite.owner == 0),
				(ssSite.owner != self.myID and ssSite.owner != 0) or (ssSite.strength == 0 and ssSite.owner == 0),
				(sseSite.owner != self.myID and sseSite.owner != 0) or (sseSite.strength == 0 and sseSite.owner == 0),
				(sswSite.owner != self.myID and sswSite.owner != 0) or (sswSite.strength == 0 and sswSite.owner == 0),])
				
			eBlocks = sum([(eastSite.owner != self.myID and eastSite.owner != 0) or (eastSite.strength == 0 and eastSite.owner == 0),
				(seastSite.owner != self.myID and seastSite.owner != 0) or (seastSite.strength == 0 and seastSite.owner == 0),
				(neastSite.owner != self.myID and neastSite.owner != 0) or (neastSite.strength == 0 and neastSite.owner == 0),
				(eeSite.owner != self.myID and eeSite.owner != 0) or (eeSite.strength == 0 and eeSite.owner == 0),
				(eenSite.owner != self.myID and eenSite.owner != 0) or (eenSite.strength == 0 and eenSite.owner == 0),
				(eewSite.owner != self.myID and eewSite.owner != 0) or (eewSite.strength == 0 and eewSite.owner == 0),])
				
			wBlocks = sum([(westSite.owner != self.myID and westSite.owner != 0) or (westSite.strength == 0 and westSite.owner == 0),
				(swestSite.owner != self.myID and swestSite.owner != 0) or (swestSite.strength == 0 and swestSite.owner == 0),
				(nwestSite.owner != self.myID and nwestSite.owner != 0) or (nwestSite.strength == 0 and nwestSite.owner == 0),
				(wwSite.owner != self.myID and wwSite.owner != 0) or (wwSite.strength == 0 and wwSite.owner == 0),
				(wwnSite.owner != self.myID and wwnSite.owner != 0) or (wwnSite.strength == 0 and wwnSite.owner == 0),
				(wwsSite.owner != self.myID and wwsSite.owner != 0) or (wwsSite.strength == 0 and wwsSite.owner == 0),])
		
		
			
			if (eBlocks >= wBlocks) and (eBlocks>= nBlocks) and (eBlocks >= sBlocks):
				return EAST
			elif (wBlocks >= sBlocks) and (wBlocks>= nBlocks) and (wBlocks >= eBlocks):
				return WEST
			elif (sBlocks >= nBlocks) and (sBlocks >= wBlocks) and (sBlocks >= eBlocks):
				return NORTH
			elif (nBlocks >= sBlocks) and (nBlocks >= wBlocks) and (nBlocks >= eBlocks):
				return SOUTH
		
			#logging.debug('ATTACK MODE')
			# if gm.getSite(neastLocation).owner != self.myID and gm.getSite(neastLocation).owner != 0 and gm.getSite(nwestLocation).owner != self.myID and gm.getSite(nwestLocation).owner != 0:
				#logging.debug('ATTACK MODE NORTH')
				# return NORTH
			# elif gm.getSite(seastLocation).owner != self.myID and gm.getSite(seastLocation).owner != 0 and gm.getSite(swestLocation).owner != self.myID and gm.getSite(swestLocation).owner != 0:
				#logging.debug('ATTACK MODE SOUTH')
				# return SOUTH
			# elif gm.getSite(neastLocation).owner != self.myID and gm.getSite(neastLocation).owner != 0 and gm.getSite(seastLocation).owner != self.myID and gm.getSite(seastLocation).owner != 0:
				#logging.debug('ATTACK MODE EAST')
				# return EAST
			# elif gm.getSite(swestLocation).owner != self.myID and gm.getSite(swestLocation).owner != 0 and gm.getSite(nwestLocation).owner != self.myID and gm.getSite(nwestLocation).owner != 0:
				#logging.debug('ATTACK MODE WEST')
				# return WEST
				
			# if (gm.getSite(eastLocation).owner != self.myID and gm.getSite(eastLocation).owner != 0) or (gm.getSite(eastLocation).strength == 0 and gm.getSite(eastLocation).owner == 0):
				#logging.debug('ATTACK EAST')
				# return EAST
			# elif (gm.getSite(westLocation).owner != self.myID and gm.getSite(westLocation).owner != 0) or (gm.getSite(westLocation).strength == 0 and gm.getSite(westLocation).owner == 0):
				#logging.debug('ATTACK WEST')
				# return WEST
			# elif (gm.getSite(northLocation).owner != self.myID and gm.getSite(northLocation).owner != 0) or (gm.getSite(northLocation).strength == 0 and gm.getSite(northLocation).owner == 0):
				#logging.debug('ATTACK SOUTH')
				# return SOUTH
			# elif (gm.getSite(southLocation).owner != self.myID and gm.getSite(southLocation).owner != 0) or (gm.getSite(southLocation).strength == 0 and gm.getSite(southLocation).owner == 0):
				#logging.debug('ATTACK NORTH')
				# return NORTH

				
		# if (gm.getSite(eastLocation).owner != self.myID and self.canTake(gameMap, location, gm.getSite(eastLocation))):
				# return EAST
		# elif (gm.getSite(westLocation).owner != self.myID and self.canTake(gameMap, location, gm.getSite(westLocation))):
				# return WEST
		# elif (gm.getSite(northLocation).owner != self.myID and self.canTake(gameMap, location, gm.getSite(northLocation))):
				# return SOUTH
		# elif (gm.getSite(southLocation).owner != self.myID and self.canTake(gameMap, location, gm.getSite(southLocation))):
				# return NORTH

		xDistance = 1
		yDistance = 1
		wFound = False
		eFound = False
		
		#if xMine and yMine:
		#	return STILL
		
		#logging.debug('Block at x: '+ str(x) +' y: ' + str(y))
		#if yMine == False:
			##while (xDistance < (self.gameMap.height)/2) and (xFound <4):
		while (xDistance < (self.gameMap.width)/2) and (wFound == False or eFound == False):
			#logging.debug('xDist: '+str(xDistance))
			#currentEastLocation = gm.getSite(self.getNextXLocation(xDistance, location))
			#currentWestLocation = gm.getSite(self.getNextXLocation(-xDistance, location))
			
			currentEL = self.getNextXLocation(xDistance, location)
			currentWL = self.getNextXLocation(-xDistance, location)
			currentEastLocation = gm.contents[currentEL.y][currentEL.x]
			currentWestLocation = gm.contents[currentWL.y][currentWL.x]
			
			if currentEastLocation.owner != self.myID:
				if eFound == False:
					eWeight=currentEastLocation.strength / float(currentEastLocation.production+1) + (xDistance-1)
					#logging.debug('eW: ' +str(eWeight)+' str: ' +str(currentEastLocation.strength)+ ' prod: ' + str(currentEastLocation.production))
					eFound = True
				xFound += 1
			if currentWestLocation.owner != self.myID:
				if wFound == False:
					wWeight=currentWestLocation.strength / float(currentWestLocation.production+1) + (xDistance-1)
					#logging.debug('wW: ' +str(wWeight)+' str: ' +str(currentWestLocation.strength)+ ' prod: ' + str(currentWestLocation.production))
					wFound = True
				xFound += 1
			xDistance += 1
					
		sFound = False
		nFound = False
		
		#if xMine==False:
			##while (yDistance < (self.gameMap.height)/2) and (yFound < 4):
		while (yDistance < (self.gameMap.height)/2) and (sFound == False or nFound == False):
			#logging.debug('yDist: '+str(yDistance))
			#currentNorthLocation = gm.getSite(self.getNextYLocation(yDistance, location))
			#currentSouthLocation = gm.getSite(self.getNextYLocation(-yDistance, location))
			currentNL = self.getNextYLocation(yDistance, location)
			currentSL = self.getNextYLocation(-yDistance, location)
			currentNorthLocation = gm.contents[currentNL.y][currentNL.x]
			currentSouthLocation = gm.contents[currentSL.y][currentSL.x]
			if currentNorthLocation.owner != self.myID:
				yDirection = SOUTH
				if sFound == False:
					sWeight=currentNorthLocation.strength / float(currentNorthLocation.production+1) + (yDistance-1)
					#logging.debug('sW: ' +str(sWeight)+' str: ' +str(currentNorthLocation.strength)+ ' prod: ' + str(currentNorthLocation.production))
					sFound = True
				yFound += 1
			if currentSouthLocation.owner != self.myID:
				yDirection = NORTH
				if nFound == False:
					nWeight=currentSouthLocation.strength / float(currentSouthLocation.production+1) + (yDistance-1)
					#logging.debug('nW: ' +str(nWeight)+' str: ' +str(currentSouthLocation.strength)+ ' prod: ' + str(currentSouthLocation.production))
					nFound = True
				yFound += 1
			yDistance += 1
		
		#if eWeight >= 255 or wWeight >= 255 or sWeight >= 255 or nWeight >= 255:
		#	 return STILL
		# if isinstance(eWeight, float) and isinstance(wWeight, float) and isinstance(sWeight, float) and isinstance(nWeight, float):
			# lol = 1
		# else:
			# return STILL
		# if sFound == False or nFound ==False or wFound == False or eFound ==False:
			# return STILL
		#logging.debug('eW: ' +str(eWeight)+' wW: ' +str(wWeight)+ ' nW: ' + str(nWeight) + ' sW: ' + str(sWeight))
		
		if (eWeight <= wWeight) and (eWeight<= sWeight) and (eWeight <= nWeight):
			if self.canTake(gameMap, location, gm.getSite(eastLocation)) == False and gm.getSite(eastLocation).owner != self.myID:
				return STILL
			#logging.debug('MOVE EAST')
			return EAST
		elif (wWeight <= nWeight) and (wWeight<= sWeight) and (wWeight <= eWeight):
			if self.canTake(gameMap, location, gm.getSite(westLocation)) == False and gm.getSite(westLocation).owner != self.myID:
				return STILL
			#logging.debug('MOVE WEST')
			return WEST
		elif (nWeight <= sWeight) and (nWeight <= wWeight) and (nWeight <= eWeight):
			if self.canTake(gameMap, location, gm.getSite(southLocation)) == False and gm.getSite(southLocation).owner != self.myID:
				return STILL
			#logging.debug('MOVE NORTH')
			return NORTH
		elif (sWeight <= nWeight) and (sWeight <= wWeight) and (sWeight <= eWeight):
			if self.canTake(gameMap, location, gm.getSite(northLocation)) == False and gm.getSite(northLocation).owner != self.myID:
				return STILL
			#logging.debug('MOVE SOUTH')
			return SOUTH
		return STILL
			
	def getDirections(self, gameMap):
		directions = []
		return directions

	

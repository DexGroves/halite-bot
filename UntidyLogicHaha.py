from __future__ import division
import numpy as np
from hlt import Move, WEST, EAST, NORTH, SOUTH, STILL, Location
import logging


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
		
		
		if sum([(gm.getSite(eastLocation).owner != self.myID and gm.getSite(eastLocation).owner != 0) or (gm.getSite(eastLocation).strength == 0 and gm.getSite(eastLocation).owner == 0),
			(gm.getSite(westLocation).owner != self.myID and gm.getSite(westLocation).owner != 0) or (gm.getSite(westLocation).strength == 0 and gm.getSite(westLocation).owner == 0),
			(gm.getSite(northLocation).owner != self.myID and gm.getSite(northLocation).owner != 0) or (gm.getSite(northLocation).strength == 0 and gm.getSite(northLocation).owner == 0),
			(gm.getSite(southLocation).owner != self.myID and gm.getSite(southLocation).owner != 0) or (gm.getSite(southLocation).strength == 0 and gm.getSite(southLocation).owner == 0)]) > 0:
		
			neastLocation = self.getNextXLocation(xDistance, self.getNextYLocation(-yDistance, location))
			nwestLocation = self.getNextXLocation(-xDistance, self.getNextYLocation(-yDistance, location))
			seastLocation = self.getNextXLocation(xDistance, self.getNextYLocation(yDistance, location))
			swestLocation = self.getNextXLocation(-xDistance, self.getNextYLocation(yDistance, location))
		
			##logging.debug('ATTACK MODE')
			if gm.getSite(neastLocation).owner != self.myID and gm.getSite(neastLocation).owner != 0 and gm.getSite(nwestLocation).owner != self.myID and gm.getSite(nwestLocation).owner != 0:
				##logging.debug('ATTACK MODE NORTH')
				return NORTH
			elif gm.getSite(seastLocation).owner != self.myID and gm.getSite(seastLocation).owner != 0 and gm.getSite(swestLocation).owner != self.myID and gm.getSite(swestLocation).owner != 0:
				##logging.debug('ATTACK MODE SOUTH')
				return SOUTH
			elif gm.getSite(neastLocation).owner != self.myID and gm.getSite(neastLocation).owner != 0 and gm.getSite(seastLocation).owner != self.myID and gm.getSite(seastLocation).owner != 0:
				##logging.debug('ATTACK MODE EAST')
				return EAST
			elif gm.getSite(swestLocation).owner != self.myID and gm.getSite(swestLocation).owner != 0 and gm.getSite(nwestLocation).owner != self.myID and gm.getSite(nwestLocation).owner != 0:
				##logging.debug('ATTACK MODE WEST')
				return WEST
				
			if (gm.getSite(eastLocation).owner != self.myID and gm.getSite(eastLocation).owner != 0) or (gm.getSite(eastLocation).strength == 0 and gm.getSite(eastLocation).owner == 0):
				#logging.debug('ATTACK EAST')
				return EAST
				#else:
				#	return STILL
			elif (gm.getSite(westLocation).owner != self.myID and gm.getSite(westLocation).owner != 0) or (gm.getSite(westLocation).strength == 0 and gm.getSite(westLocation).owner == 0):
				#logging.debug('ATTACK WEST')
				return WEST
				#else:
				#	return STILL
			elif (gm.getSite(northLocation).owner != self.myID and gm.getSite(northLocation).owner != 0) or (gm.getSite(northLocation).strength == 0 and gm.getSite(northLocation).owner == 0):
				#logging.debug('ATTACK SOUTH')
				return SOUTH
				#else:
				#	return STILL
			elif (gm.getSite(southLocation).owner != self.myID and gm.getSite(southLocation).owner != 0) or (gm.getSite(southLocation).strength == 0 and gm.getSite(southLocation).owner == 0):
				#logging.debug('ATTACK NORTH')
				return NORTH

				
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
			logging.debug('xDist: '+str(xDistance))
			currentEastLocation = gm.getSite(self.getNextXLocation(xDistance, location))
			currentWestLocation = gm.getSite(self.getNextXLocation(-xDistance, location))
			
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
			currentNorthLocation = gm.getSite(self.getNextYLocation(yDistance, location))
			currentSouthLocation = gm.getSite(self.getNextYLocation(-yDistance, location))
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

	

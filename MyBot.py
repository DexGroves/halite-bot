import json
from halitesrc.hlt import *
from halitesrc.networking import *
from dexbot.dexbot import DexBot


config = json.load(open("dexbot.config", "r"))


_, game_map = getInit()
sendInit("DexBot")

db = DexBot(game_map, config)


while True:
    game_map = getFrame()
    db.update(game_map)
    moves = db.move()
    sendFrame(moves)

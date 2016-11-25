import json
import timeit
from halitesrc.hlt import *
from halitesrc.networking import *
from refbot.dexbot import DexBot


config = json.load(open("refbot.config", "r"))

my_id, game_map = getInit()
db = DexBot(my_id, game_map, config)

sendInit("RefBot")
while True:
    start_time = timeit.default_timer()
    game_map = getFrame()
    db.update(game_map)
    moves = db.move(start_time)
    sendFrame(moves)

import json
import timeit
from halitesrc.hlt import *
from halitesrc.networking import *
from dexbot.dexbot import DexBot


config = json.load(open("dexbot.config", "r"))


_, game_map = getInit()
sendInit("DexBot")

db = DexBot(game_map, config)


with open('times.txt', 'w') as f:
    f.write("Times!\n")

while True:
    start_time = timeit.default_timer()
    game_map = getFrame()
    db.update(game_map)
    moves = db.move()
    sendFrame(moves)
    end_time = timeit.default_timer()

    with open('times.txt', 'a') as f:
        f.write(repr(end_time - start_time) + '\n')

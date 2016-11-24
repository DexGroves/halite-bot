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

end_time = timeit.default_timer()

while True:
    game_map = getFrame()
    start_time = timeit.default_timer()
    db.update(game_map)
    moves = db.move()

    with open('times.txt', 'a') as f:
        f.write(repr(start_time - end_time) + '\t')

    end_time = timeit.default_timer()
    sendFrame(moves)

    with open('times.txt', 'a') as f:
        f.write(repr(end_time - start_time) + '\n')

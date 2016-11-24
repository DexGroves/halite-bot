import json
import timeit
import numpy as np
from halitesrc.hlt import *
from halitesrc.networking import *
from ref.dexbot import DexBot
from ref.map_evaluator import MapEvaluator

config = json.load(open("refbot.config", "r"))


my_id, game_map = getInit()
sendInit("RefBot")
db = DexBot(my_id, config)
mapeval = MapEvaluator(my_id, game_map, config)

while True:
    start_time = timeit.default_timer()

    game_map = getFrame()
    mapeval.set_evaluation(game_map)
    db.set_evaluator(mapeval)

    self_pts = mapeval.get_self_pts()
    moves = np.empty(len(self_pts), dtype=Move)

    elapsed = 0
    i = 0
    np.random.shuffle(self_pts)

    for x, y in self_pts:
        location = Location(x, y)
        moves[i] = db.move(location, game_map)

        check_time = (x + y) % config['time_check_frequency'] == 0
        if check_time:
            elapsed = timeit.default_timer() - start_time
        if check_time and elapsed > config['max_time']:
            # Panic mode, everything stays!
            moves[i:] = [Move(Location(x, y), STILL) for x, y in self_pts[i:]]
            break
        i += 1

    sendFrame(moves)

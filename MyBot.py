from hlt import *
from networking import *
from dexbot.dexbot import DexBot
from dexbot.map_evaluator import MapEvaluator


my_id, game_map = getInit()
sendInit("DexBot")
db = DexBot(my_id)


while True:
    moves = []
    game_map = getFrame()
    mapeval = MapEvaluator(my_id)
    mapeval.set_evaluation(game_map)
    db.set_evaluator(mapeval)

    for y in range(game_map.height):
        for x in range(game_map.width):
            location = Location(x, y)
            owner = game_map.getSite(location).owner
            if owner == my_id:
                moves.append(db.move(location, game_map))
    sendFrame(moves)

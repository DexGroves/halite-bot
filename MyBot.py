import json
import timeit
import argparse
from halitesrc.hlt import *
from halitesrc.networking import *
from dexbot.dexbot import DexBot


parser = argparse.ArgumentParser(description='Dexbot!')
parser.add_argument('config', type=str, default="dexbot.config",
                    help='Config file location', nargs='?')
args = parser.parse_args()

config = json.load(open(args.config, "r"))

my_id, game_map = getInit()
db = DexBot(my_id, game_map, config)

sendInit(config['name'])
while True:
    start_time = timeit.default_timer()
    game_map = getFrame()
    db.update(game_map)
    moves = db.move(start_time)
    sendFrame(moves)

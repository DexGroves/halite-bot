import json
import timeit
import argparse
from halitesrc.hlt import *
from halitesrc.networking import *
from refbot.dexbot import DexBot
from refbot.get_config import get_config

parser = argparse.ArgumentParser(description='Dexbot!')
parser.add_argument('config', type=str, default="choose",
                    help='Config file location', nargs='?')
args = parser.parse_args()

my_id, game_map = getInit()

if args.config == "choose":
    config_filename = get_config(game_map)
else:
    config_filename = args.config

config = json.load(open(config_filename, "r"))
db = DexBot(my_id, game_map, config)

sendInit(config['name'])
while True:
    start_time = timeit.default_timer()
    game_map = getFrame()
    db.update(game_map)
    moves = db.move(start_time)
    sendFrame(moves)

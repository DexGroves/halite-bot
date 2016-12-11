import argparse
import json
from dexlib.bot_api import BotAPI
from dexlib.game_state import send_init, send_frame, get_init


parser = argparse.ArgumentParser(description='Dexbot!')
parser.add_argument('config', type=str, default="choose",
                    help='Config file location', nargs='?')
args = parser.parse_args()
if args.config == "choose":
    args.config = "configs/dexbot.config"

config = json.load(open(args.config, "r"))


my_id, map_state = get_init()
bot = BotAPI(map_state, config)

send_init("DexBot")


while True:
    map_state.get_frame()
    bot.update(map_state)
    moves = bot.get_moves(map_state)

    send_frame(moves)

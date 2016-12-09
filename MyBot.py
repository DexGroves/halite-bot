from dexlib.bot_api import BotAPI
from dexlib.game_state import send_init, send_frame, get_init


my_id, map_state = get_init()
bot = BotAPI()

send_init("DexBot")


while True:
    map_state.get_frame()
    bot.update(map_state)
    moves = bot.get_moves(map_state)

    send_frame(moves)

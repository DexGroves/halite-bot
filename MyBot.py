from dexlib.game_state import send_init, send_frame, get_init, Move
import random
import numpy as np


my_id, game_map = get_init()
send_init("DexBot")


while True:
    game_map.get_frame()
    game_map.update()
    moves = [Move(x, y, random.choice(range(5)))
             for (x, y) in np.transpose(np.where(game_map.owners == my_id))]
    send_frame(moves)

from nphlt import send_init, send_frame, get_init, Move
import random
import numpy as np


myID, game_map = get_init()
send_init("RandomPythonBot")


while True:
    game_map.get_frame()
    moves = [Move(x, y, random.choice(range(5)))
             for (x, y) in np.transpose(np.where(game_map.owners == myID))]
    send_frame(moves)

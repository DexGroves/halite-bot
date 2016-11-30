import numpy as np


def get_config(game_map):
    xdim = game_map.width
    ydim = game_map.height

    long_dim = max(xdim, ydim)
    owner = np.zeros((xdim, ydim), dtype=int)

    for x in range(xdim):
        for y in range(ydim):
            owner[x, y] = game_map.contents[y][x].owner

    nplayers = owner.max()

    if nplayers == 2:
        return "configs/dexbot.default.config"

    if nplayers == 3:
        return "configs/dexbot.threeway.config"

    if long_dim <= 21:
        return "configs/dexbot.multiway.config"

    return "configs/dexbot.default.config"

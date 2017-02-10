import numpy as np
from collections import deque


def dist_to(game_map, sources):
    dist = np.empty_like(game_map.owners)
    dist.fill(-1)

    for sx, sy in sources:
        dist[sx, sy] = 0

    ds = deque(sources)
    while len(ds) > 0:
        cx, cy = ds.popleft()
        c_dist = dist[cx, cy]
        for nx, ny in game_map.nbrs[cx, cy]:
            if dist[nx, ny] == -1 or dist[nx, ny] > (c_dist + 1):
                dist[nx, ny] = c_dist + 1
                ds.append((nx, ny))

    return dist


def friendly_to(game_map, sources):
    dist = np.empty_like(game_map.owners)
    dist.fill(-1)

    for sx, sy in sources:
        dist[sx, sy] = 0

    ds = deque(sources)
    while len(ds) > 0:
        cx, cy = ds.popleft()
        c_dist = dist[cx, cy]
        for nx, ny in game_map.nbrs[cx, cy]:
            if not game_map.owned[nx, ny]:
                continue

            if dist[nx, ny] == -1 or dist[nx, ny] > (c_dist + 1):
                dist[nx, ny] = c_dist + 1
                ds.append((nx, ny))

    return dist

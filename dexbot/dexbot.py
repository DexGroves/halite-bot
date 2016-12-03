"""Handle the control flow of DexBot."""


from dexbot.map_state import MapState
from dexbot.move_queue import MoveResolver
from dexbot.move_finder import MoveFinder
from dexbot.pathfinder import Pathfinder
import time



class DexBot(object):

    def __init__(self, my_id, game_map, config):
        self.ms = MapState(my_id, game_map, config)
        self.mf = MoveFinder(config)
        self.pathfinder = Pathfinder(self.ms)

        self.turn = 0

        with open("timing.txt", "w") as f:
            f.write("MSupdate\t\tMFupdateStrto\t\tMFupdateBrdr\t\tMove\n")

    def update(self, game_map):
        t0 = time.time()

        self.ms.update(game_map)
        t1 = time.time()
        self.mf.update(self.ms)

        with open("timing.txt", "a") as f:
            f.write(repr(t1-t0) + '\t')

    def move(self, start_time):
        t0 = time.time()

        owned_locs = self.ms.get_self_locs()
        mq = MoveResolver(owned_locs)

        for i, (x, y) in enumerate(mq.rem_locs):
            tx, ty = self.mf.find_move(x, y, self.ms)
            mq.pend_move(x, y, tx, ty)

        self.turn += 1

        mq.resolve_dirs(self.pathfinder, self.ms)
        mq.write_moves(self.ms)

        t1 = time.time()

        with open("timing.txt", "a") as f:
            f.write(repr(t1-t0) + '\n')

        return mq.moves

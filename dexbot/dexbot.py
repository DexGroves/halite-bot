"""Handle the control flow of DexBot."""


from dexbot.map_state import MapState
from dexbot.move_queue import MoveQueue
from dexbot.move_finder import MoveFinder
import time


class DexBot(object):

    def __init__(self, my_id, game_map, config):
        self.ms = MapState(my_id, game_map, config)
        self.mf = MoveFinder(config)
        self.turn = 0

        with open("timing.txt", "w") as f:
            f.write("MSupdate\t\tMFupdate\t\tMove\n")

        with open("moves.txt", "w") as f:
            f.write("\n")

    def update(self, game_map):
        t0 = time.time()

        self.ms.update(game_map)
        t1 = time.time()
        self.mf.update(self.ms)
        t2 = time.time()

        with open("timing.txt", "a") as f:
            f.write(repr(t1-t0) + '\t' + repr(t2-t1) + '\t')

    def move(self, start_time):
        t0 = time.time()

        owned_locs = self.ms.get_self_locs()
        mq = MoveQueue(owned_locs)

        for i, (x, y) in enumerate(mq.rem_locs):
            tx, ty = self.mf.find_move(x, y, self.ms)
            if self.ms.can_occupy_safely(x, y, tx, ty):
                d = self.ms.nxny_to_cardinal(x, y, tx, ty)
                mq.pend_move(x, y, d)
                with open("moves.txt", "a") as f:
                    f.write(repr(self.turn) + '\t' + repr((x, y)) + '\t' + repr(d) + '\t' + repr((tx, ty)) + "\n")

            else:
                mq.pend_move(x, y, 0)
                with open("moves.txt", "a") as f:
                    f.write(repr(self.turn) + '\t' + repr((x, y)) + '\t' + repr('stay') + "\n")

        self.turn += 1

        t1 = time.time()

        with open("timing.txt", "a") as f:
            f.write(repr(t1-t0) + '\n')

        return mq.moves

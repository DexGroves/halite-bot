"""Handle the control flow of DexBot."""


import timeit
from halitesrc.hlt import Move, Location
from refbot.map_state import MapState
from refbot.appraiser import Appraiser
from refbot.border_operator import BorderOperator
from refbot.move_queue import MoveQueue
from refbot.pathfinder import Pathfinder


class DexBot(object):

    def __init__(self, my_id, game_map, config):
        self.map_state = MapState(my_id, game_map)
        self.appraiser = Appraiser(self.map_state, config)
        self.pathfinder = Pathfinder(self.map_state)
        self.border_operator = BorderOperator(self.map_state, config)
        self.time_chk_freq = 20
        self.max_time = 0.95
        self.turn = 0

    def update(self, game_map):
        self.map_state.update(game_map)
        self.appraiser.set_value(self.map_state)
        self.border_operator.set_border_value(self.map_state, self.appraiser)

    def move(self, start_time):
        owned_locs = self.map_state.get_self_locs()
        mq = MoveQueue(owned_locs)

        ic_q, t1_q, t2_q = self.border_operator.get_moves(self.map_state)

        mq.process_pending(ic_q)
        mq.process_pending(t1_q)
        mq.process_pending(t2_q)

        # mq.shuffle_remaining_locs()
        mq.order_locs_by_strength(self.appraiser)

        for i, (x, y) in enumerate(mq.rem_locs):
            # Handle timeout
            check_time = i % self.time_chk_freq == 1

            if check_time:
                elapsed = timeit.default_timer() - start_time
            if check_time and elapsed > self.max_time:
                # Panic mode, everything stays!
                mq.moves[mq.nmoved:] = [Move(Location(x, y), 0) for (x, y) in mq.rem_locs[i:]]
                break

            (nx, ny), move_value = self.appraiser.get_best_target(self.map_state, x, y)
            stay_value = self.appraiser.get_stay_value(x, y)

            if stay_value > move_value:
                mq.pend_move(x, y, 0)

            else:
                direction = self.pathfinder.find_path(x, y, nx, ny, self.map_state)
                mq.pend_move(x, y, direction)

        self.turn += 1
        return mq.moves

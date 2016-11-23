"""Handle the control flow of DexBot."""


from dexbot.map_state import MapState
from dexbot.appraiser import Appraiser
from dexbot.border_operator import BorderOperator
from dexbot.move_queue import MoveQueue
from dexbot.pathfinder import Pathfinder


class DexBot(object):

    def __init__(self, game_map, config):
        self.map_state = MapState(game_map)
        self.appraiser = Appraiser(self.map_state, config)
        self.pathfinder = Pathfinder(self.map_state)
        self.border_operator = BorderOperator(self.map_state)
        self.turn = 0
        with open('pending.txt', 'w') as f:
            f.write('Start! ------- ' + '\n')
        with open('map.txt', 'w') as f:
            f.write('Start! ------- ' + '\n')

    def update(self, game_map):
        self.map_state.update(game_map)
        self.appraiser.set_value(self.map_state)
        self.border_operator.set_border_value(self.map_state, self.appraiser)

    def move(self):
        with open('pending.txt', 'a') as f:
            f.write('Turn! %i ------- ' % self.turn + '\n')
            # f.write(repr(self.map_state.get_self_locs()) + '\n')
            # f.write(repr(self.map_state.get_border_locs()) + '\n')
            self.turn += 1
        with open('map.txt', 'a') as f:
            f.write('Turn %i' % self.turn + '\n')
            f.write(repr(self.map_state.mine_strn)+ '\n')

        owned_locs = self.map_state.get_self_locs()
        mq = MoveQueue(owned_locs)

        ic_queue, bm_queue = self.border_operator.get_moves(self.map_state)

        mq.process_pending(ic_queue)
        mq.process_pending(bm_queue)

        mq.shuffle_remaining_locs()

        for x, y in mq.rem_locs:
            (nx, ny), move_value = self.appraiser.get_best_target(self.map_state, x, y)
            stay_value = self.appraiser.get_stay_value(x, y)

            if stay_value > move_value:
                mq.pend_move(x, y, 0)
                with open('pending.txt', 'a') as f:
                   f.write('Staying:\t' + repr((x, y)) + '\t' + repr(0) + '\n')

            else:
                direction = self.pathfinder.find_path(x, y, nx, ny)
                if self.map_state.can_move_safely(x, y, direction):
                    mq.pend_move(x, y, direction)
                    with open('pending.txt', 'a') as f:
                       f.write('Moving:\t' + repr((x, y)) + '\t' + repr(direction) + '\t' +
                               repr(stay_value) + '\t' + repr(move_value) + '\n')
                else:
                    mq.pend_move(x, y, 0)
                    with open('pending.txt', 'a') as f:
                        f.write('Staying:\t' + repr((x, y)) + '\t' + repr(0) + '\n')

        # with open('pending.txt', 'a') as f:
        #     locs = [move.loc for move in mq.moves]
        #     dirs = [move.direction for move in mq.moves]

        #     moves_list = [repr((locs[i].x, ' ', locs[i].y, ' ', dirs[i]))
        #                   for i in range(len(locs))]

        #     f.write('Moves ---- :\n' + '\n'.join(moves_list) + '\n')
        return mq.moves


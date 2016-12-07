from dexbot.evaluator import Evaluator
from dexbot.map_state import MapState
from dexbot.move_queue import MoveResolver
from dexbot.pathfinder import Pathfinder
from dexbot.mcts import MCTSApi


class DexBot(object):
    """Handle the control flow of DexBot."""
    def __init__(self, my_id, game_map, config):
        self.ms = MapState(my_id, game_map, config)
        self.evaluator = Evaluator(config, self.ms)
        self.pathfinder = Pathfinder(self.ms)
        self.mcts = MCTSApi(self.ms)
        self.mcts.think(15)
        self.mcts.set_depth(7)

        self.turn = 1
        # print("turn\tx\ty\tnx\tny", file=open('moves.txt', 'w'))

    def update(self, game_map):
        self.ms.update(game_map)
        # self.evaluator.update(self.ms)
        # self.mcts.update(self.ms, self.turn)
        # mcts.think(1)
        self.mcts.set_target_matrix(self.ms)

    def move(self):
        mq = MoveResolver(self.ms.get_self_locs())
        # tx, ty = self.mcts.get_target(self.ms)
        for x, y in mq.rem_locs:
            if self.ms.strn[x, y] > self.ms.prod[x, y] * 5:
                tx, ty = self.mcts.get_best_target(x, y, self.ms)
                mq.pend_move(x, y, tx, ty)
            else:
                mq.pend_move(x, y, x, y)

        # for i, (x, y) in enumerate(mq.rem_locs):
        #     tx, ty = self.evaluator.get_move(x, y, self.ms)
        #     mq.pend_move(x, y, tx, ty)

        # print('\t'.join([str(self.turn), str(x), str(y), str(tx), str(ty)]),
        #       file=open('moves.txt', 'a'))

        self.turn += 1
        mq.resolve_dirs(self.pathfinder, self.ms)
        mq.write_moves(self.ms)

        return mq.moves

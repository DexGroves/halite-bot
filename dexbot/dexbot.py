from dexbot.evaluator import Evaluator
from dexbot.map_state import MapState
from dexbot.move_queue import MoveResolver
from dexbot.pathfinder import Pathfinder


class DexBot(object):
    """Handle the control flow of DexBot."""
    def __init__(self, my_id, game_map, config):
        self.ms = MapState(my_id, game_map, config)
        self.evaluator = Evaluator(config, self.ms)
        self.pathfinder = Pathfinder(self.ms)

        self.turn = 0

    def update(self, game_map):
        self.ms.update(game_map)
        self.evaluator.update(self.ms)

    def move(self):
        mq = MoveResolver(self.ms.get_self_locs())

        for i, (x, y) in enumerate(mq.rem_locs):
            tx, ty = self.evaluator.get_move(x, y, self.ms)
            mq.pend_move(x, y, tx, ty)
        self.turn += 1

        mq.resolve_dirs(self.pathfinder, self.ms)
        mq.write_moves(self.ms)

        return mq.moves

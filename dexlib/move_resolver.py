import operator
from dexlib.game_state import Move


class MoveResolver:
    """Stop people from bumping into each other while moving.
    Avoid the cap, have a good formation, etc etc.
    """

    def __init__(self):
        self.moves = {}

    def add_move(self, qmove):
        if qmove.priority in self.moves.keys():
            self.moves[qmove.priority].append(qmove)
        else:
            self.moves[qmove.priority] = [qmove]

    def process_moves(self, ms, pf):
        output_moves = []

        priorities = sorted(self.moves.keys())
        for priority in priorities:
            self.moves[priority].sort(key=operator.attrgetter('score'))

            for move in self.moves[priority]:
                cardinal = pf.find_pref_cardinal(move.x, move.y,
                                                 move.tx, move.ty, ms)

                output_moves.append(Move(move.x, move.y, cardinal))

        return output_moves

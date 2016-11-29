"""Handle changes to behaviour as a function of combat."""


import numpy as np
from dexbot.move_queue import PendingMoves


class CombatOperator(object):

    def __init__(self, map_state):
        self.width = map_state.width
        self.height = map_state.height

    def get_moves(self, map_state):
        pm = PendingMoves()
        cmb_locs = map_state.get_combat_locs()

        for cx, cy in cmb_locs:
            # dmg_in = np.zeros(4, dtype=int)
            # dmg_out = np.zeros(4, dtype=int)
            val_mv = np.zeros(4, dtype=int)

            nbrs = map_state.get_neighbours(cx, cy)
            for i, (nx, ny) in enumerate(nbrs):
                if map_state.blank[nx, ny] and map_state.strn[nx, ny] > 20:
                    val_mv[i] = 0
                    continue
                # This is technically wrong. Enemies will generally head
                # towards this piece from one direction only!
                dmg_out = map_state.enemy_2brd[nx, ny]

                dmg_in = 0# np.minimum(map_state.strn[cx, cy],
                         #           map_state.enemy_2brd[nx, ny])
                val_mv[i] = dmg_out - dmg_in

            # idk what to do, I'm too powerful for the scrubs.
            if val_mv.max() == 0:
                continue  # Make what move I was gonna make anywayyy
                # Stops me going backwards until I have enough mental energy
                # to think of something more effective.
                # pm.pend_move(cx, cy, 0)
                # map_state.register_move(cx, cy, 0)
            else:
                direction = np.argmax(val_mv) + 1
                pm.pend_move(cx, cy, direction)
                map_state.register_move(cx, cy, direction)

        return pm

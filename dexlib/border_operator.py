import numpy as np
from dexlib.move_finder import QMove
import logging
logging.basicConfig(filename='bo.info', filemode="w", level=logging.DEBUG)


EmptyMove = QMove(None, None, None, None, 1000, 1000)


class BorderOperator:
    """Overwrite moves that can be improved by clutch teamup mechanics."""

    def __init__(self):
        pass

    def improve_moves(self, mr, ms, mf):
        for bx, by in ms.border_locs:
            self.improve_move(bx, by, mr, ms, mf)

    def improve_move(self, bx, by, mr, ms, mf):
        if ms.combat[bx, by]:
            return

        broi = ms.strn[bx, by] / ms.prod[bx, by]

        # If this isn't ultrapremium, skip it
        if broi > mf.roi_limit * 2:
            return

        bstrn = ms.strn[bx, by]
        immediate_nbrs = [n for n in ms.nbrs[bx, by] if ms.owned[n[0], n[1]]]

        str_deficit = [(bstrn - ms.strn[nx, ny]) for (nx, ny) in immediate_nbrs]
        ttc = [str_deficit[i] / ms.prod[nx, ny]
               for (i, (nx, ny)) in enumerate(immediate_nbrs)]

        # If I'm getting it soon anyway, skip it
        if min(ttc) < 2:
            return

        if len(immediate_nbrs) > 1:
            # I can do some immediate capture mechanics maybe
            strs = np.array([ms.strn[nx, ny] for (nx, ny) in immediate_nbrs])
            highest_i = np.argpartition(strs, -2)[-2:]
            if strs[highest_i].sum() > bstrn:
                # Just do it. Should probably check if it helps but f it
                for i in highest_i:
                    nx, ny = immediate_nbrs[i]
                    cur_move_key, cur_move_loc = mr.map_[(nx, ny)]

                    mr.moves[cur_move_key][cur_move_loc] = EmptyMove
                    mr.add_move(QMove(nx, ny, bx, by, -2, 1 / broi))

                logging.debug((ms.turn, 'immediate', bx, by))

                return

        for ix, iy in immediate_nbrs:
            istrn = ms.strn[ix, iy]
            helpers = [h for h in ms.nbrs[ix, iy] if ms.owned[h[0], h[1]]]

            for hx, hy in helpers:
                hstrn = ms.strn[hx, hy]
                if (hstrn + istrn) < bstrn:
                    continue
                # I'm just going to check if the helper is low priority,
                # then assume it's good and grab it
                h_move_key, h_move_loc = mr.map_[(hx, hy)]
                if mr.moves[h_move_key][h_move_loc].priority == 100:
                    i_move_key, i_move_loc = mr.map_[(ix, iy)]
                    mr.moves[h_move_key][h_move_loc] = EmptyMove
                    mr.moves[i_move_key][i_move_loc] = EmptyMove
                    mr.add_move(QMove(hx, hy, ix, iy, -1, 1 / broi))
                    mr.add_move(QMove(ix, iy, ix, iy, 100, 1 / broi))

                    logging.debug((ms.turn, 'delayed', bx, by))

                    return

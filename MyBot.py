import numpy as np
import dexlib.nphlt as hlt
import logging


logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class BorderEvaluator:
    """Evaluate the value of border squares and coordinate moves.
    Values are taken for each x, y, s, where s is the degree to which
    to hunt for teamups.
    """
    def __init__(self, maxd):
        self.maxd = maxd

    def update(self, gm):
        # Masking like this isn't _quite_ right
        self.motile = (gm.strnc >= gm.prodc * 5)
        strn_avail = gm.ostrn * self.motile

        t2r = gm.strnc / gm.prodc    # Can relax this later
        cell_value = gm.prod.copy()  # Can improve this later

        Bs = [(x, y, s) for (x, y) in gm.ubrdr_locs
              for s in range(1, self.maxd)]
        Cs = gm.owned_locs
        loc_to_Cs = {(x, y): i for i, (x, y) in enumerate(Cs)}

        m_assign = np.zeros((len(Bs), len(Cs)), dtype=bool)
        m_values = np.zeros(len(Bs), dtype=float)

        # Calculate move values and assignments
        for i, (bx, by, s) in enumerate(Bs):
            assign_idx = np.where(gm.dists[bx, by] <= s * gm.owned)
            nbr_strn = strn_avail[assign_idx].sum()
            nbr_prod = gm.oprod[assign_idx].sum()

            bstrn = gm.strn[bx, by]

            t2c = max(s, (bstrn - nbr_strn) / nbr_prod)

            m_values[i] = cell_value[bx, by] / (t2r[bx, by] + t2c)

            assign_locs = np.transpose(assign_idx)
            assign_is = np.fromiter((loc_to_Cs[x, y] for (x, y) in assign_locs),
                                    dtype=int)
            m_assign[i, assign_is] = True

        m_values *= -1  # Too lazy to worry about reverse iterating
        m_sorter = np.argsort(m_values)

        moveset = []
        for mi in m_sorter:
            if m_values[mi] == 0:
                continue
            else:
                sel_cs = m_assign[mi]
                logging.debug(m_assign)
                logging.debug(m_values)
                logging.debug(sel_cs)
                logging.debug((m_assign[:, sel_cs]))
                logging.debug((m_assign[:, sel_cs].shape))
                logging.debug((m_assign[:, sel_cs].max(axis=1)))
                logging.debug(np.nonzero(m_assign[:, sel_cs].max(axis=1).flatten()))
                # Can do better than a   max here!
                m_values[np.nonzero(m_assign[:, sel_cs].max(axis=1).flatten())] = 0

                moveset.append((Bs[mi], m_assign[mi]))

        self.moves = {}
        for (mx, my, s), assignment in moveset:
            for ax, ay in [Cs[i[0]] for i in np.nonzero(assignment)]:
                if self.motile[ax, ay]:
                    self.moves[(ax, ay)] = (mx, my)

    def dump_moves(self, gm):
        moves = []
        for (ax, ay), (mx, my) in self.moves.items():
            dir_ = gm.path_towards(ax, ay, mx, my)
            moves.append(hlt.Move(ax, ay, dir_))
        return moves


game_map = hlt.ImprovedGameMap()
bord_eval = BorderEvaluator(5)

hlt.send_init("DexBotNeuer")


while True:
    game_map.get_frame()
    game_map.update()
    bord_eval.update(game_map)
    hlt.send_frame(bord_eval.dump_moves(game_map))

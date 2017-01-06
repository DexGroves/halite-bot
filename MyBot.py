import numpy as np
import dexlib.nphlt as hlt
import logging
from dexlib.find_path import find_path


logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class MoveMaker:
    """Evaluate the value of border squares and coordinate moves.
    Values are taken for each x, y, s, where s is the degree to which
    to hunt for teamups.
    """
    def __init__(self, gm, maxd, glob_k):
        self.maxd = maxd
        self.glob_k = glob_k
        self.bulk_mvmt_off = 10
        self.brdr_mvmt_off = 10
        self.set_global_value(gm)

    def update(self, gm):
        # Masking like this isn't _quite_ right
        motile = ((gm.strnc >= gm.prodc * 5) * gm.owned).astype(bool)
        strn_avail = gm.ostrn * motile

        # t2r = gm.strnc / gm.prodc    # Can relax this later
        # cell_value = gm.prod.copy()  # Can improve this later
        cell_value = self.get_cell_value(gm)

        Bs = [(x, y, s) for (x, y) in gm.ubrdr_locs
              for s in range(1, self.maxd)]
        Cs = gm.owned_locs
        loc_to_Cs = {(x, y): i for i, (x, y) in enumerate(Cs)}

        m_support = np.zeros((len(Bs), len(Cs)), dtype=bool)
        m_values = np.zeros(len(Bs), dtype=float)

        moved = np.zeros_like(gm.prod, dtype=bool)
        assigned = np.zeros_like(gm.prod, dtype=bool)

        # Calculate move values and assignments
        for i, (bx, by, s) in enumerate(Bs):
            assign_idx = np.where(gm.dists[bx, by] <= s * gm.owned)
            nbr_strn = strn_avail[assign_idx].sum()
            nbr_prod = gm.oprod[assign_idx].sum()

            bstrn = gm.strn[bx, by]

            t2c = max(s, (bstrn - nbr_strn) / nbr_prod)

            # m_values[i] = cell_value[bx, by] / (t2r[bx, by] + t2c)
            m_values[i] = cell_value[bx, by] / (t2c + self.brdr_mvmt_off)

            assign_locs = np.transpose(assign_idx)
            assign_is = np.fromiter((loc_to_Cs[x, y] for (x, y) in assign_locs),
                                    dtype=int)
            m_support[i, assign_is] = True

        m_values *= -1  # Too lazy to worry about reverse iterating
        m_sorter = np.argsort(m_values)

        logging.debug('TURN ------------' + str(gm.turn))
        moveset = []
        # for mi in m_sorter:
        #     logging.debug((m_values[mi], Bs[mi]))

        for mi in m_sorter:
            bx, by, _ = Bs[mi]
            if assigned[bx, by] or m_values[mi] == 0:
                continue
            else:
                # Can do better than a max here!
                sel_cs = m_support[mi]
                m_values[np.nonzero(m_support[:, sel_cs].max(axis=1).flatten())] = 0
                moveset.append((Bs[mi], m_support[mi]))
                assigned[bx, by] = True

        self.moves = {}
        for (mx, my, s), assignment in moveset:
            for ax, ay in Cs[assignment]:
                moved[ax, ay] = True
                if motile[ax, ay] and s == gm.dists[ax, ay, mx, my]:
                    self.moves[(ax, ay)] = (mx, my)
                    # logging.debug((motile[ax, ay], gm.strnc[ax, ay], gm.prodc[ax, ay]))
                    # logging.debug(('brdr', (mx, my, s), (ax, ay)))

        # Get bulk moves now
        # to_move = np.maximum(0, motile - moved)
        to_move = motile.copy()
        to_move[np.nonzero(moved)] = False
        to_move_locs = np.transpose(np.nonzero(to_move))
        for ax, ay in to_move_locs:
            # Whatever
            prox_value = np.divide(cell_value * gm.ubrdr, gm.dists[ax, ay] + self.bulk_mvmt_off)
            tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)
            self.moves[(ax, ay)] = tx, ty
            # logging.debug((motile[ax, ay], gm.strnc[ax, ay], gm.prodc[ax, ay]))
            # logging.debug(('klub', (tx, ty, gm.dists[tx, ty, ax, ay]), (ax, ay)))

    def dump_moves(self, gm):
        # Need to force corner moves, don't forget
        moves = []
        for (ax, ay), (mx, my) in self.moves.items():
            dir_ = find_path(ax, ay, mx, my, gm)
            moves.append(hlt.Move(ax, ay, dir_))
        return moves

    def set_global_value(self, gm):
        pass
        # self.global_value = np.zeros_like(gm.prod, dtype=float)
        # for x in range(gm.width):
        #     for y in range(gm.height):
        #         self.global_value[x, y] = np.divide(gm.prodc, gm.str_to[x, y]).sum()

        # for i in range(3):
        #     self.global_value = gm.plus_filter(self.global_value, max)

        # np.savetxt("globval.txt", self.global_value)
        # np.savetxt("strn.txt", gm.strn)

    def get_cell_value(self, gm):
        # Sig_prod = (gm.prod * gm.owned).sum()
        # cell_value = np.divide(gm.prodc ** 2, gm.strnc) + \
        #    self.glob_k * self.global_value * gm.node_impt
        # cell_value = self.global_value * gm.node_impt
        local_value = np.divide(gm.prodc ** 2, gm.strnc) * gm.ubrdr
        global_value = gm.Mbval

        return local_value + global_value


game_map = hlt.ImprovedGameMap()
hlt.send_init("DexBotNeuer")
game_map.get_frame()
game_map.update()

bord_eval = MoveMaker(game_map, 10, 0.1)


while True:
    game_map.update()
    bord_eval.update(game_map)
    hlt.send_frame(bord_eval.dump_moves(game_map))
    game_map.get_frame()

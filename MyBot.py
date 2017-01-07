import numpy as np
import dexlib.nphlt as hlt
import logging
from scipy.ndimage import maximum_filter
from scipy.ndimage.filters import gaussian_filter
from dexlib.resolver import Resolver

logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class Combatant:
    """Handle all the moves for combat zones."""

    def __init__(self, com_radius=8):
        self.com_radius = com_radius
        self.combat_wait = 4

    def decide_combat_moves(self, gm):
        self.moves = {}
        self.moved = np.zeros_like(gm.owned)

        # Actually, I need a diamond filter!
        # close_Cs = maximum_filter(gm.ubrdr_combat, size=self.com_radius) * gm.owned
        # close_Cs -= com_Cs
        # Lazymode
        close_Cs = gm.com_mat.copy()
        for i in range(self.com_radius):
            close_Cs = np.maximum(close_Cs, gm.plus_filter(close_Cs, max))
        close_Cs -= gm.com_mat
        close_Cs *= gm.owned

        self.decide_melee_moves(gm, np.transpose(np.nonzero(gm.com_mat)))
        self.decide_close_moves(gm, np.transpose(np.nonzero(close_Cs)), gm.com_mat)

        return self.moved

    def decide_melee_moves(self, gm, locs):
        for cx, cy in locs:
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            nbrs = gm.nbrs[(cx, cy)]
            scores = [gm.combat_heur[nx, ny] for (nx, ny) in nbrs]

            self.moves[(cx, cy)] = nbrs[np.argmax(scores)]
            self.moved[cx, cy] = True

            nx, ny = nbrs[np.argmax(scores)]
            # logging.debug(((cx, cy), 'Melee!', scores, (nx, ny),
            # gm.strn[nx, ny], gm.prod[nx, ny], gm.enemy[nx, ny], gm.blank[nx, ny]))

    def decide_close_moves(self, gm, locs, com_Cs):
        for cx, cy in locs:
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            dmat = np.divide(com_Cs, gm.dists[cx, cy])
            tx, ty = np.unravel_index(dmat.argmax(), dmat.shape)

            self.moves[(cx, cy)] = tx, ty
            self.moved[cx, cy] = True
            # logging.debug(((cx, cy), 'Moving to combat!', (tx, ty)))

    def dump_moves(self, gm):
        # Can replace some of this with explicit directions
        return self.moves


class MoveMaker:
    """Evaluate the value of border squares and coordinate moves.
    Values are taken for each x, y, s, where s is the degree to which
    to hunt for teamups.
    """
    def __init__(self, gm, maxd, glob_k):
        self.maxd = maxd
        self.glob_k = glob_k
        self.bulk_mvmt_off = 10
        self.glob_invest_cap = 1.8
        self.bval_cutoff = 0.3

        # print("globalmax", "localmax", file=open("values.txt", "w"))

    def decide_noncombat_moves(self, gm, moved):
        self.moves = {}

        motile = ((gm.strnc >= gm.prodc * 4) * gm.owned).astype(bool)
        motile[np.nonzero(gm.gte_nbr)] = True
        motile[np.nonzero(moved)] = False
        strn_avail = gm.ostrn * motile

        Vloc, Vmid, Vglob = self.get_cell_value(gm)
        Vtot = Vloc + Vmid + Vglob

        high_val_brdrs = np.transpose(np.where(Vloc > (Vtot * self.bval_cutoff)))
        hvb_value = [Vtot[hx, hy] for hx, hy in high_val_brdrs]

        # High value borders grab the strongest neighbour
        # for i in np.argsort(hvb_value[::-1]):
        #     hx, hy = high_val_brdrs[i]
        #     nbrs = [(nx, ny) for (nx, ny) in gm.nbrs[hx, hy]
        #             if gm.owned[nx, ny] and motile[nx, ny] and not moved[nx, ny]]

        #     if len(nbrs) == 0:
        #         continue

        #     nbr_strns = np.array([gm.strn[nx, ny] for (nx, ny) in nbrs])
        #     best_nbr_i = nbr_strns.argmax()
        #     nx, ny = nbrs[best_nbr_i]

        #     self.moves[(nx, ny)] = (hx, hy)
        #     moved[nx, ny] = True

        # Now the bulk moves happen
        to_move = motile.copy()
        to_move[np.nonzero(moved)] = False
        to_move_locs = np.transpose(np.nonzero(to_move))
        for ax, ay in to_move_locs:
            prox_value = np.divide(Vmid, (gm.dists[ax, ay])) + \
                np.divide(Vglob, (gm.dists[ax, ay] + self.bulk_mvmt_off))
            tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)
            self.moves[(ax, ay)] = tx, ty

        # print(Vglob.max(), Vmid.max(), file=open("values.txt", "a"))

    def dump_moves(self, gm):
        # Need to force corner moves, don't forget
        return self.moves

    def get_cell_value(self, gm):
        # local_value = gm.prodc * gm.ubrdr
        # Should set this to ignore my strn and prod
        mid_value = gaussian_filter(
            (gm.prodc ** 2 / gm.original_strn), 3, mode='wrap'
        ) * gm.ubrdr
        local_value = np.maximum(mid_value, (gm.prodc ** 2 / gm.strnc)) * gm.ubrdr
        global_value = gm.Mbval

        return local_value, mid_value, global_value * self.glob_k


game_map = hlt.ImprovedGameMap()
hlt.send_init("DexBotNeuer")
game_map.get_frame()
game_map.update()


bord_eval = MoveMaker(game_map, 10, 4)
combatant = Combatant(10)
resolver = Resolver(game_map)


while True:
    logging.debug('TURN ------------' + str(game_map.turn))
    game_map.update()

    moved = combatant.decide_combat_moves(game_map)
    bord_eval.decide_noncombat_moves(game_map, moved)

    comb_moves = combatant.dump_moves(game_map)
    bord_moves = bord_eval.dump_moves(game_map)
    resolved_moves = resolver.resolve({**comb_moves, **bord_moves}, game_map)

    hlt.send_frame(resolved_moves)
    game_map.get_frame()

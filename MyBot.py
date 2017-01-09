import numpy as np
import dexlib.nphlt as hlt
import logging
from scipy.ndimage import maximum_filter
from scipy.ndimage.filters import gaussian_filter
from dexlib.resolver import Resolver

logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


class Combatant:
    """Handle all the moves for combat zones."""

    def __init__(self, combat_wait):
        self.combat_wait = combat_wait

    def decide_combat_moves(self, gm):
        self.moves = {}
        self.moved = np.zeros_like(gm.owned)

        self.decide_melee_moves(gm)
        self.decide_close_moves(gm)

        return self.moved

    def decide_melee_moves(self, gm):
        locs = np.transpose(np.nonzero(gm.melee_mat))
        for cx, cy in locs:
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            if (cx + cy + gm.turn % 2) != gm.parity:
                self.moves[cx, cy] = cx, cy
                self.moved[cx, cy] = True

            nbrs = gm.nbrs[(cx, cy)]
            scores = [gm.combat_heur[nx, ny] for (nx, ny) in nbrs]

            self.moves[(cx, cy)] = nbrs[np.argmax(scores)]
            self.moved[cx, cy] = True

            nx, ny = nbrs[np.argmax(scores)]
            # logging.debug(((cx, cy), 'Melee!', scores, (nx, ny),
            # gm.strn[nx, ny], gm.prod[nx, ny], gm.enemy[nx, ny], gm.blank[nx, ny]))

    def decide_close_moves(self, gm):
        locs = np.transpose(np.nonzero(gm.close_to_combat))
        for cx, cy in locs:
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            if (cx + cy + gm.turn % 2) != gm.parity:
                self.moves[cx, cy] = cx, cy
                self.moved[cx, cy] = True

            dmat = np.divide(gm.melee_mat, gm.dists[cx, cy])
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

        self.desired_d1_moves = {}
        d1_conquered = np.ones_like(Vtot, dtype=bool)

        to_move = motile.copy()
        to_move[np.nonzero(moved)] = False
        to_move_locs = np.transpose(np.nonzero(to_move))
        for ax, ay in to_move_locs:
            prox_value = np.divide(Vmid, (gm.dists[ax, ay])) + \
                np.divide(Vglob, (gm.dists[ax, ay] + self.bulk_mvmt_off))
            prox_value *= d1_conquered
            tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)
            self.moves[(ax, ay)] = tx, ty

            # Add to a postprocessing queue for later
            if gm.dists[ax, ay, tx, ty] == 1:
                self.desired_d1_moves.setdefault((tx, ty), []).append((ax, ay))
                if gm.strn[ax, ay] > gm.strn[tx, ty]:
                    # No one else can erroneously target this cell
                    d1_conquered[tx, ty] = 0

        self.process_d1_teamups(gm)

    def dump_moves(self, gm):
        # Need to force corner moves, don't forget
        return self.moves

    def get_cell_value(self, gm):
        # local_value = gm.prodc * gm.ubrdr
        # Should set this to ignore my strn and prod
        mid_value = gaussian_filter(
            (gm.prodc ** 2 / gm.original_strn), 1, mode='wrap'
        ) * gm.ubrdr
        local_value = np.maximum(mid_value, (gm.prodc ** 2 / gm.strnc)) * gm.ubrdr
        global_value = gm.Mbval

        return local_value, mid_value, global_value * self.glob_k

    def process_d1_teamups(self, gm):
        """This is megagrizzle hacks. If two pieces want to occupy
        the same cell 1-distance away, that is too strong for either
        of them, set the gm.strn variable to 0 so that the
        pathfinder is tricked into allowing the moves.
        """
        for (tx, ty), locs in self.desired_d1_moves.items():
            if len(locs) < 2:
                continue
            else:
                total_strn = np.array([
                    gm.strn[ax, ay] for ax, ay in locs
                ])
                if total_strn.sum() > gm.strn[tx, ty] and \
                        total_strn.max() <= gm.strn[tx, ty]:
                    gm.strn[tx, ty] = 0


game_map = hlt.ImprovedGameMap(8)
hlt.send_init("DexBotNeuer")
game_map.get_frame()
game_map.update()


bord_eval = MoveMaker(game_map, 10, 4)
combatant = Combatant(4)
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

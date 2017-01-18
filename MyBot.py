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
        strns = [gm.strn[x, y] for (x, y) in locs]

        for ci in np.argsort(strns)[::-1]:
            cx, cy = locs[ci]
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            # if (cx + cy + gm.turn % 2) != gm.parity:
            #     self.moves[cx, cy] = cx, cy
            #     self.moved[cx, cy] = True

            nbrs = gm.nbrs[(cx, cy)]
            scores = [gm.combat_heur[nx, ny] for (nx, ny) in nbrs]

            nx, ny = nbrs[np.argmax(scores)]
            self.moves[(cx, cy)] = nx, ny
            self.moved[cx, cy] = True
            gm.combat_heur[nx, ny] /= 10000

            nx, ny = nbrs[np.argmax(scores)]

    def decide_close_moves(self, gm):
        locs = np.transpose(np.nonzero(gm.close_to_combat))
        for cx, cy in locs:
            if gm.strnc[cx, cy] < (gm.prodc[cx, cy] * self.combat_wait):
                continue

            # if (cx + cy + gm.turn % 2) != gm.parity:
            #     self.moves[cx, cy] = cx, cy
            #     self.moved[cx, cy] = True

            dmat = np.divide(gm.melee_mat, gm.dists[cx, cy])
            tx, ty = np.unravel_index(dmat.argmax(), dmat.shape)

            self.moves[(cx, cy)] = tx, ty
            self.moved[cx, cy] = True

    def dump_moves(self, gm):
        return self.moves


class MoveMaker:
    """Evaluate the value of border squares and coordinate moves.
    Values are taken for each x, y, s, where s is the degree to which
    to hunt for teamups.
    """
    def __init__(self, gm, wait, glob_k):
        self.glob_k = glob_k
        self.bulk_mvmt_off = 10
        self.wait = wait

    def decide_noncombat_moves(self, gm, moved):
        working_strn = gm.strn.copy()
        self.to_travel = np.zeros_like(gm.prod)
        self.moves = {}

        motile = ((gm.strnc >= gm.prodc * self.wait) * gm.owned).astype(bool)
        motile[np.nonzero(gm.gte_nbr)] = True
        motile[np.nonzero(moved)] = False
        strn_avail = gm.ostrn * motile

        Vloc, Vmid, Vglob = self.get_cell_value(gm)
        Vmid *= gm.safe_to_take
        Vglob *= gm.safe_to_take

        Vtot = Vloc + Vmid + Vglob

        self.desired_d1_moves = {}
        d1_conquered = np.ones_like(Vtot, dtype=bool)
        fully_alloc = np.zeros_like(Vtot, dtype=bool)

        to_move = motile.copy()
        to_move[np.nonzero(moved)] = False
        to_move_locs = np.transpose(np.nonzero(to_move))
        to_move_strn = [gm.strn[x, y] for (x, y) in to_move_locs]
        for ai in np.argsort(to_move_strn)[::-1]:
            ax, ay = to_move_locs[ai]
            t2c = np.maximum(0, (working_strn - gm.strn[ax, ay]) / gm.prodc)

            prox_value = np.divide(Vmid, (gm.dists[ax, ay] + t2c)) * d1_conquered + \
                np.divide(Vglob, (gm.dists[ax, ay] + self.bulk_mvmt_off))
            tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)
            self.moves[(ax, ay)] = tx, ty
            self.to_travel[ax, ay] = gm.dists[ax, ay, tx, ty]

            # if not fully_alloc[tx, ty] and gm.dists[ax, ay, tx, ty] <= 2:
            #     working_strn[tx, ty] -= gm.strn[ax, ay]
            #     if working_strn[tx, ty] < 0:
            #         working_strn[tx, ty] = gm.strn[tx, ty]
            #         fully_alloc[tx, ty] = True

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


def coalesce(moves, gm, bord_eval):
    return moves
    # newmoves = {}
    # weakmoves = {(ax, ay): (tx, ty, dir_)
    #              for (ax, ay), (tx, ty, dir_) in moves.items()
    #              if gm.strn[ax, ay] < 95 and dir_ != 0 and
    #                 bord_eval.to_travel[ax, ay] > 6}
    # for (ax, ay), (tx, ty, dir_) in weakmoves.items():
    #     if dir_ == 1 or dir_ == 3:
    #         if (ax+2, ay) in weakmoves.keys() and weakmoves[(ax+2, ay)][2] == dir_:
    #             newmoves[(ax, ay)] = ax+1, ay, 2
    #             newmoves[(ax+2, ay)] = ax+1, ay, 4
    #         elif (ax-2, ay) in weakmoves.keys() and weakmoves[(ax-2, ay)][2] == dir_:
    #             newmoves[(ax, ay)] = ax-1, ay, 4
    #             newmoves[(ax-2, ay)] = ax-1, ay, 2
    #     if dir_ == 2 or dir_ == 4:
    #         if (ax, ay+2) in weakmoves.keys() and weakmoves[(ax, ay+2)][2] == dir_:
    #             newmoves[(ax, ay)] = ax, ay+1, 3
    #             newmoves[(ax, ay+2)] = ax, ay+1, 1
    #         elif (ax, ay-2) in weakmoves.keys() and weakmoves[(ax, ay-2)][2] == dir_:
    #             newmoves[(ax, ay)] = ax, ay-1, 1
    #             newmoves[(ax, ay-2)] = ax, ay-1, 3

    # for k, v in newmoves.items():
    #     moves[k] = v

    # return moves


def process_moves(moves):
    return [hlt.Move(ax, ay, dir_) for (ax, ay), (_, _, dir_) in moves.items()]


game_map = hlt.ImprovedGameMap(8)
hlt.send_init("DexBotNeuer")
game_map.get_frame()
game_map.update()

k = 1.5 - game_map.num_enemies * 0.1
bord_eval = MoveMaker(game_map, wait=4, glob_k=k)
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
    coalesce_moves = coalesce(resolved_moves, game_map, bord_eval)

    hlt.send_frame(process_moves(coalesce_moves))
    game_map.get_frame()



    # def decide_noncombat_moves(self, gm, moved):
    #     working_strn = gm.strn.copy()
    #     self.moves = {}

    #     motile = ((gm.strnc >= gm.prodc * self.wait) * gm.owned).astype(bool)
    #     motile[np.nonzero(gm.gte_nbr)] = True
    #     motile[np.nonzero(moved)] = False
    #     strn_avail = gm.ostrn * motile

    #     Vloc, Vmid, Vglob = self.get_cell_value(gm)
    #     Vtot = Vloc + Vmid + Vglob

    #     self.desired_d1_moves = {}
    #     d1_conquered = np.ones_like(Vtot, dtype=bool)
    #     fully_alloc = np.zeors_like(Vtot, dtype=bool)

    #     to_move = motile.copy()
    #     to_move[np.nonzero(moved)] = False
    #     to_move_locs = np.transpose(np.nonzero(to_move))
    #     for ax, ay in to_move_locs:
    #         t2c = np.maximum(0, (working_strn - gm.strn[ax, ay]) / gm.prodc)
    #         # str_bonus = np.maximum(1, gm.strn[ax, ay] / gm.strn)
    #         # str_bonus = np.minimum(1.2, np.sqrt(str_bonus))

    #         prox_value = np.divide(Vmid, (gm.dists[ax, ay] + t2c)) * d1_conquered + \
    #             np.divide(Vglob, (gm.dists[ax, ay] + self.bulk_mvmt_off))
    #         # prox_value *= d1_conquered
    #         tx, ty = np.unravel_index(prox_value.argmax(), prox_value.shape)
    #         self.moves[(ax, ay)] = tx, ty

    #         if not fully_alloc[tx, ty]:
    #             working_strn[tx, ty] -= gm.strn[ax, ay]
    #             if working_strn[tx, ty] < 0:
    #                 working_strn[tx, ty] = gm.strn[tx, ty]
    #                 fully_alloc[tx, ty] = True

    #         # Add to a postprocessing queue for later
    #         if gm.dists[ax, ay, tx, ty] == 1:
    #             self.desired_d1_moves.setdefault((tx, ty), []).append((ax, ay))
    #             if gm.strn[ax, ay] > gm.strn[tx, ty]:
    #                 # No one else can erroneously target this cell
    #                 d1_conquered[tx, ty] = 0

    #     self.process_d1_teamups(gm)

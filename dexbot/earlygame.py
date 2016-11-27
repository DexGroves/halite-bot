"""Classes to help with playing the earlygame."""


import numpy as np
import random
from dexbot.move_queue import MoveQueue, PendingMoves
from dexbot.pathfinder import Pathfinder
from dexbot.distance_calculator import DistanceCalculator as dc


class EarlybotAPI(object):
    """Turn a MapState into a MoveQueue based on earlygame logic."""

    def __init__(self, map_state, order, max_t):
        self.max_t = max_t
        self.tactician = EarlyTactician(map_state, order, self.max_t)
        self.pathfinder = Pathfinder(map_state)
        self.teamupper = TeamUpper(map_state)
        self.active = True
        # with open('moves.txt', 'w') as f:
        #     f.write('\n')
        # with open("teamup.txt", "w") as f:
        #     f.write(repr(self.max_t) + '--------------\n')

    def update(self, map_state):
        self.max_t -= 1
        if self.max_t <= 1:
            self.active = False

        # with open('moves.txt', 'a') as f:
        #     f.write(repr(self.max_t) + '\t' + repr(self.active) + '\n')

        # with open("teamup.txt", "a") as f:
        #     f.write(repr(self.max_t) + '--------------\n')

        self.tactician.update(map_state, self.max_t)
        self.owned_locs = map_state.get_self_locs()

    def get_moves(self, map_state):
        mq = MoveQueue(self.owned_locs)

        plan_targ = np.empty(len(self.owned_locs), dtype=tuple)
        value = np.empty(len(self.owned_locs), dtype=float)

        for i, (x, y) in enumerate(self.owned_locs):
            moves, value[i] = self.tactician.find_optimal_move(x, y, map_state)
            if value[i] == 0:
                plan_targ[i] = x, y
            else:
                plan_targ[i] = moves[0], moves[1]

        static_moves = {
            (self.owned_locs[i][0], self.owned_locs[i][1]): plan_targ[i]
            for i in range(len(self.owned_locs))
        }

        pm = self.teamupper.get_teamups(self.owned_locs, plan_targ, value, map_state)

        mq.process_pending(pm)

        # with open('moves.txt', 'a') as f:
        #     f.write(repr(pm))
        #     f.write(repr(mq))
        #     f.write(repr(static_moves) + '\n')

        for (x, y), (tx, ty) in static_moves.items():
            if (x, y) in mq.rem_locs and tx is not None:
                direction = self.pathfinder.find_path(x, y, tx, ty, map_state)
                mq.pend_move(x, y, direction)

        # with open('moves.txt', 'a') as f:
        #     f.write(repr(mq))

        return mq


class EarlyTactician(object):
    """Expose a move() that returns moves based on the earlygame state."""

    def __init__(self, map_state, order, max_t):
        self.order = order
        self.max_t = max_t

        self.centre = map_state.get_self_locs()[0]

        self.base = dc.get_base_matrix(map_state.width, map_state.height, 1)
        self.base[0, 0] = 0
        self.dists = dc.offset(self.base, self.centre[0], self.centre[1])

        self.handover = False

    def update(self, map_state, max_t):
        self.max_t = max_t
        locs = map_state.get_self_locs()
        for loc in locs:
            new_dist = dc.offset(self.base, loc[0], loc[1])
            self.dists = np.minimum(self.dists, new_dist)

    def find_optimal_move(self, x, y, map_state):
        """Loop over all indices up to order in order to determine
        the best move. Inefficient, can probably do something better
        with recursion starting at the outside, but for now f it.
        x, y unused but required for future multi piece logic.
        """
        hons = self.find_higher_order_neigbours(x, y, map_state)
        Ahi = np.zeros(len(hons), dtype=float)

        # No neighbours, no moves!
        if len(hons) == 0:
            return (x, y), 0

        Sh = map_state.strn[x, y]
        for i, (ix, iy) in enumerate(hons):
            Tcap = self.time_to_cap(x, y, ix, iy, map_state, Sh)
            if Tcap < self.max_t:
                Pi = map_state.prod[ix, iy]
                Si = map_state.strn[ix, iy]
                extra_strn = np.max(Sh - Si, 0)
                Aij = self.get_maxAij(ix, iy, 1,
                                      self.max_t - Tcap,
                                      map_state, extra_strn)
                Ahi[i] = Pi + Aij
        maxj = np.argmax(Ahi)
        return (hons[maxj][0], hons[maxj][1]), Ahi[maxj]

    def get_maxAij(self, ix, iy, cur_ord, Ti, map_state, extra_strn):
        hons = self.find_higher_order_neigbours(ix, iy, map_state)
        Aij = np.zeros(len(hons), dtype=float)

        # No neighbours, no moves!
        if len(hons) == 0:
            return 0

        if cur_ord > 2:
            extra_strn = 0  # A hack, assume strength can't bleed more than 2

        # Last call!
        if cur_ord == self.order:
            for i, (jx, jy) in enumerate(hons):
                Tcap = self.time_to_cap(ix, iy, jx, jy, map_state, 0)
                if Tcap < Ti:
                    dvdt = map_state.prod[ix, iy] * map_state.prod[jx, jy] / \
                        map_state.strn[jx, jy]
                    Aij[i] = dvdt * (Ti - Tcap)
            maxj = np.argmax(Aij)
            return Aij[maxj]

        # Else still recursing
        for i, (jx, jy) in enumerate(hons):
            Tcap = self.time_to_cap(ix, iy, jx, jy, map_state, extra_strn)
            if Tcap < Ti:
                Ajk = self.get_maxAij(jx, jy, cur_ord + 1, Ti - Tcap,
                                      map_state, extra_strn)

                dvdt = map_state.prod[ix, iy] * map_state.prod[jx, jy] / \
                    map_state.strn[jx, jy]
                Aij[i] = dvdt * (Ti - Tcap) + Ajk
        maxj = np.argmax(Aij)

        # with open('debug.txt', 'w') as f:
        #     f.write(
        #         repr(hons) + '\n' + repr(maxj) + '\n' +
        #         repr(Aij)
        #     )

        return Aij[maxj]

    def find_higher_order_neigbours(self, x, y, map_state):
        order = self.dists[x, y]
        neighbours = map_state.get_neighbours(x, y)

        return [n for n in neighbours if self.dists[n[0], n[1]] == (order + 1)]

    def time_to_cap(self, ox, oy, ux, uy, map_state, extra_strn):
        """Time to capture a piece."""
        own_prod = map_state.prod[ox, oy]

        if own_prod == 0:
            return 9999  # Arbitrarily large. Very big number. Wooow.

        turns = np.max(
            map_state.strn[ux, uy] - extra_strn, 0
        ) / own_prod

        return turns


class TeamUpper(object):
    """Handle teaming up to capture border areas in the earlygame."""

    def __init__(self, map_state):
        self.pathfinder = Pathfinder(map_state)

    def get_teamups(self, locs, targs, vals, map_state):
        # costs = np.empty(len(locs), dtype=float)
        # for i, (x, y) in enumerate(locs):
        #    costs[i] = self.get_cost_move(x, y, val[i], map_state)
        pm = PendingMoves()

        loc_to_cost = {
            (x, y): self.get_cost_move(x, y, vals[i], map_state)
            for i, (x, y) in enumerate(locs)
        }

        targ_to_assignee = {
            (targs[i][0], targs[i][1]): locs[i] for i, (x, y) in enumerate(locs)
        }

        assignee_to_value = {
            (x, y): vals[i] for i, (x, y) in enumerate(locs)
        }

        # Build possible teamups
        # brdr_locs = map_state.get_border_locs()
        targ_list = []
        ass_list = []
        nbr_list = []
        val_list = []
        for i, (tx, ty) in enumerate(targs):
            if (tx, ty) in targ_to_assignee.keys():
                ax, ay = targ_to_assignee[(tx, ty)]  # Block ready to go
            else:
                neighbours = map_state.get_allied_neighbours(tx, ty)

                ax, ay = random.choice(neighbours)   # Could be better!

            a_val = assignee_to_value[(ax, ay)]

            if tx == ax and ty == ay:
                continue
            if tx is None:
                continue

            a_neighbours = map_state.get_allied_neighbours(ax, ay)
            t_neighbours = map_state.get_allied_neighbours(tx, ty)
            for nbrx, nbry in (a_neighbours + t_neighbours):
                if nbrx == ax and nbry == ay:
                    continue
                val_move = self.get_val_move(
                    ax, ay, nbrx, nbry, tx, ty, a_val, map_state)
                cost_move = loc_to_cost[(nbrx, nbry)]

                total_str = map_state.strn[nbrx, nbry] + map_state.strn[ax, ay] + \
                    map_state.prod[ax, ay]

                if (val_move - cost_move) > 0 and (
                        map_state.strn[tx, ty] < total_str):
                    targ_list.append((tx, ty))
                    ass_list.append((ax, ay))
                    nbr_list.append((nbrx, nbry))
                    val_list.append(val_move - cost_move)

                # with open("teamup.txt", "a") as f:
                #     f.write("\t".join(
                #         [
                #             repr((tx, ty)), repr((ax, ay)), repr((nbrx, nbry)),
                #             repr(cost_move), repr(val_move), "\n"
                #         ]
                #     ))

        # Issue
        while len(val_list) > 0:
            i = np.argmax(val_list)
            ax, ay = ass_list[i]
            tx, ty = targ_list[i]
            nbrx, nbry = nbr_list[i]

            direction = self.pathfinder.find_path(nbrx, nbry, tx, ty, map_state)
            pm.pend_move(nbrx, nbry, direction)
            pm.pend_move(ax, ay, 0)

            deletions = []
            for i in range(len(val_list)):
                if ass_list[i] == (ax, ay) or ass_list[i] == (nbrx, nbry):
                    deletions.append(i)
                elif nbr_list[i] == (ax, ay) or nbr_list[i] == (nbrx, nbry):
                    deletions.append(i)
                elif targ_list[i] == (tx, ty):
                    deletions.append(i)

            for deletion in reversed(deletions):
                del ass_list[deletion]
                del targ_list[deletion]
                del nbr_list[deletion]
                del val_list[deletion]

        return pm

    @staticmethod
    def get_cost_move(x, y, val, map_state):
        if map_state.prod[x, y] == 0:
            return 0
        Tdelay = (map_state.strn[x, y] / map_state.prod[x, y] + 1)
        return val * Tdelay

    @staticmethod
    def get_val_move(ax, ay, hx, hy, tx, ty, val, map_state):
        if map_state.prod[ax, ay] == 0:
            return 0

        Tcap = (map_state.strn[tx, ty] - map_state.strn[ax, ay]) / \
            map_state.prod[ax, ay]

        if Tcap <= 1:
            return 0

        Tred = (map_state.strn[hx, hy] / map_state.prod[ax, ay])
        Tred = np.minimum(Tcap - 1, Tred)

        return val * Tred

import time
import numpy as np


class MoveFinder(object):
    """Find moves for pieces to make!"""

    def __init__(self, config):
        self.map_scorer = MapScorer()
        self.min_wait_turns = config['min_wait_turns']
        with open("value.txt", "w") as f:
            f.write("turn,x,y,val\n")
        with open("evalby.txt", "w") as f:
            f.write("turn,x,y,val\n")
        self.turn = -1

    def update(self, ms):
        self.bvals = self.get_border_values(ms)
        self.turn += 1
        with open("value.txt", "a") as f:
            for bx, by in ms.border_locs:
                f.write(",".join([
                    repr(self.turn), repr(bx), repr(by), repr(self.bvals[bx, by])]))
                f.write("\n")

    # def find_move(self, x, y, ms):
    #     """This assumes that the most direct route to the border can
    #     always be taken.
    #     """
    #     if ms.strn[x, y] < (self.min_wait_turns * ms.prod[x, y]):
    #         return x, y

    #     offset = 2
    #     # wait_time = np.maximum(0, (ms.strn - ms.strn[x, y]) / max(ms.prod[x, y], 1))
    #     wait_time = (ms.strn - ms.strn[x, y]) / ms.prod[x, y]
    #     b_by_dist = np.divide(self.bvals, ms.base_dist[x, y, :, :] + wait_time + offset)
    #     # b_by_dist = np.divide(self.bvals, ms.base_dist[x, y, :, :])
    #     # b_by_dist = self.bvals
    #     # Discount the delta for blocks that are too weak
    #     # xy_strn = ms.strn[x, y]
    #     # discount = np.minimum(1, xy_strn / ms.border_strn)
    #     # b_by_dist_disc = np.multiply(b_by_dist, discount)

    #     tx, ty = np.unravel_index(b_by_dist.argmax(), b_by_dist.shape)

    #     # with open('debug.txt', 'w') as f:
    #     #     f.write(repr(self.bvals) + '\n' +
    #     #             repr(b_by_dist) + '\n' +
    #     #             repr(b_by_dist_disc) + '\n' +
    #     #             repr((tx, ty)))

    #     return tx, ty-

    def find_move(self, x, y, ms):
        if ms.strn[x, y] < (self.min_wait_turns * ms.prod[x, y]):
            gomode = False
            nbrs = ms.get_neighbours(x, y)
            for nx, ny in nbrs:
                if ms.strn[nx, ny] < ms.strn[x, y] and ms.mine[nx, ny] == 0:
                    gomode = True
                    break
            if not gomode:
                return x, y

        mv_vals = np.zeros(len(ms.border_locs))
        for i, (bx, by) in enumerate(ms.border_locs):
            prod_cost = ms.ip.get_path_cost(x, y, bx, by) + ms.prod[x, y]

            str_ratio = (ms.strn[bx, by] - ms.strn[x, y]) / max(1, ms.prod[x, y])
            str_deficit = max(str_ratio, 0)
            str_bonus = min(max(ms.strn[x, y] / max(1, ms.strn[bx, by]), 1), 10)

            turn_cost = ms.base_dist[x, y, bx, by]  # Approximation!

            damage_bonus = ms.get_splash_from(bx, by) * 1

            total_cost = prod_cost + (str_deficit * 1) + (max(1, turn_cost) * 1.0)
            mv_vals[i] = (damage_bonus + str_bonus) * self.bvals[bx, by] / total_cost

            # with open("evalby.txt", "a") as f:
            #     f.write(",".join([
            #         repr(self.turn), repr(x), repr(y),
            #         repr(bx), repr(by), repr(damage_bonus), repr(str_bonus),
            #         repr(self.bvals[bx, by]), repr(total_cost), repr(mv_vals[i])]))
            #     f.write("\n")

        mv = np.argmax(mv_vals)
        # with open('wtf.txt', 'w') as f:
        #     f.write(repr(self.bvals) + '\t' +
        #             repr(prod_cost) + '\t' +
        #             repr(mv_vals) + '\t' +
        #             repr(mv))

        tx, ty = ms.border_locs[mv]
        px, py = ms.ip.get_path_step(x, y, tx, ty)

        with open("evalby.txt", "a") as f:
            f.write(",".join(["END",
                repr(self.turn), repr(x), repr(y), repr(ms.strn[x, y]),
                repr(tx), repr(ty), repr(px), repr(py), repr(mv_vals[mv])]))
            f.write("\n")
        # if px == x and py == y:
        #     return tx, ty
        # else:
        #     return px, py
        return px, py

    def get_border_values(self, ms):
        mapval = self.map_scorer.eval(ms)
        bvals = np.zeros((ms.width, ms.height), dtype=float)
        for bx, by in ms.border_locs:
            bvals[bx, by] = self.map_scorer.eval_on_capture(ms, bx, by)

        # with open("borders.txt", "a") as f:
        #     f.write(repr(self.turn) + '\t' + repr(ms.border_locs) + '\n')

        return bvals - mapval


class MapScorer(object):
    """Score the value of a real or hypothetical board state."""

    def __init__(self):
        """Config stuff goes here."""
        self.optimism = 10
        with open("eval.txt", "w") as f:
            f.write("\n")

    def eval(self, ms):
        """Return the value of the board state."""
        self.Vown = self.eval_owned(ms)
        self.Vnear = self.optimism * self.eval_near(ms, ms.sp.reach)
        return self.Vown + self.Vnear

    def eval_on_capture(self, ms, x, y):
        """Return the value of the board state for x, y being captured."""

        # Mock up the new board state
        orig_blank = ms.blank[x, y]
        orig_enemy = ms.enemy[x, y]
        ms.mine[x, y] = True
        ms.blank[x, y] = False
        ms.enemy[x, y] = False

        # Get new paths. ms.sp handles the mocking on its end
        hypo_path = ms.sp.update_path_acquisition(x, y)
        # hypo_reach = np.apply_along_axis(np.min, 0,
        #                                  np.stack([hypo_path, ms.sp.reach]))
        longer = hypo_path > ms.sp.reach
        hypo_path[longer] = ms.sp.reach[longer]

        if orig_blank == 1 and ms.strn[x, y] > 0:
            Vown = self.eval_owned(ms)
        else:
            Vown = self.Vown + 10  # Flat bonus for taking border square

        Vnear = self.optimism * self.eval_near(ms, hypo_path)

        # with open("eval.txt", "a") as f:
        #     f.write(repr((x, y)) + '\t' + repr(Vown) + '\t' +
        #             repr(Vnear) + '\n')

        # Unmock the board
        ms.mine[x, y] = False
        ms.blank[x, y] = orig_blank
        ms.enemy[x, y] = orig_enemy

        return Vown + Vnear

    def eval_owned(self, ms):
        """This ignores owned strength for now. Just sum of owned prod."""
        mine_idx = np.nonzero(ms.mine)
        return np.sum(ms.prod[mine_idx])

    def eval_near(self, ms, reach):
        """Just considers blank production for now."""
        blank_sq = np.nonzero(ms.blank.flatten())
        # map_vals = np.divide(ms.sp.prod_vec[blank_sq], reach[blank_sq])
        map_vals = ms.sp.prod_vec[blank_sq] - (reach[blank_sq]/10)
        return map_vals.sum()

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
            f.write("turn,status,x,y,bx,by,dmgbonus,strbonus,bval,cost,mval,px,py\n")
        self.turn = -1

    def update(self, ms):
        self.map_scorer.set_eval(ms)
        self.bvals = self.get_border_values(ms)
        self.turn += 1
        with open("value.txt", "a") as f:
            for bx, by in ms.border_locs:
                f.write(",".join([
                    repr(self.turn), repr(bx), repr(by), repr(self.bvals[bx, by])]))
                f.write("\n")

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
            prod_cost = ms.ip.get_path_cost(x, y, bx, by) + ms.prod[x, y] - ms.prod[bx, by]

            str_ratio = (ms.strn[bx, by] - ms.strn[x, y]) / max(1, ms.prod[x, y])
            time_to_cap = np.sqrt(max(str_ratio, 1))
            # time_to_arr = ms.base_dist[x, y, bx, by]  # Approximation!
            time_to_arr = ms.ip.get_path_length(x, y, bx, by)

            str_bonus = min(max(ms.strn[x, y] / max(1, ms.strn[bx, by]), 1), 1.5)

            # recoup_cost = ms.strn[bx, by] / max(1, ms.prod[x, y])
            damage_bonus = ms.get_splash_from(bx, by) * 1

            # total_cost = np.sqrt(prod_cost + (max(1, time_to_arr) * 1.0))
            if prod_cost > (0.3 * ms.strn[x, y]):
                mv_vals[i] = -9999
                total_cost = 9999
            else:
                # See ten turns ahead
                total_cost = max(time_to_cap + time_to_arr + 1, 6)
                mv_vals[i] = self.bvals[bx, by] / total_cost

            with open("evalby.txt", "a") as f:
                f.write(",".join([
                    repr(self.turn), "think", repr(x), repr(y),
                    repr(bx), repr(by), repr(damage_bonus), repr(str_bonus),
                    repr(self.bvals[bx, by]), repr(total_cost), repr(mv_vals[i]), " ", " "]))
                f.write("\n")

        mv = np.argmax(mv_vals)
        # with open('wtf.txt', 'w') as f:
        #     f.write(repr(self.bvals) + '\t' +
        #             repr(prod_cost) + '\t' +
        #             repr(mv_vals) + '\t' +
        #             repr(mv))

        tx, ty = ms.border_locs[mv]
        px, py = ms.ip.get_path_step(x, y, tx, ty)

        with open("evalby.txt", "a") as f:
            f.write(",".join([
                    repr(self.turn), "choose", repr(x), repr(y),
                    repr(tx), repr(ty), " ", " ", " ", " ", repr(mv_vals[i]), repr(px), repr(py)]))
            f.write("\n")

        # if px == x and py == y:
        #     return tx, ty
        # else:
        #     return px, py

        return px, py

    def get_border_values(self, ms):
        bvals = np.zeros((ms.width, ms.height), dtype=float)
        for bx, by in ms.border_locs:
            bvals[bx, by] = self.map_scorer.eval_on_capture(ms, bx, by)

        # with open("borders.txt", "a") as f:
        #     f.write(repr(self.turn) + '\t' + repr(ms.border_locs) + '\n')

        return bvals


class MapScorer(object):
    """Score the value of a real or hypothetical board state."""

    def __init__(self):
        """Config stuff goes here."""
        self.optimism = 1
        with open("eval.txt", "w") as f:
            f.write("\n")
        self.paths_cache = {}

    def set_eval(self, ms):
        """Return the value of the board state."""
        self.Vown = self.eval_owned(ms)
        self.map_vals = self.eval_near(ms, ms.sp.reach)
        self.Vnear = self.optimism * self.map_vals.sum()
        self.V = self.Vown + self.Vnear

    def eval_on_capture(self, ms, x, y):
        """Return the value of the board state for x, y being captured."""

        # Mock up the new board state
        orig_blank = ms.blank[x, y]
        orig_enemy = ms.enemy[x, y]
        ms.mine[x, y] = True
        ms.blank[x, y] = False
        ms.enemy[x, y] = False

        # Get new paths.
        if (x, y) in self.paths_cache.keys():
            hypo_path = self.paths_cache[(x, y)]
        else:
            # paths = np.stack([ms.sp.get_path(nx, ny) for (nx, ny) in ms.nbrs[x, y]])
            # hypo_path = np.apply_along_axis(np.min, 0, paths)
            # hypo_path[hypo_path == 0] = 1
            # self.paths_cache[(x, y)] = hypo_path
            hypo_path = ms.sp.get_path(x, y)
            hypo_path[hypo_path == 0] = 1

        longer = hypo_path > ms.sp.reach
        hypo_path[longer] = ms.sp.reach[longer]

        if orig_blank == 1 and ms.strn[x, y] > 0:
            Vown = self.eval_owned(ms)
        else:
            Vown = self.Vown + 1  # Flat bonus for taking border square

        map_vals = self.eval_near(ms, hypo_path)

        vi = ms.sp.get_vertex(x, y)
        map_vals[vi] = self.map_vals[vi]  # Don't count capturing as a negative

        Vnear = self.optimism * map_vals.sum()
        with open("eval.txt", "a") as f:
            f.write(repr(map_vals.sum()) + '\t' + repr((x, y)) + '\t' + repr(Vown) +
                    '\t' + repr(Vnear) + '\n')

        # Unmock the board
        ms.mine[x, y] = False
        ms.blank[x, y] = orig_blank
        ms.enemy[x, y] = orig_enemy

        return Vown + Vnear - self.V

    def eval_owned(self, ms):
        """This ignores owned strength for now. Just sum of owned prod."""
        mine_idx = np.nonzero(ms.mine)
        return np.sum(ms.prod[mine_idx] ** 2 / ms.orig_strn[mine_idx])

    def eval_near(self, ms, reach):
        """Just considers blank production for now."""
        blank_sq = np.nonzero(ms.blank.flatten())
        orig_strn = ms.orig_strn.flatten()
        map_vals = np.zeros(len(reach), dtype=float)
        map_vals[blank_sq] = np.divide(ms.sp.prod_vec[blank_sq] ** 2,
                                       np.multiply(reach[blank_sq],
                                                   orig_strn[blank_sq]))

        # map_vals = ms.sp.prod_vec[blank_sq] - (reach[blank_sq]/10)
        return map_vals

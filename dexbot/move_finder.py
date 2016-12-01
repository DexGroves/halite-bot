import numpy as np
from dexbot.matrix_tools import StrToCalculator as stc


class MoveFinder(object):
    """Find moves for pieces to make!"""

    def __init__(self, config):
        self.map_scorer = MapScorer(5)
        self.min_wait_turns = config['min_wait_turns']

    def update(self, ms):
        self.bvals = self.get_border_values(ms)

    def find_move(self, x, y, ms):
        """This assumes that the most direct route to the border can
        always be taken.
        """
        if ms.strn[x, y] < (self.min_wait_turns * ms.prod[x, y]):
            return x, y

        b_by_dist = np.divide(self.bvals, ms.base_dist[x, y, :, :])

        # Discount the delta for blocks that are too weak
        xy_strn = ms.strn[x, y]
        discount = np.minimum(1, xy_strn / ms.border_strn)
        b_by_dist_disc = np.multiply(b_by_dist, discount)

        tx, ty = np.unravel_index(b_by_dist_disc.argmax(), b_by_dist_disc.shape)

        # with open('debug.txt', 'w') as f:
        #     f.write(repr(self.bvals) + '\n' +
        #             repr(b_by_dist) + '\n' +
        #             repr(b_by_dist_disc) + '\n' +
        #             repr((tx, ty)))

        return tx, ty

    def get_border_values(self, ms):
        bvals = np.zeros((ms.width, ms.height), dtype=float)
        for bx, by in ms.border_locs:
            bvals[bx, by] = self.map_scorer.eval_on_capture(ms, bx, by)
        return bvals


class MapScorer(object):
    """Score the value of a real or hypothetical board state."""

    def __init__(self, Dmax):
        """Config stuff goes here."""
        self.Dmax = Dmax

    def eval(self, ms):
        """Return the value of the board state."""
        V = self.eval_owned(ms) + self.eval_near(ms, ms.dist_from_mine)
        return V

    def eval_on_capture(self, ms, x, y):
        """Return the value of the board state for x, y being captured."""
        orig_blank = ms.blank[x, y]
        orig_enemy = ms.enemy[x, y]

        # Mock up the new board state
        ms.mine[x, y] = True
        ms.blank[x, y] = False
        ms.enemy[x, y] = False

        dist_from_mine = stc.distance_from_owned(ms.base_dist, ms.mine)
        V = self.eval_owned(ms) + self.eval_near(ms, dist_from_mine).sum()

        # with open('vs.txt', 'w') as f:
        #     f.write(repr(self.eval_owned(ms)) + '\n' +
        #             repr(self.eval_near(ms, dist_from_mine)) + '\n' +
        #             repr(dist_from_mine) + '\n')

        # Unmock the board
        ms.mine[x, y] = False
        ms.blank[x, y] = orig_blank
        ms.enemy[x, y] = orig_enemy

        return V.sum()

    def eval_owned(self, ms):
        """This ignores owned strength for now. Just sum of owned prod."""
        mine_idx = np.nonzero(ms.mine)
        return np.sum(ms.prod[mine_idx])

    def eval_near(self, ms, dist_from_mine):
        """Just considers blank production for now. With no constant."""
        blank_idx = np.nonzero(ms.blank)
        blank_prod = np.zeros_like(ms.prod)
        blank_prod[blank_idx] = ms.prod[blank_idx]

        str_to = stc.get_str_to(ms.strn, dist_from_mine, self.Dmax)

        np.savetxt('strn_to.txt', str_to)

        return np.divide(blank_prod, str_to)

import numpy as np
from itertools import product
import dexlib.nphlt as hlt


class BorderEvaluator:
    """Evaluate the value of border squares and coordinate moves.
    Values are taken for each x, y, s, where s is the degree to which
    to hunt for teamups.
    """
    def __init__(self, maxd):
        self.maxd = maxd

    def update(self, gmap):
        # Masking like this isn't _quite_ right
        self.motile = (gmap.strnc >= gmap.prodc * 5)
        strn_avail = gmap.ostrn * self.motile

        t2r = gmap.strnc / gmap.prodc  # Can relax this later
        value = gmap.prod.copy()       # Can improve this later

        iter_ = product(gmap.border_locs, range(self.maxd))
        iterlen = len(gmap.border_locs) * self.maxd

        self.bmoves = np.empty(iterlen, dtype=tuple)
        self.bavail = np.empty(iterlen, dtype=bool)
        bvals = np.empty(iterlen, dtype=float)

        for i, ((bx, by), s) in enumerate(iter_):
            bstrn = gmap.strn[bx, by]
            nbr_strn = strn_avail[np.where(gmap.dists[bx, by] <= s)]
            nbr_prod = gmap.oprod[np.where(gmap.dists[bx, by] <= s)]

            t2c = max(s, (bstrn - nbr_strn) / nbr_prod)

            self.bmoves[i] = bx, by, s
            self.bavail[i] = nbr_strn > bstrn
            bvals[i] = value[bx, by] / (t2r[bx, by] + t2c)

        bvals *= -1  # Force high-to-low sorting
        self.bmoves = self.bmoves[np.argsort(bvals)]
        self.bavail = self.bavail[np.argsort(bvals)]

    def get_moves(self, gmap):
        moves = []
        available = gmap.owned.copy()
        for (bx, by, s), bavail in zip(self.bmoves, self.bavail):
            assigned_cells = (gmap.dists[bx, by] <= s) * gmap.owned
            available[np.where(gmap.dists[bx, by] <= s)] = 0



def get_move(x, y, gmap):
    pass


game_map = hlt.ImprovedGameMap()
hlt.send_init("DexBotNeuer")


while True:
    game_map.get_frame()
    game_map.update()
    moves = [get_move(x, y, game_map) for (x, y) in game_map.owned_locs]
    hlt.send_frame(moves)

class Pathfinder(object):
    """Handle the routing from x, y to nx, ny."""
    def __init__(self, ms):
        self.width = ms.width
        self.height = ms.height

    def find_pref_next(self, x, y, nx, ny, ms):
        dist_north = (y - ny) % self.height
        dist_east = (nx - x) % self.width
        dist_south = (ny - y) % self.height
        dist_west = (x - nx) % self.width

        if dist_north < dist_south:
            ypref, ydist = 1, dist_north
        elif (dist_north == 0):
            ypref, ydist = None, 0
        else:
            ypref, ydist = 3, dist_south

        if dist_east < dist_west:
            xpref, xdist = 2, dist_east
        elif (dist_east == 0):
            xpref, xdist = None, 0
        else:
            xpref, xdist = 4, dist_west

        xnx, xny = ms.cardinal_to_nxny(x, y, xpref)
        ynx, yny = ms.cardinal_to_nxny(x, y, ypref)

        if ms.mine[xnx, xny] and ms.mine[ynx, yny] and \
                ydist > 0 and xdist > 0:
            if ms.prod[xnx, xny] < ms.prod[ynx, yny]:
                return (xnx, xny), (ynx, yny)
            else:
                return (ynx, yny), (xnx, xny)

        can_mv_x = ms.can_occupy_safely(x, y, xnx, xny) == 1
        can_mv_y = ms.can_occupy_safely(x, y, ynx, yny) == 1

        if ypref is None and can_mv_x:
            return (xnx, xny), (None, None)
        if xpref is None and can_mv_y:
            return (ynx, yny), (None, None)

        if not can_mv_x and not can_mv_y:
            return (x, y), (None, None)

        if not can_mv_x:
            return (ynx, yny), (None, None)

        if not can_mv_y:
            return (xnx, xny), (None, None)

        if (x + y) % 2 == 0:
            return (xnx, xny), (ynx, yny)
        else:
            return (ynx, yny), (xnx, xny)

        return (x, y), (None, None)  # Note... why?

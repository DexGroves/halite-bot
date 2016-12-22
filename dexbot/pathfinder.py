"""Handle the routing from x, y to nx, ny."""


import random


class Pathfinder(object):

    def __init__(self, ms, min_wait=0):
        self.width = ms.width
        self.height = ms.height

        self.min_wait = min_wait

    # def find_path(self, x, y, nx, ny):
    #     dists = np.array([
    #         (y - ny) % self.height,
    #         (nx - x) % self.width,
    #         (ny - y) % self.height,
    #         (x - nx) % self.width
    #     ])
    #     dists[dists == 0] = 999
    #     dist_sort = np.argsort(dists)
    #     return np.argmin(dists) + 1

    def find_path(self, x, y, nx, ny, ms):
        if ms.strn[x, y] <= (ms.prod[x, y] * self.min_wait):
            return 0

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

        # Don't jitter from faraway activity. Be steadfast.
        if (ydist > 0) and xdist > (5 * ydist):
            ydist = 0
        if (xdist > 0) and ydist > (5 * xdist):
            xdist = 0

        if ms.mine[xnx, xny] and ms.mine[ynx, yny] and \
                ydist > 0 and xdist > 0:
            if ms.prod[xnx, xny] < ms.prod[ynx, yny]:
                return xpref
            else:
                return ypref

        # if random.random() > 0.5:
        if (x + y) % 2 == 0:
            if xdist > 0 and ms.mine[xnx, xny] == 1:
                return xpref
            elif ydist > 0 and ms.mine[ynx, yny] == 1:
                return ypref

            if xdist > 0 and ms.can_occupy_safely(x, y, xnx, xny) == 1:
                return xpref
            elif ydist > 0 and ms.can_occupy_safely(x, y, ynx, yny) == 1:
                return ypref
            else:
                return 0
        else:
            if ydist > 0 and ms.mine[ynx, yny]:
                return ypref
            elif xdist > 0 and ms.mine[xnx, xny]:
                return xpref

            if ydist > 0 and ms.can_occupy_safely(x, y, ynx, yny) == 1:
                return ypref
            elif xdist > 0 and ms.can_occupy_safely(x, y, xnx, xny) == 1:
                return xpref
            else:
                return 0

    def force_path(self, x, y, nx, ny, ms):
        """Find a path even if it looks like suicide.
        Useful for teaming up pieces.
        """
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

        if (x + y) % 2 == 0:
            if xdist > 0:
                return xpref
            elif ydist > 0:
                return ypref
            else:
                return 0
        else:
            if ydist > 0:
                return ypref
            elif xdist > 0:
                return xpref
            else:
                return 0

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

        # If both cardinals are mine, prefer to move along the
        # direction with lower production.
        if ms.mine[xnx, xny] and ms.mine[ynx, yny] and \
                ydist > 0 and xdist > 0:
            if ms.prod[xnx, xny] < ms.prod[ynx, yny]:
                return (xnx, xny), (ynx, yny)
            else:
                return (ynx, yny), (xnx, xny)

        can_mv_x = ms.can_occupy_safely(x, y, xnx, xny) and xdist > 0
        can_mv_y = ms.can_occupy_safely(x, y, ynx, yny) and ydist > 0

        # If one direction is mine, move along it
        if ms.mine[xnx, xny] and xdist > 0 and can_mv_y:
            return (xnx, xny), (ynx, yny)
        if ms.mine[ynx, yny] and ydist > 0 and can_mv_x:
            return (ynx, yny), (xnx, xny)

        if ms.mine[xnx, xny] and xdist > 0:
            return (xnx, xny), (None, None)
        if ms.mine[ynx, yny] and ydist > 0:
            return (ynx, yny), (None, None)

        # If both directions are possible, take the enemy, and then
        # the one that will pay for itself sooner.
        # Really some smarter combat object should be forcing moves here.
        if can_mv_x and can_mv_y:
            if ms.enemy[xnx, xny]:
                return (xnx, xny), (ynx, yny)
            if ms.enemy[ynx, yny]:
                return (ynx, yny), (xnx, xny)

            x_roi = ms.prod[xnx, xny] / max(1, ms.strn[xnx, xny])
            y_roi = ms.prod[ynx, yny] / max(1, ms.strn[ynx, yny])

            if x_roi > y_roi:
                return (xnx, xny), (ynx, yny)
            else:
                return (ynx, yny), (xnx, xny)

        # Only cases left are when one or no directions are possible
        if can_mv_x:
            return (xnx, xny), (None, None)
        elif can_mv_y:
            return (ynx, yny), (None, None)

        return (x, y), (None, None)

# class AStarPathfinder(object):

#     def __init__(self, ms, dists, min_wait=0):
#         self.width = ms.width
#         self.height = ms.height

#         self.dists = dists
#         self.min_wait = min_wait

#         self.solved_targets = {}

#     def find_path(self, ms, x, y, tx, ty):
#         if (tx, ty) in self.solved_targets.keys():
#             return self.solved_targets[x, y]  # Gonna need to do more here but w/e

#         td = np.zeros((ms.width, ms.height))

class PathFinder(object):
    """Handle the routing from x, y to nx, ny."""

    def __init__(self, ms):
        self.width = ms.width
        self.height = ms.height

    def find_pref_cardinal(self, x, y, nx, ny, ms):
        """Return the naive best way to go without a backup."""
        xpref, ypref, xdist, ydist = self._get_pref_and_distances(x, y, nx, ny)

        xnx, xny = self._cardinal_to_nxny(x, y, xpref)
        ynx, yny = self._cardinal_to_nxny(x, y, ypref)

        # If both cardinals are owned, prefer to move along the
        # direction with lower production.
        if ms.owned[xnx, xny] and ms.owned[ynx, yny] and \
                ydist > 0 and xdist > 0:
            if ms.prod[xnx, xny] < ms.prod[ynx, yny]:
                return xpref
            else:
                return ypref

        # If one direction is owned, move along it
        if ms.owned[xnx, xny] and xdist > 0:
            return xpref
        if ms.owned[ynx, yny] and ydist > 0:
            return ypref

        can_mv_x = self._can_occupy_safely(x, y, xnx, xny, ms) and xdist > 0
        can_mv_y = self._can_occupy_safely(x, y, ynx, yny, ms) and ydist > 0

        # If both directions are possible, take the enemy, and then
        # the one that will pay for itself sooner.
        # Really some smarter combat object should be forcing moves here.
        if can_mv_x and can_mv_y:
            if ms.enemy[xnx, xny]:
                return xpref
            if ms.enemy[ynx, yny]:
                return ypref

            x_roi = ms.prod[xnx, xny] / max(1, ms.strn[xnx, xny])
            y_roi = ms.prod[ynx, yny] / max(1, ms.strn[ynx, yny])

            if x_roi > y_roi:
                return xpref
            else:
                return ypref

        # Only cases left are when one or no directions are possible
        if can_mv_x:
            return xpref
        elif can_mv_y:
            return ypref

        return 0  # Still!

    def find_pref_next(self, x, y, nx, ny, ms):
        """Return two target x,y tuples in order of preference.
        Blocks have a bunch of heuristics to decide which of
        the <=2 possible directions is more appropriate.
        MoveResolver will force some blocks out of their way later.
        """
        xpref, ypref, xdist, ydist = self._get_pref_and_distances(x, y, nx, ny)

        xnx, xny = self._cardinal_to_nxny(x, y, xpref)
        ynx, yny = self._cardinal_to_nxny(x, y, ypref)

        # If both cardinals are owned, prefer to move along the
        # direction with lower production.
        if ms.owned[xnx, xny] and ms.owned[ynx, yny] and \
                ydist > 0 and xdist > 0:
            if ms.prod[xnx, xny] < ms.prod[ynx, yny]:
                return (xnx, xny), (ynx, yny)
            else:
                return (ynx, yny), (xnx, xny)

        can_mv_x = self._can_occupy_safely(x, y, xnx, xny, ms) and xdist > 0
        can_mv_y = self._can_occupy_safely(x, y, ynx, yny, ms) and ydist > 0

        # If one direction is owned, move along it
        if ms.owned[xnx, xny] and xdist > 0 and can_mv_y:
            return (xnx, xny), (ynx, yny)
        if ms.owned[ynx, yny] and ydist > 0 and can_mv_x:
            return (ynx, yny), (xnx, xny)

        if ms.owned[xnx, xny] and xdist > 0:
            return (xnx, xny), (None, None)
        if ms.owned[ynx, yny] and ydist > 0:
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

    def _get_pref_and_distances(self, x, y, nx, ny):
        """Get the preferred direction along the wrap (north vs south,
        east vs west) and corresponding distances for movement
        from x, y to nx, ny.
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

        return xpref, ypref, xdist, ydist

    def _cardinal_to_nxny(self, x, y, cardinal):
        if cardinal == 1:
            return x, (y - 1) % self.height
        elif cardinal == 2:
            return (x + 1) % self.width, y
        elif cardinal == 3:
            return x, (y + 1) % self.height
        elif cardinal == 4:
            return (x - 1) % self.width, y
        return x, y

    def _can_occupy_safely(self, x, y, nx, ny, ms):
        """Return whether a square can safely capture square nx, ny."""
        if ms.strn[nx, ny] < ms.strn[x, y] or ms.strn[x, y] >= 255:
            return True

        if ms.owned[nx, ny]:
            return True

        return False

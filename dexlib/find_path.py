def find_path(x, y, nx, ny, gm):
    dist_north = (y - ny) % gm.height
    dist_east = (nx - x) % gm.width
    dist_south = (ny - y) % gm.height
    dist_west = (x - nx) % gm.width

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

    xnx, xny = cardinal_to_nxny(x, y, xpref, gm)
    ynx, yny = cardinal_to_nxny(x, y, ypref, gm)

    # If both cardinals are owned, prefer to move along the
    # direction with lower production.
    if gm.owned[xnx, xny] and gm.owned[ynx, yny] and \
            ydist > 0 and xdist > 0:
        if gm.prod[xnx, xny] < gm.prod[ynx, yny]:
            return xpref, xnx, xny
        else:
            return ypref, ynx, yny

    # If one direction is owned, move along it
    if gm.owned[xnx, xny] and xdist > 0:
        return xpref, xnx, xny
    if gm.owned[ynx, yny] and ydist > 0:
        return ypref, ynx, yny

    can_mv_x = can_occupy_safely(x, y, xnx, xny, gm) and xdist > 0
    can_mv_y = can_occupy_safely(x, y, ynx, yny, gm) and ydist > 0

    # If both directions are possible, take the enemy, and then
    # the one that will pay for itself sooner.
    # Really some smarter combat object should be forcing moves here.
    if can_mv_x and can_mv_y:
        if gm.enemy[xnx, xny]:
            return xpref, xnx, xny
        if gm.enemy[ynx, yny]:
            return ypref, ynx, yny

        x_roi = gm.prod[xnx, xny] / max(1, gm.strn[xnx, xny])
        y_roi = gm.prod[ynx, yny] / max(1, gm.strn[ynx, yny])

        if x_roi > y_roi:
            return xpref, xnx, xny
        else:
            return ypref, ynx, yny

    # Only cases left are when one or no directions are possible
    if can_mv_x:
        return xpref, xnx, xny
    elif can_mv_y:
        return ypref, ynx, yny

    return 0  # Still!


def find_pref_next(x, y, nx, ny, gm):
    """Return two target x,y tuples in order of preference.
    Blocks have a bunch of heuristics to decide which of
    the <=2 possible directions is more appropriate.
    """

    # Can shortcut a lot of this if I can detect len-1 moves
    dist_north = (y - ny) % gm.height
    dist_east = (nx - x) % gm.width
    dist_south = (ny - y) % gm.height
    dist_west = (x - nx) % gm.width

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

    xnx, xny = cardinal_to_nxny(x, y, xpref, gm)
    ynx, yny = cardinal_to_nxny(x, y, ypref, gm)

    # If both cardinals are owned, prefer to move along the
    # direction with lower production.
    if gm.owned[xnx, xny] and gm.owned[ynx, yny] and \
            ydist > 0 and xdist > 0:
        if gm.prod[xnx, xny] < gm.prod[ynx, yny]:
            return (xnx, xny, xpref), (ynx, yny, ypref)
        else:
            return (ynx, yny, ypref), (xnx, xny, xpref)

    can_mv_x = can_occupy_safely(x, y, xnx, xny, gm) and xdist > 0
    can_mv_y = can_occupy_safely(x, y, ynx, yny, gm) and ydist > 0

    # If one direction is owned, move along it
    if gm.owned[xnx, xny] and xdist > 0 and can_mv_y:
        return (xnx, xny, xpref), (ynx, yny, ypref)
    if gm.owned[ynx, yny] and ydist > 0 and can_mv_x:
        return (ynx, yny, ypref), (xnx, xny, xpref)

    if gm.owned[xnx, xny] and xdist > 0:
        return (xnx, xny, xpref), (None, None, None)
    if gm.owned[ynx, yny] and ydist > 0:
        return (ynx, yny, ypref), (None, None, None)

    # If both directions are possible, take the enemy, and then
    # the one that will pay for itself sooner.
    # Really some smarter combat object should be forcing moves here.
    if can_mv_x and can_mv_y:
        if gm.enemy[xnx, xny]:
            return (xnx, xny, xpref), (ynx, yny, ypref)
        if gm.enemy[ynx, yny]:
            return (ynx, yny, ypref), (xnx, xny, xpref)

        x_roi = gm.prodc[xnx, xny] / gm.strnc[xnx, xny]
        y_roi = gm.prodc[ynx, yny] / gm.strnc[ynx, yny]

        if x_roi > y_roi:
            return (xnx, xny, xpref), (ynx, yny, ypref)
        else:
            return (ynx, yny, ypref), (xnx, xny, xpref)

    # Only cases left are when one or no directions are possible
    if can_mv_x:
        return (xnx, xny, xpref), (None, None, None)
    elif can_mv_y:
        return (ynx, yny, ypref), (None, None, None)

    return (x, y, 0), (None, None, None)


def can_occupy_safely(x, y, nx, ny, gm):
    if gm.owned[nx, ny]:
        return True

    if gm.strn[x, y] >= 255:
        return True

    if gm.strn[nx, ny] < gm.strn[x, y]:
        return True

    return False


def cardinal_to_nxny(x, y, cardinal, gm):
    if cardinal == 1:
        return x, (y - 1) % gm.height
    elif cardinal == 2:
        return (x + 1) % gm.width, y
    elif cardinal == 3:
        return x, (y + 1) % gm.height
    elif cardinal == 4:
        return (x - 1) % gm.width, y
    return x, y



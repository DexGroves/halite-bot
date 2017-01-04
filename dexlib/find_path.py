def find_path(x, y, nx, ny, gm):
    if gm.strn[x, y] <= (gm.prod[x, y] * 5):  # Min wait is here
        return 0

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

    # Don't jitter from faraway activity. Be steadfast.
    if (ydist > 0) and xdist > (5 * ydist):
        ydist = 0
    if (xdist > 0) and ydist > (5 * xdist):
        xdist = 0

    if gm.owned[xnx, xny] and gm.owned[ynx, yny] and \
            ydist > 0 and xdist > 0:
        if gm.prod[xnx, xny] < gm.prod[ynx, yny]:
            return xpref
        else:
            return ypref

    if (x + y) % 2 == 0:
        if xdist > 0 and gm.owned[xnx, xny] == 1:
            return xpref
        elif ydist > 0 and gm.owned[ynx, yny] == 1:
            return ypref

        if xdist > 0 and can_occupy_safely(x, y, xnx, xny, gm) == 1:
            return xpref
        elif ydist > 0 and can_occupy_safely(x, y, ynx, yny, gm) == 1:
            return ypref
        else:
            return 0
    else:
        if ydist > 0 and gm.owned[ynx, yny]:
            return ypref
        elif xdist > 0 and gm.owned[xnx, xny]:
            return xpref

        if ydist > 0 and can_occupy_safely(x, y, ynx, yny, gm) == 1:
            return ypref
        elif xdist > 0 and can_occupy_safely(x, y, xnx, xny, gm) == 1:
            return xpref
        else:
            return 0


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

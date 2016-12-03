import itertools
import numpy as np
from scipy.sparse import dok_matrix
from scipy.sparse.csgraph import dijkstra


class DijkstraPather(object):
    """Parent class for other Dijkstra pathers."""

    def get_dist(self, costs):
        """Set the x*y distance matrix."""
        dist = dok_matrix((self.w * self.h, self.w * self.h), dtype=int)

        for x, y in self.vertices:
            nbrs = self.get_neighbours_and_costs(x, y, costs)
            orig_i = self.get_vertex(x, y)

            for (nx, ny), cost in nbrs.items():
                targ_i = self.get_vertex(nx, ny)
                dist[orig_i, targ_i] = cost

        return dist

    def get_neighbours_and_costs(self, x, y, costs):
        """Return a dictionary of the neighbours and cost of x, y."""
        neighbours = [((x + 1) % self.w, y), ((x - 1) % self.w, y),
                      (x, (y + 1) % self.h), (x, (y - 1) % self.h)]
        return {(nx, ny): costs[nx, ny] for (nx, ny) in neighbours}

    def get_vertex(self, x, y):
        """Return the index of vertices containing the pt x, y."""
        return (x * self.h) + y


class InternalPather(DijkstraPather):
    """Handle movement internally trying to minimise production wastage."""

    def __init__(self, prod, mine, brdr, prod_lim=64):
        # Can consider setting harder searches for smaller maps.
        self.mine_prod = self.get_mine_prod(mine, prod)
        self.prod_lim = prod_lim

        self.w, self.h = prod.shape
        self.vertices = list(itertools.product(range(self.w), range(self.h)))
        self.dist = self.get_dist(self.mine_prod)

        self.path_dist, self.route = dijkstra(self.dist, False, limit=prod_lim,
                                              return_predecessors=True)

        self.prior_brdr = brdr

    def update(self, prod, mine, brdr):
        """Recompute distances and (niamhly) update self.path for a
        set of changed vertices.
        """
        self.mine_prod = self.get_mine_prod(mine, prod)
        self.dist = self.get_dist(self.mine_prod)
        d_brdr = np.transpose(np.nonzero(self.prior_brdr - brdr))

        vis = [self.get_vertex(x, y) for (x, y) in d_brdr]
        self.path_dist[vis], self.route[vis] = \
            dijkstra(self.dist, False, indices=vis, limit=self.prod_lim,
                     return_predecessors=True)

        self.prior_brdr = brdr

    def get_mine_prod(self, mine, prod):
        mine_prod = np.zeros_like(prod)
        mine_prod.fill(255)
        mine_prod[np.nonzero(mine)] = prod[np.nonzero(mine)]
        return mine_prod

    def get_path_cost(self, x, y, nx, ny):
        vo = self.get_vertex(x, y)
        vd = self.get_vertex(nx, ny)
        return self.path_dist[vd, vo]

    def get_path_step(self, x, y, nx, ny):
        vo = self.get_vertex(x, y)
        vd = self.get_vertex(nx, ny)
        next_node = self.route[vd, vo]
        if next_node == -9999:
            return x, y
        return self.vertices[next_node]


class StrPather(DijkstraPather):
    """Calculate shortest paths about the place.
    Too slow to update fully each iteration, so will only be updated in part.
    Might be worth upgrading to Anytime Dynamic A* since it seems to
    solve this problem exactly.
    """

    def __init__(self, strn, prod, strn_lim=4000):
        # Can consider setting harder searches for smaller maps.
        self.prod_vec = prod.flatten()
        self.strn_lim = strn_lim

        self.w, self.h = strn.shape
        self.vertices = itertools.product(range(self.w), range(self.h))

        self.dist = self.get_dist(strn)
        self.path = dijkstra(self.dist, False, limit=strn_lim)

        self.prior_strn = strn

    def update(self, strn, mine):
        """Recompute distances and (niamhly) update self.path for a
        set of changed vertices. Maybe it's fairer to search over vertices
        randomly when compute is limited.
        """
        self.dist = self.get_dist(strn)
        d_strn = np.transpose(np.nonzero(self.prior_strn - strn))

        vis = [self.get_vertex(x, y) for (x, y) in d_strn]
        self.path[vis] = dijkstra(self.dist, False, indices=vis,
                                  limit=self.strn_lim)

        self.reach = self.get_reach(mine)
        self.prior_strn = strn

    def get_reach(self, mine):
        owned_vi = np.nonzero(mine.flatten())
        global_reach = np.apply_along_axis(np.min, 0, self.path[owned_vi])
        global_reach[global_reach == 0] = 0.01
        return global_reach

    def update_path_acquisition(self, x, y):
        """Niamhly update the path for one, hypothetical block acquisition."""
        # Mock the strn in place
        orig_strn = self.prior_strn[x, y]
        self.prior_strn[x, y] = 0
        hypo_dist = self.get_dist(self.prior_strn)
        self.prior_strn[x, y] = orig_strn

        return dijkstra(hypo_dist, False, indices=self.get_vertex(x, y),
                        limit=self.strn_lim)

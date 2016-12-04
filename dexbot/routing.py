import itertools
import numpy as np
import random
from scipy.sparse import dok_matrix
from scipy.sparse.csgraph import dijkstra


class DijkstraPather(object):
    """Parent class for other Dijkstra pathers."""
    def get_vertex(self, x, y):
        """Return the index of vertices containing the pt x, y."""
        return (x * self.h) + y


class AllPather(DijkstraPather):
    """Calculate shortest paths about the place.
    Too slow to update fully each iteration, so will only be updated in part.
    Might be worth upgrading to Anytime Dynamic A* since it seems to
    solve this problem exactly.
    """
    def __init__(self, mprod, estrn, lim, budget=1000):
        """Give it blank strn and mine prod yo."""
        # Can consider setting harder searches for smaller maps.
        self.budget = budget

        self.w, self.h = mprod.shape
        self.vertices = list(itertools.product(range(self.w), range(self.h)))

        self.dist = self._get_dist(mprod, estrn)
        self.path, self.route = dijkstra(self.dist, False, limit=lim,
                                         return_predecessors=True)

    def update(self, mprod, estrn, brdr, lim):
        """Recompute distances and (niamhly) update self.path for a
        set of changed vertices.
        """
        self.dist = self._get_dist(mprod, estrn)

        vis = [self.get_vertex(x, y) for (x, y) in
               np.transpose(np.nonzero(brdr))]

        if len(vis) > self.budget:
            vis = random.sample(vis, self.budget)

        self.path[vis], self.route[vis] = \
            dijkstra(self.dist, False, indices=vis, limit=lim,
                     return_predecessors=True)

    def update_xy(self, x, y, lim):
        """Recompute distances and (niamhly) update self.path for a
        set of changed vertices. Assumes self.dist is right.
        """
        vi = self.get_vertex(x, y)
        self.path[vi], self.route[vi] = \
            dijkstra(self.dist, False, indices=vi, limit=lim,
                     return_predecessors=True)

    def get_movement_costs(self, x, y):
        vi = self.get_vertex(x, y)
        return np.reshape(self.path[:, vi], (self.w, self.h))

    def get_path_step(self, x, y, tx, ty):
        path = self.reconstruct_path(x, y, tx, ty)
        if len(path) < 2:  # I understand how zero, but not how 1
            return tx, ty   # You're on your own bro
        return self.vertices[path[-2]]

    def reconstruct_path(self, x, y, tx, ty):
        vo = self.get_vertex(x, y)
        vd = self.get_vertex(tx, ty)
        nodes = []
        while vd != vo:
            if vd == -9999:
                return []
            nodes.append(vd)
            vd = self.route[vo, vd]
        return nodes

    def _get_dist(self, mprod, estrn):
        """Set the x*y distance matrix."""
        dist = dok_matrix((self.w * self.h, self.w * self.h), dtype=int)

        for x, y in self.vertices:
            nbrs = self._get_neighbours_and_costs(x, y, mprod, estrn)
            orig_i = self.get_vertex(x, y)

            for (nx, ny), cost in nbrs.items():
                targ_i = self.get_vertex(nx, ny)
                dist[orig_i, targ_i] = cost

        return dist

    def _get_neighbours_and_costs(self, x, y, mprod, estrn):
        """Return a dictionary of the neighbours and cost of x, y."""
        neighbours = [((x + 1) % self.w, y), ((x - 1) % self.w, y),
                      (x, (y + 1) % self.h), (x, (y - 1) % self.h)]
        # The strn of the to-block and the prod of the from-block
        return {(nx, ny): estrn[nx, ny] + mprod[x, y]
                for (nx, ny) in neighbours}

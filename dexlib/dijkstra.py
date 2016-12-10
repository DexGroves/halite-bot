"""Logic for working out shortest-path style things."""


import itertools
import numpy as np
from scipy.sparse import dok_matrix
from scipy.sparse.csgraph import dijkstra


class ShortestPather:
    """Calculate 4D shortest paths matrix.
    Very expensive, so probably an up-front in init one-and-done deal.
    """

    def __init__(self, costs):
        self.w, self.h = costs.shape
        self.vertices = list(itertools.product(range(self.w), range(self.h)))

        self.dist = self._get_dist_graph(costs)
        self.path, self.route = dijkstra(self.dist, False,
                                         return_predecessors=True)

    def _get_dist_graph(self, costs):
        """Get the v*v distance graph."""
        dist = dok_matrix((self.w * self.h, self.w * self.h), dtype=int)

        for x, y in self.vertices:
            nbrs = self._get_nbrs_and_costs(x, y, costs)
            orig_i = self._get_vertex(x, y)

            for (nx, ny), cost in nbrs.items():
                targ_i = self._get_vertex(nx, ny)
                dist[orig_i, targ_i] = cost

        return dist

    def get_dist_matrix(self):
        """Get the x*y*x*y matrix of shortest path lengths."""
        dist_mat = np.zeros((self.w, self.h, self.w, self.h))
        for x in range(self.w):
            for y in range(self.h):
                vertex = self._get_vertex(x, y)
                dist_mat[x, y, :, :] = self.path[vertex].reshape((self.w, self.h))

        return dist_mat

    def _get_nbrs_and_costs(self, x, y, costs):
        """Return a dictionary of the neighbours and cost of x, y."""
        neighbours = [((x + 1) % self.w, y), ((x - 1) % self.w, y),
                      (x, (y + 1) % self.h), (x, (y - 1) % self.h)]
        # The strn of the to-block and the prod of the from-block
        return {(nx, ny): costs[nx, ny] for (nx, ny) in neighbours}

    def _get_vertex(self, x, y):
        """Return the index of vertices containing the pt x, y."""
        return (x * self.h) + y

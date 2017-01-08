"""Logic for working out shortest-path style things."""


import itertools
import numpy as np
from scipy.sparse import dok_matrix
from scipy.sparse.csgraph import dijkstra
# import logging
# logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


class ShortestPather:
    """Calculate 4D shortest paths matrix.
    Very expensive, so probably an up-front in init one-and-done deal.
    """

    def __init__(self, strn, prod):
        self.w, self.h = strn.shape
        self.vertices = list(itertools.product(range(self.w), range(self.h)))

        self.dist = self._get_dist_graph(strn, prod)
        self.path, self.route = dijkstra(self.dist, False,
                                         return_predecessors=True)

    def _get_dist_graph(self, strn, prod):
        """Get the v*v distance graph."""
        dist = dok_matrix((self.w * self.h, self.w * self.h), dtype=int)

        for x, y in self.vertices:
            nbrs = self._get_nbrs(x, y)
            orig_i = self.get_vertex(x, y)

            for nx, ny in nbrs:
                targ_i = self.get_vertex(nx, ny)
                dist[orig_i, targ_i] = strn[nx, ny] / (prod[x, y] + 0.1)  # Thin air 2

        return dist

    def get_dist_matrix(self):
        """Get the x*y*x*y matrix of shortest path lengths."""
        dist_mat = np.zeros((self.w, self.h, self.w, self.h))
        for x in range(self.w):
            for y in range(self.h):
                vertex = self.get_vertex(x, y)
                dist_mat[x, y, :, :] = self.path[vertex].reshape((self.w, self.h))

        return dist_mat

    def _get_nbrs(self, x, y):
        """Return a dictionary of the neighbours and cost of x, y."""
        neighbours = [((x + 1) % self.w, y), ((x - 1) % self.w, y),
                      (x, (y + 1) % self.h), (x, (y - 1) % self.h)]
        return neighbours

    def get_vertex(self, x, y):
        """Return the index of vertices containing the pt x, y."""
        return (x * self.h) + y

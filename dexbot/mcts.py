import itertools
import numpy as np
import time


class MCTSApi(object):
    """Expose MCTS moves."""
    def __init__(self, ms):
        self.graph = MapGraph(ms.prod, ms.strn)
        Tree.set_map(self.graph)

        self.startxy = ms.get_self_locs()[0]
        self.startv = self.graph.get_vertex(*self.startxy)

        self.tree = Node(self.startv)
        self.dora = MCTSExplorer(6, 1, ms.prod.shape[0] * ms.prod.shape[1])

        self.nowned = 1

        print('\n', file=open('debug.txt', 'w'))

    def think(self, nsec):
        start_time = time.time()
        while time.time() - start_time < nsec:
            for rep in range(10):
                self.dora.explore(self.tree)

    def update(self, ms, turn):
        if np.sum(ms.mine) > self.nowned:
            self.nowned += 1
            vals = self.tree.child_values
            next_i = np.argmax(vals)
            self.tree = self.tree.children[next_i]

            all_nbrs = [self.graph.get_vertex(x, y) for x, y in ms.border_locs] + [self.startv]
            members = [self.graph.get_vertex(x, y) for x, y in ms.get_self_locs()]
            capacity = np.sum(np.multiply(ms.mine, ms.prod))
            self.tree = Node(self.startv, members, all_nbrs, capacity, turn)

    def get_target(self, ms):
        owned = ms.get_self_locs()
        owned = [(o[0], o[1]) for o in owned]
        path = [self.graph.vertices[v]
                for v in self.tree.reconstruct_best().members]
        print(path, file=open('debug.txt', 'a'))
        path = [p for p in path if p not in owned]
        return path[0]

    def get_closest_target(self, x, y, ms):
        vals = np.zeros(len(self.tree.full_nbrs), dtype=float)
        for i, v in enumerate(self.tree.full_nbrs):
            bx, by = self.graph.vertices[v]
            node_val = self.tree.child_values[i]
            dist = ms.base_dist[x, y, bx, by]
            vals[i] = node_val / dist
        return self.graph.vertices[np.argmax(vals)]


class MapGraph(object):
    """Processes and holds the graph of strn and prod for a map."""
    def __init__(self, prod, strn):
        self.w, self.h = prod.shape
        self.vertices = list(itertools.product(range(self.w), range(self.h)))
        self.prod = prod.flatten()
        self.strn = strn.flatten()

        self.nbrs = {vi: self.get_neighbours(vi)
                     for vi, _ in enumerate(self.vertices)}

    def get_neighbours(self, vi):
        """Get a list of the self.vertices indices that neighbour vi."""
        x, y = self.vertices[vi]
        nbrs_xy = [((x + 1) % self.w, y),
                   ((x - 1) % self.w, y),
                   (x, (y + 1) % self.h),
                   (x, (y - 1) % self.h)]
        return [self.get_vertex(nx, ny) for (nx, ny) in nbrs_xy]

    def get_vertex(self, x, y):
        return (x * self.h) + y


class Tree(object):
    """Hold the map of all moves, and all unexplored nodes."""
    @classmethod
    def set_map(cls, graph):
        """Set the global map status from an input MapGraph."""
        cls.graph = graph


class Node(Tree):
    """A decision point in the Monte Carlo tree."""
    def __init__(self, vi, members=[], full_nbrs=[], cum_prod=0, clock=1):
        self.vi = vi                # Vertex id
        self.times_expld = 1        # Number of times explored
        self.cum_prod = cum_prod + self.graph.prod[self.vi]

        self.clock = clock
        self.members = members + [self.vi]
        self.own_nbrs = [n for n in self.graph.nbrs[self.vi]
                         if n not in self.members]
        self.full_nbrs = list(set(full_nbrs + self.own_nbrs))

        # If I was passed neighbours, then I'm in them
        if len(full_nbrs) > 0:
            self.full_nbrs.remove(vi)

        self.child_values = self.get_child_values()
        self.child_srches = np.zeros_like(self.child_values)
        self.child_srches.fill(1)

        self.children = None

        self.intr_value = self.cum_prod / self.clock
        self.srch_value = 0

    def __repr__(self):
        repr_ = '\n'.join([
            '\nMCTS Node object.',
            'xy\'s:\t\t' + repr([self.graph.vertices[x] for x in self.members]),
            'Members:\t' + repr(self.members),
            'Nbrs\t\t' + repr(self.full_nbrs),
            'Clock:\t\t' + repr(self.clock),
            'Cum_prod:\t' + repr(self.cum_prod),
            'Intr. Value:\t' + repr(self.intr_value),
            'Srch Value:\t' + repr(self.srch_value),
            'Times expl\'d:\t' + repr(self.times_expld)
        ])
        return repr_

    def set_children(self):
        self.children = [
            Node(ni, self.members, self.full_nbrs, self.cum_prod,
                 (self.clock + (self.graph.strn[ni] / self.cum_prod)))
            for ni in self.full_nbrs
        ]

    def get_child_values(self):
        vals = [(self.cum_prod + self.graph.prod[ni]) /
                (self.clock + (self.graph.strn[ni] / self.cum_prod))
                for ni in self.full_nbrs]
        return np.array(vals)

    def update_value(self, i, newval):
        """Overwrite srch_value with newval if it is higher."""
        self.child_values[i] = max(newval, self.child_values[i])

    def reconstruct_best(self, tree=None):
        """Get the best solution to a tree."""
        if tree is None:
            tree = self

        if tree.children is None:
            return tree

        best = np.argmax(self.child_values)
        return tree.reconstruct_best(tree.children[best])


class MCTSExplorer(object):
    """Orchestrate the state space exploration!"""
    def __init__(self, max_depth, explore_wt, num_verts):
        self.max_depth = max_depth
        self.explore_wt = explore_wt
        # Times explored is at a vertex level
        self.times_explored = np.zeros(num_verts, dtype=int)
        self.times_explored.fill(1)

    def explore(self, tree, depth=0):
        if tree.children is None:
            tree.set_children()

        if depth == self.max_depth:
            return tree.child_values.max()

        # Calculate the probability of searching each node based on UCT
        values = tree.child_values
        values = values / np.std(values)
        times_explds = self.times_explored[tree.full_nbrs]

        p_explore = values + \
            self.explore_wt * np.sqrt(np.log(times_explds.sum()) / times_explds)
        p_explore = p_explore / p_explore.sum()

        # Recurse down down down!
        expl_i = np.random.choice(range(len(tree.children)), p=p_explore)

        self.times_explored[tree.children[expl_i].vi] += 1
        mcts_value = self.explore(tree.children[expl_i], depth=depth + 1)

        # Update this node, and return srch_val to update nodes up the chain
        tree.update_value(expl_i, mcts_value)
        return mcts_value

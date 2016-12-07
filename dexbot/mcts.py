import itertools
import numpy as np
import time
from copy import copy


class MCTSApi(object):
    """Expose MCTS moves."""
    def __init__(self, ms):
        self.graph = MapGraph(ms.prod, ms.strn)
        Tree.set_map(self.graph)

        self.startxy = ms.get_self_locs()[0]
        self.startv = self.graph.get_vertex(*self.startxy)

        self.state = State([self.startv])
        self.tree = Node(self.startv)
        self.dora = Explorer(0.1, 12, self.state)

        self.nowned = 1

        print('\n', file=open('debug.txt', 'w'))

    def think(self, nsec):
        start_time = time.time()
        while time.time() - start_time < nsec:
            for rep in range(10):
                self.dora.explore(self.tree)
        self.soln = [self.graph.vertices[v] for v in reconstruct(self.tree)]
        print(self.soln, file=open('debug.txt', 'a'))
        print([(child.vi, child.value, child.visits) for child in self.tree.children],
              file=open('debug.txt', 'a'))

    def set_depth(self, newdepth):
        self.dora.depth = newdepth

    def update(self, ms, turn):
        if np.sum(ms.mine) - self.nowned != 1:
            # Completely restart the state
            self.state = State([self.graph.get_vertex(x, y)
                                for (x, y) in ms.get_self_locs()])
            self.tree = Node(self.startv)
            self.tree.children = [Node(self.graph.get_vertex(nx, ny))
                                  for nx, ny in ms.border_locs]
            self.nowned = np.sum(ms.mine)

        self.set_target_matrix(ms)

    def set_target_matrix(self, ms):
        self.tmat = np.zeros_like(ms.prod)
        for i, (x, y) in enumerate(self.soln):
            self.tmat[x, y] = 1

    def get_best_target(self, x, y, ms):
        strn_bonus = 1
        prox_val = np.divide(np.multiply(self.tmat, strn_bonus),
                             ms.base_dist[x, y, :, :])
        prox_val[x, y] = 0
        prox_val[np.nonzero(ms.mine)] = 0
        print(np.unravel_index(prox_val.argmax(), prox_val.shape), file=open('debug.txt', 'a'))
        return np.unravel_index(prox_val.argmax(), prox_val.shape)


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


class State(Tree):
    """A manipulable, disposable representation of the board that nodes use."""
    def __init__(self, members):
        self.members = members

    def add_member(self, member):
        self.members.append(member)

    def get_value(self, depth):
        # prod_sum = np.sum([self.graph.prod[vi] for vi in self.members[-depth:]])
        # strn_sum = np.sum([self.graph.strn[vi] for vi in self.members[-depth:]])
        prod_sum = np.sum([self.graph.prod[vi] for vi in self.members])
        strn_sum = np.sum([self.graph.strn[vi] for vi in self.members])
        return prod_sum / strn_sum

    def clone(self):
        return State(copy(self.members))


class Node(object):
    def __init__(self, vi):
        self.vi = vi
        self.visits = 0.001  # Small number so no infs later
        self.value = 0
        self.children = None

    def set_children(self, children):
        self.children = children

    def update_value(self, newval):
        self.value = ((self.visits / (self.visits + 1)) * self.value) + \
            newval / (self.visits + 1)
        self.visits += 1


class Explorer(object):
    """MCTS Explorer."""
    def __init__(self, expl_wt, maxdepth, state):
        self.expl_wt = expl_wt
        self.maxdepth = maxdepth
        self.true_state = copy(state)

    def explore(self, tree, state=None, depth=0):
        if state is None:
            state = self.true_state.clone()

        if depth == self.maxdepth:
            return state.get_value(self.maxdepth)

        if tree.children is None:
            tree.set_children([Node(ni) for ni in state.graph.nbrs[tree.vi]
                               if ni not in state.members])

        if len(tree.children) == 0:
            return 0

        values = np.array([child.value for child in tree.children])
        visits = np.array([child.visits for child in tree.children])

        p_explore = values + \
            self.expl_wt * np.sqrt(np.log(max(visits.sum(), 1.0001)) / visits)
        p_explore = p_explore / p_explore.sum()

        chosen_child = np.random.choice(tree.children, p=p_explore)
        state.add_member(chosen_child.vi)

        mcts_value = self.explore(chosen_child, state, depth=depth + 1)

        # Update this node, and return srch_val to update nodes up the chain
        chosen_child.update_value(mcts_value)
        return mcts_value


def reconstruct(tree):
    if tree.children is None:
        return [tree.vi]
    child_vals = [child.value for child in tree.children]
    i = np.argmax(child_vals)
    return [tree.vi] + reconstruct(tree.children[i])

"""Handle the logistics of teamwork to capture border areas."""


import numpy as np
import dexbot.loupes as loupes
from dexbot.move_queue import PendingMoves

class BorderOperator(object):

    def __init__(self, map_state):
        self.width = map_state.width
        self.height = map_state.height

    def set_border_value(self, map_state, appraiser):
        # self.capture_value = self.appraiser.get_value() # call in dexbot
        self.brdr_locs = map_state.get_border_locs()
        self.brdr_value = np.empty(len(self.brdr_locs), dtype=float)

        for i, (x, y) in enumerate(self.brdr_locs):
            if map_state.prod[x, y] == 0:
                self.brdr_value[i] = 0
            else:
                self.brdr_value[i] = appraiser.value_at_point(x, y)

        sort_value = np.argsort(-1 * self.brdr_value)
        self.impt_locs = [(r[0], r[1]) for r in self.brdr_locs[sort_value]]
        self.brdr_value = self.brdr_value[sort_value]

        self.impt_locs = [self.impt_locs[i] for i in range(len(self.impt_locs))
                          if self.brdr_value[i] > self.brdr_value.mean()]

    def get_moves(self, map_state):
        ic_queue = self.get_immediate_captures(self.impt_locs, map_state)

        rem_locs = [loc for loc in self.impt_locs
                    if not loc in ic_queue.locs]
        bm_queue = self.get_border_moves(rem_locs, map_state)

        return ic_queue, bm_queue

    def get_immediate_captures(self, rem_locs, map_state):
        pm = PendingMoves()

        for x, y in rem_locs:
            target_str = map_state.strn[x, y]

            if map_state.mine[(x+1) % self.width, y]:  # Has self to east
                nx, ny = (x+1) % self.width, y
                if map_state.mine_strn[nx, ny] > target_str or \
                        map_state.mine_strn[nx, ny] > 255:
                    pm.pend_move(nx, ny, 4)
                    map_state.register_move(nx, ny, 4)
                    with open('pending.txt', 'a') as f:
                        f.write('CapImmediate:\t' + repr((nx, ny)) + '\t' + repr(4) + '\n')

            elif map_state.mine[(x-1) % self.width, y]:  # Has self to west
                nx, ny = (x-1) % self.width, y
                if map_state.mine_strn[nx, ny] > target_str or \
                        map_state.mine_strn[nx, ny] > 255:
                    pm.pend_move(nx, ny, 2)
                    map_state.register_move(nx, ny, 2)
                    with open('pending.txt', 'a') as f:
                        f.write('CapImmediate:\t' + repr((nx, ny)) + '\t' + repr(2) + '\n')

            elif map_state.mine[x, (y+1) % self.height]:  # Has self to south
                nx, ny = x, (y+1) % self.height
                if map_state.mine_strn[nx, ny] > target_str or \
                        map_state.mine_strn[nx, ny] > 255:
                    pm.pend_move(nx, ny, 1)
                    map_state.register_move(nx, ny, 3)
                    with open('pending.txt', 'a') as f:
                        f.write('CapImmediate:\t' + repr((nx, ny)) + '\t' + repr(1) + '\n')

            elif map_state.mine[x, (y-1) % self.height]:  # Has self to north
                nx, ny = x, (y-1) % self.height
                if map_state.mine_strn[nx, ny] > target_str or \
                        map_state.mine_strn[nx, ny] > 255:
                    pm.pend_move(nx, ny, 3)
                    map_state.register_move(nx, ny, 1)
                    with open('pending.txt', 'a') as f:
                        f.write('CapImmediate:\t' + repr((nx, ny)) + '\t' + repr(3) + '\n')

        return pm

    def get_border_moves(self, rem_locs, map_state):
        pm = PendingMoves()

        for x, y in rem_locs:
            target_str = map_state.strn[x, y]

            if map_state.mine[(x+1) % self.width, y]:  # Has self to east
                nx, ny = (x+1) % self.width, y
                teamup_coords = (loupes.east + (x, y)) % (self.width, self.height)
                with open('tcoords.txt', 'a') as f: f.write(repr(teamup_coords) + '\n')
                total_str = 0
                for tx, ty in teamup_coords:
                    with open('tadd_value.txt', 'a') as f: f.write(repr(map_state.mine_strn[tx, ty]) + '\t')
                    total_str += map_state.mine_strn[tx, ty]
                with open('tadd_value.txt', 'a') as f: f.write("\n----\n")

                if total_str > (target_str + map_state.prod[nx, ny]):
                    for (lx, ly), cardinal in loupes.east_outer.items():
                        xlx, yly = (x+lx) % self.width, (y+ly) % self.height
                        if map_state.mine[xlx, yly]:
                            pm.pend_move(xlx, yly, cardinal)
                            map_state.register_move(xlx, yly, cardinal)
                            with open('pending.txt', 'a') as f:
                                f.write('CapConglom:\t' + repr((xlx, yly)) + '\t' +
                                        repr(cardinal) + '\t' +
                                        repr((target_str, total_str)) + '\t' +
                                        repr((x, y)) + '\n' +
                                        repr(teamup_coords) + '\n' +
                                        repr(map_state.mine_strn[teamup_coords]) + '\n' +
                                        repr(np.sum(map_state.mine_strn[teamup_coords])) + '\n'
                                        '')

            elif map_state.mine[(x-1) % self.width, y]:  # Has self to west
                nx, ny = (x-1) % self.width, y
                teamup_coords = (loupes.west + (x, y)) % (self.width, self.height)
                with open('tcoords.txt', 'a') as f: f.write(repr(teamup_coords) + '\n')
                total_str = 0
                for tx, ty in teamup_coords:
                    with open('tadd_value.txt', 'a') as f: f.write(repr(map_state.mine_strn[tx, ty]) + '\t')
                    total_str += map_state.mine_strn[tx, ty]
                with open('tadd_value.txt', 'a') as f: f.write("\n----\n")

                if total_str > (target_str + map_state.prod[nx, ny]):
                    for (lx, ly), cardinal in loupes.west_outer.items():
                        xlx, yly = (x+lx) % self.width, (y+ly) % self.height
                        if map_state.mine[xlx, yly]:
                            pm.pend_move(xlx, yly, cardinal)
                            map_state.register_move(xlx, yly, cardinal)
                            with open('pending.txt', 'a') as f:
                                f.write('CapConglom:\t' + repr((xlx, yly)) + '\t' +
                                        repr(cardinal) + '\t' +
                                        repr((target_str, total_str)) + '\t' +
                                        repr((x, y)) + '\n' +
                                        repr(teamup_coords) + '\n' +
                                        repr(map_state.mine_strn[teamup_coords]) + '\n' +
                                        repr(np.sum(map_state.mine_strn[teamup_coords])) + '\n'
                                        '')

            elif map_state.mine[x, (y+1) % self.height]:  # Has self to south
                nx, ny = x, (y+1) % self.height
                teamup_coords = (loupes.south + (x, y)) % (self.width, self.height)
                with open('tcoords.txt', 'a') as f: f.write(repr(teamup_coords) + '\n')
                total_str = 0
                for tx, ty in teamup_coords:
                    with open('tadd_value.txt', 'a') as f: f.write(repr(map_state.mine_strn[tx, ty]) + '\t')
                    total_str += map_state.mine_strn[tx, ty]
                with open('tadd_value.txt', 'a') as f: f.write("\n----\n")

                if total_str > (target_str + map_state.prod[nx, ny]):
                    for (lx, ly), cardinal in loupes.south_outer.items():
                        xlx, yly = (x+lx) % self.width, (y+ly) % self.height
                        if map_state.mine[xlx, yly]:
                            pm.pend_move(xlx, yly, cardinal)
                            map_state.register_move(xlx, yly, cardinal)
                            with open('pending.txt', 'a') as f:
                                f.write('CapConglom:\t' + repr((xlx, yly)) + '\t' +
                                        repr(cardinal) + '\t' +
                                        repr((target_str, total_str)) + '\t' +
                                        repr((x, y)) + '\n' +
                                        repr(teamup_coords) + '\n' +
                                        repr(map_state.mine_strn[teamup_coords]) + '\n' +
                                        repr(np.sum(map_state.mine_strn[teamup_coords])) + '\n'
                                        '')

            elif map_state.mine[x, (y-1) % self.height]:  # Has self to north
                nx, ny = x, (y-1) % self.height
                teamup_coords = (loupes.north + (x, y)) % (self.width, self.height)
                with open('tcoords.txt', 'a') as f: f.write(repr(teamup_coords) + '\n')
                total_str = 0
                for tx, ty in teamup_coords:
                    with open('tadd_value.txt', 'a') as f: f.write(repr(map_state.mine_strn[tx, ty]) + '\t')
                    total_str += map_state.mine_strn[tx, ty]
                with open('tadd_value.txt', 'a') as f: f.write("\n----\n")

                if total_str > (target_str + map_state.prod[nx, ny]):
                    for (lx, ly), cardinal in loupes.north_outer.items():
                        xlx, yly = (x+lx) % self.width, (y+ly) % self.height
                        if map_state.mine[xlx, yly]:
                            pm.pend_move(xlx, yly, cardinal)
                            map_state.register_move(xlx, yly, cardinal)
                            with open('pending.txt', 'a') as f:
                                f.write('CapConglom:\t' + repr((xlx, yly)) + '\t' +
                                        repr(cardinal) + '\t' +
                                        repr((target_str, total_str)) + '\t' +
                                        repr((x, y)) + '\n' +
                                        repr(teamup_coords) + '\n' +
                                        repr(map_state.mine_strn[teamup_coords]) + '\n' +
                                        repr(np.sum(map_state.mine_strn[teamup_coords])) + '\n'
                                        '')

        return pm

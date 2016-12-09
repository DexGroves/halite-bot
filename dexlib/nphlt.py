"""
A Python-based Halite starter-bot framework.
A barebones, numpy-inspired fork of erdman's hlt.py that focuses on
assembling prod, strn and owner numpy matrices as quickly as possible.
Moves are tuples of x, y and dir, where dir behaves as in the
base starter.
"""

import sys
from numpy import array, zeros
from collections import namedtuple

import logging
logging.basicConfig(filename='wtf.info', filemode="w", level=logging.DEBUG)


Move = namedtuple('Move', 'x y dir')


class GameMap:
    """Hold prod, strn and owners and update on each new frame."""

    def __init__(self, size_string, prod_string, my_id):
        self.width, self.height = tuple(map(int, size_string.split()))
        self.my_id = my_id

        prod = [int(p) for p in prod_string.split()]
        self.prod = array(prod, dtype=int).reshape((self.width, self.height))

        self.get_frame()

    def get_frame(self, map_string=None):
        if map_string is None:
            map_string = get_string()

        split_string = map_string.split()
        owners = zeros(self.width * self.height, dtype=int)

        ctr, strloc = 0, 0
        while ctr < self.width * self.height:
            increment = int(split_string[strloc])
            owner_id = int(split_string[strloc + 1])
            owners[ctr:(ctr + increment)] = owner_id
            ctr += increment
            strloc += 2
        self.owners = owners.reshape((self.width, self.height))
        logging.info(self.owners)

        strn = [int(s) for s in split_string[strloc:]]
        self.strn = array(strn, dtype=int).reshape((self.width, self.height))


def send_string(s):
    sys.stdout.write(s)
    sys.stdout.write('\n')
    sys.stdout.flush()


def get_string():
    return sys.stdin.readline().rstrip('\n')


def get_init():
    my_id = int(get_string())
    m = GameMap(get_string(), get_string(), my_id)
    return my_id, m


def send_init(name):
    send_string(name)


def send_frame(moves):
    send_string(' '.join(str(move.x) + ' ' + str(move.y) + ' ' + str(move.dir)
                         for move in moves))

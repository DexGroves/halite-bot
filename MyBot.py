import dexlib.nphlt as hlt
import logging
from dexlib.resolver import Resolver
from dexlib.movement import (
    Combatant,
    MoveMaker,
    Moveset,
    Amalgamator,
    Nonaggressor,
    Noswapper
)


logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


game_map = hlt.ImprovedGameMap(8)
hlt.send_init("DexBotNeuer")
game_map.get_frame()
game_map.update()

k = 1.5 - game_map.num_enemies * 0.1
bord_eval = MoveMaker(game_map, wait=4, glob_k=k)
combatant = Combatant(4)
resolver = Resolver(game_map)
amalgamator = Amalgamator(strlim=20)
nonaggr = Nonaggressor()
noswapper = Noswapper()


while True:
    logging.debug('TURN ------------' + str(game_map.turn))
    game_map.update()

    moveset = Moveset(game_map)
    moveset = combatant.decide_combat_moves(game_map, moveset)
    moveset = bord_eval.decide_noncombat_moves(game_map, moveset)
    # moveset = amalgamator.process_moves(game_map, moveset)
    moveset = resolver.resolve(game_map, moveset)
    # moveset = amalgamator.process_moved_into(game_map, moveset)
    moveset = nonaggr.process_moves(game_map, moveset)
    # moveset = noswapper.process_moves(game_map, moveset)

    hlt.send_frame(moveset.process_moves())
    game_map.get_frame()

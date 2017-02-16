import reflib.nphlt as hlt
import logging
from reflib.resolver import Resolver
from reflib.movement import Combatant, MoveMaker, Moveset


# logging.basicConfig(filename='wtf.info', level=logging.DEBUG, filemode="w")


game_map = hlt.ImprovedGameMap(8)
hlt.send_init("ReferenceBot")
game_map.get_frame()
game_map.update()

k = 1.5 - game_map.num_enemies * 0.1
bord_eval = MoveMaker(game_map, wait=4, glob_k=k)
combatant = Combatant(4)
resolver = Resolver(game_map)


while True:
    # logging.debug('TURN ------------' + str(game_map.turn))
    game_map.update()

    if game_map.turn < 5000:
        hlt.send_frame([])
        game_map.get_frame()
        continue

    moveset = Moveset(game_map)
    moveset = combatant.decide_combat_moves(game_map, moveset)
    moveset = bord_eval.decide_noncombat_moves(game_map, moveset)
    moveset = resolver.resolve(game_map, moveset)

    hlt.send_frame(moveset.process_moves())
    game_map.get_frame()

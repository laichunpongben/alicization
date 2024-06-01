# players/policies/max_build.py

import logging

from ..actions.battle import (
    can_place_bounty,
)
from ..actions.extension import (
    can_set_home,
)
from ..actions.investment import (
    can_collect,
    can_invest,
)
from ..actions.manufacturing import (
    can_manufacture,
)
from ..actions.material import (
    can_mine,
    can_salvage,
)
from ..actions.movement import (
    can_move_asteroid_belt,
    can_move_debris,
    can_move_moon,
    can_move_planet,
    can_move_stargate,
    can_travel,
)
from ..actions.spaceship_maintenance import (
    can_repair,
    can_upgrade,
)
from ..actions.spaceship_piloting import (
    can_load,
    can_pilot,
    can_unload,
)
from ..actions.trade import (
    can_sell,
    can_buy_material,
    can_sell_material,
    can_buy_spaceship,
)
from ...spaceships.miner import Miner
from ...spaceships.extractor import Extractor
from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def max_build_policy(player):
    action_index_probs = []
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_move_planet(current_system):
        action_index_probs.append((1, 0.1))
    if can_move_asteroid_belt(current_system):
        action_index_probs.append((2, 0.05))
    if can_move_moon(current_system):
        action_index_probs.append((3, 0.01))
    if can_move_stargate(current_system):
        action_index_probs.append((4, 0.01))
    if can_move_debris(current_system):
        action_index_probs.append((5, 0.01))
    if can_travel(current_location):
        action_index_probs.append((6, 0.01))
    if can_mine(current_location, spaceship):
        action_index_probs.append((8, 0.50))
    if can_salvage(current_location, spaceship):
        action_index_probs.append((17, 0.10))
    if can_buy_material(player, current_location):
        action_index_probs.append((10, 0.1))
    if can_sell_material(player, current_location):
        action_index_probs.append((11, 0.1))
    if can_sell(player, current_location, "corvette", 1):
        action_index_probs.append((24, 0.2))
    if can_sell(player, current_location, "frigate", 1):
        action_index_probs.append((41, 0.2))
    if can_sell(player, current_location, "destroyer", 1):
        action_index_probs.append((42, 0.2))
    if can_sell(player, current_location, "courier", 1):
        action_index_probs.append((46, 0.2))
    if can_sell(player, current_location, "miner", 1):
        action_index_probs.append((38, 0.001))
    if can_sell(player, current_location, "extractor", 1):
        action_index_probs.append((43, 0.001))
    if can_set_home(player, current_system, current_location):
        action_index_probs.append((22, 0.001))
    if can_place_bounty(player):
        action_index_probs.append((31, 0.01))
    if can_invest(player, current_location, "factory"):
        action_index_probs.append((12, 0.001))
    if can_invest(player, current_location, "drydock"):
        action_index_probs.append((32, 0.001))
    if can_invest(player, current_location, "marketplace"):
        action_index_probs.append((40, 0.001))
    if can_collect(player, current_location):
        action_index_probs.append((13, 0.001))
    if can_repair(player, current_location, spaceship):
        action_index_probs.append((15, 0.1))
    if can_upgrade(player, current_location, spaceship):
        action_index_probs.append((16, 0.03))
    if can_unload(current_location, spaceship):
        action_index_probs.append((9, 0.1))
    if can_load(player, current_location, spaceship):
        action_index_probs.append((39, 0.01))

    if can_manufacture(player, current_location, "destroyer"):
        action_index_probs.append((33, 1))
    if can_manufacture(player, current_location, "frigate"):
        action_index_probs.append((27, 0.1))
    if can_manufacture(player, current_location, "corvette"):
        action_index_probs.append((26, 0.01))
    if can_manufacture(player, current_location, "extractor"):
        action_index_probs.append((35, 0.1))
    if can_manufacture(player, current_location, "miner"):
        action_index_probs.append((25, 0.01))
    if can_manufacture(player, current_location, "courier"):
        action_index_probs.append((44, 0.001))

    if can_pilot(player, current_location, "miner") and not isinstance(
        spaceship, Extractor
    ):
        action_index_probs.append((28, 1))
    if can_pilot(player, current_location, "extractor"):
        action_index_probs.append((36, 1))

    if can_buy_spaceship(player, current_location) and not isinstance(
        spaceship, Extractor
    ):
        action_index_probs.append((50, 0.02))
    if can_buy_spaceship(player, current_location) and not isinstance(spaceship, Miner):
        action_index_probs.append((37, 0.01))

    if player.wallet < 10000:
        if isinstance(spaceship, (Miner, Extractor)):
            action_index_probs.append((14, 0.01))
        else:
            action_index_probs.append((14, 0.1))

    return action_index_probs

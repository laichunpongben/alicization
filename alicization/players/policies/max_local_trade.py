# players/policies/max_local_trade.py

import logging

from ..actions.extension import (
    can_set_home,
)
from ..actions.manufacturing import (
    can_manufacture,
)
from ..actions.missioning import (
    can_mission,
)
from ..actions.movement import (
    can_move_moon,
    can_move_planet,
    can_move_stargate,
    can_travel,
)
from ..actions.trade import (
    can_sell,
    can_buy_material,
    can_sell_material,
)
from ...spaceships.explorer import Explorer
from ...spaceships.courier import Courier
from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def max_local_trade_policy(player):
    action_index_probs = []
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    home_system = player_manager.get_home_system(player.name)
    if len(current_system.planets) != 1 or len(current_system.moons) == 0:
        if can_travel(current_location):
            action_index_probs.append((6, 1))
        if can_move_stargate(current_system):
            action_index_probs.append((4, 0.1))
    else:
        if (
            can_set_home(player, current_system, current_location)
            and current_system != home_system
        ):
            action_index_probs.append((22, 1))
        if can_move_planet(current_system):
            action_index_probs.append((1, 0.1))
        if can_move_moon(current_system):
            action_index_probs.append((3, 0.1))
        if can_mission(current_location) and isinstance(spaceship, (Explorer, Courier)):
            action_index_probs.append((14, 0.1))

        # trade
        if can_buy_material(player, current_location):
            action_index_probs.append((51, 0.05))
        if can_sell_material(player, current_location):
            action_index_probs.append((52, 0.05))
        if can_manufacture(player, current_location, "corvette"):
            action_index_probs.append((26, 1))
        if can_sell(player, current_location, "corvette", 1):
            action_index_probs.append((24, 1))
    return action_index_probs

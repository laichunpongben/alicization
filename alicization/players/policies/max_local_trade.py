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
from ..policies.action_map import ACTION_INDEX_MAP
from ..enums.action import Action
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
            action_index_probs.append((ACTION_INDEX_MAP[Action.TRAVEL.value], 1))
        if can_move_stargate(current_system):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.MOVE_STARGATE.value], 0.1)
            )
    else:
        if (
            can_set_home(player, current_system, current_location)
            and current_system != home_system
        ):
            action_index_probs.append((ACTION_INDEX_MAP[Action.SET_HOME.value], 1))
        if can_move_planet(current_system):
            action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_PLANET.value], 0.1))
        if can_move_moon(current_system):
            action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_MOON.value], 0.1))
        if can_mission(current_location) and isinstance(spaceship, (Explorer, Courier)):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.EASY_MISSION.value], 0.1)
            )

        # trade
        if can_buy_material(player, current_location):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.BUY_MATERIAL_LOW.value], 0.05)
            )
        if can_sell_material(player, current_location):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.SELL_MATERIAL_HIGH.value], 0.05)
            )
        if can_manufacture(player, current_location, "corvette"):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.BUILD_CORVETTE.value], 1)
            )
        if can_sell(player, current_location, "corvette", 1):
            action_index_probs.append((ACTION_INDEX_MAP[Action.SELL_CORVETTE.value], 1))
    return action_index_probs

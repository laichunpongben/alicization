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
from ..policies.action_map import ACTION_INDEX_MAP
from ..enums.action import Action
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
        action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_PLANET.value], 0.1))
    if can_move_asteroid_belt(current_system):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.MOVE_ASTEROID_BELT.value], 0.05)
        )
    if can_move_moon(current_system):
        action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_MOON.value], 0.01))
    if can_move_stargate(current_system):
        action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_STARGATE.value], 0.01))
    if can_move_debris(current_system):
        action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_DEBRIS.value], 0.01))
    if can_travel(current_location):
        action_index_probs.append((ACTION_INDEX_MAP[Action.TRAVEL.value], 0.01))
    if can_mine(current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.MINE.value], 0.50))
    if can_salvage(current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SALVAGE.value], 0.10))
    if can_buy_material(player, current_location):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY.value], 0.1))
    if can_sell_material(player, current_location):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL.value], 0.1))
    if can_sell(player, current_location, "corvette", 1):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL_CORVETTE.value], 0.2))
    if can_sell(player, current_location, "frigate", 1):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL_FRIGATE.value], 0.2))
    if can_sell(player, current_location, "destroyer", 1):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL_DESTROYER.value], 0.2))
    if can_sell(player, current_location, "courier", 1):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL_COURIER.value], 0.2))
    if can_sell(player, current_location, "miner", 1):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL_MINER.value], 0.001))
    if can_sell(player, current_location, "extractor", 1):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.SELL_EXTRACTOR.value], 0.001)
        )
    if can_set_home(player, current_system, current_location):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SET_HOME.value], 0.001))
    if can_place_bounty(player):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PLACE_BOUNTY.value], 0.01))
    if can_invest(player, current_location, "factory"):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.INVEST_FACTORY.value], 0.001)
        )
    if can_invest(player, current_location, "drydock"):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.INVEST_DRYDOCK.value], 0.001)
        )
    if can_invest(player, current_location, "marketplace"):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.INVEST_MARKETPLACE.value], 0.001)
        )
    if can_collect(player, current_location):
        action_index_probs.append((ACTION_INDEX_MAP[Action.COLLECT.value], 0.001))
    if can_repair(player, current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.REPAIR.value], 0.1))
    if can_upgrade(player, current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.UPGRADE.value], 0.03))
    if can_unload(current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.UNLOAD.value], 0.1))
    if can_load(player, current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.LOAD.value], 0.01))

    if can_manufacture(player, current_location, "destroyer"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUILD_DESTROYER.value], 1))
    if can_manufacture(player, current_location, "frigate"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUILD_FRIGATE.value], 0.1))
    if can_manufacture(player, current_location, "corvette"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUILD_CORVETTE.value], 0.01))
    if can_manufacture(player, current_location, "extractor"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUILD_EXTRACTOR.value], 0.1))
    if can_manufacture(player, current_location, "miner"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUILD_MINER.value], 0.01))
    if can_manufacture(player, current_location, "courier"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUILD_COURIER.value], 0.001))

    if can_pilot(player, current_location, "miner") and not isinstance(
        spaceship, Extractor
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PILOT_MINER.value], 1))
    if can_pilot(player, current_location, "extractor"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PILOT_EXTRACTOR.value], 1))

    if can_buy_spaceship(player, current_location) and not isinstance(
        spaceship, Extractor
    ):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.BUILD_EXTRACTOR.value], 0.02)
        )
    if can_buy_spaceship(player, current_location) and not isinstance(spaceship, Miner):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY_MINER.value], 0.01))

    if player.wallet < 10000:
        if isinstance(spaceship, (Miner, Extractor)):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.EASY_MISSION.value], 0.01)
            )
        else:
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.EASY_MISSION.value], 0.1)
            )

    return action_index_probs

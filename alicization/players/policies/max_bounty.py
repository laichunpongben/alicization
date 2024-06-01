# players/policies/max_bounty.py

import math
import logging

from ..actions.battle import (
    can_attack,
)
from ..actions.investment import (
    can_collect,
    can_invest,
)
from ..actions.material import (
    can_mine,
    can_salvage,
)
from ..actions.missioning import (
    can_mission,
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
    can_sell_material,
    can_buy_spaceship,
)
from ..policies.action_map import ACTION_INDEX_MAP
from ..enums.action import Action
from ...spaceships.explorer import Explorer
from ...spaceships.miner import Miner
from ...spaceships.extractor import Extractor
from ...spaceships.corvette import Corvette
from ...spaceships.frigate import Frigate
from ...spaceships.destroyer import Destroyer
from ...spaceships.courier import Courier
from ...managers.leaderboard import Leaderboard
from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()
leaderboard = Leaderboard()


def max_bounty_policy(player):
    action_index_probs = []
    universe = player_manager.get_universe(player.name)
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_repair(player, current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.REPAIR.value], 0.1))
    if can_upgrade(player, current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.UPGRADE.value], 0.03))
    if can_move_planet(current_system):
        action_index_probs.append((ACTION_INDEX_MAP[Action.MOVE_PLANET.value], 0.1))
    if can_move_asteroid_belt(current_system):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.MOVE_ASTEROID_BELT.value], 0.01)
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
        action_index_probs.append((ACTION_INDEX_MAP[Action.MINE.value], 0.2))
    if can_salvage(current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SALVAGE.value], 0.10))
    if can_unload(current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.UNLOAD.value], 0.01))
    if can_load(player, current_location, spaceship):
        action_index_probs.append((ACTION_INDEX_MAP[Action.LOAD.value], 0.001))
    if can_sell_material(player, current_location):
        action_index_probs.append((ACTION_INDEX_MAP[Action.SELL.value], 0.4))
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

    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 3500000
        and not isinstance(spaceship, Destroyer)
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY_DESTROYER.value], 0.2))
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 70000
        and not isinstance(spaceship, Frigate)
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY_FRIGATE.value], 0.4))
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 1400
        and not isinstance(spaceship, Corvette)
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY_CORVETTE.value], 0.2))
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 1400
        and not isinstance(spaceship, Courier)
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY_COURIER.value], 0.1))

    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 35000
        and not isinstance(spaceship, Extractor)
    ):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.BUY_EXTRACTOR.value], 0.0001)
        )
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 700
        and not isinstance(spaceship, Miner)
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.BUY_MINER.value], 0.0001))

    if can_pilot(player, current_location, "miner") and (
        player.wallet < 10000
        or (
            not can_pilot(player, current_location, "corvette")
            and not isinstance(spaceship, Corvette)
        )
    ):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PILOT_MINER.value], 0.01))

    if can_pilot(player, current_location, "extractor") and (
        player.wallet < 10000
        or (
            not can_pilot(player, current_location, "corvette")
            and not isinstance(spaceship, Corvette)
        )
    ):
        action_index_probs.append(
            (ACTION_INDEX_MAP[Action.PILOT_EXTRACTOR.value], 0.02)
        )

    if can_pilot(player, current_location, "corvette"):
        if (isinstance(spaceship, (Explorer, Miner, Courier))) or (
            isinstance(spaceship, (Frigate, Destroyer))
            and spaceship.is_damaged()
            and player.wallet <= spaceship.calc_repair_cost()
        ):
            action_index_probs.append(
                (ACTION_INDEX_MAP[Action.PILOT_CORVETTE.value], 1)
            )

    if can_pilot(player, current_location, "frigate"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PILOT_FRIGATE.value], 1))
    if can_pilot(player, current_location, "destroyer"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PILOT_DESTROYER.value], 1))
    if can_pilot(player, current_location, "courier"):
        action_index_probs.append((ACTION_INDEX_MAP[Action.PILOT_COURIER.value], 0.001))

    ready_to_mission = (
        can_mission(current_location)
        and isinstance(
            spaceship,
            (Destroyer, Frigate, Corvette, Explorer, Courier),
        )
        and math.isclose(spaceship.armor, spaceship.max_armor)
        and math.isclose(spaceship.hull, spaceship.max_hull)
    )
    if ready_to_mission:
        action_index_probs.append((ACTION_INDEX_MAP[Action.EASY_MISSION.value], 0.1))

    wanteds = [x[0] for x in leaderboard.get_top_leaders("bounty", 10) if x[1] > 0]
    kill_threshold = universe.total_kill * 0.05
    killers = [
        x[0] for x in leaderboard.get_top_leaders("kill", 10) if x[1] > kill_threshold
    ]
    target_player_names = [
        player.name for player in current_location.players if player != player
    ]
    killer_match = (
        len(
            set(wanteds)
            .intersection(set(killers))
            .intersection(set(target_player_names))
        )
        > 0
    )
    if killer_match:
        logger.debug("Killer match!")
    should_police = (
        can_attack(current_location, spaceship)
        and isinstance(spaceship, (Destroyer, Frigate, Corvette))
        and math.isclose(spaceship.hull, spaceship.max_hull)
        and killer_match
    )
    if should_police:
        action_index_probs.append((ACTION_INDEX_MAP[Action.ATTACK_STRONGEST.value], 1))

    return action_index_probs

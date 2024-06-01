# players/policies/max_mission.py

import math
import logging


from ..actions.extension import (
    can_set_home,
)
from ..actions.investment import (
    can_collect,
    can_invest,
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
from ...spaceships.explorer import Explorer
from ...spaceships.miner import Miner
from ...spaceships.corvette import Corvette
from ...spaceships.frigate import Frigate
from ...spaceships.destroyer import Destroyer
from ...spaceships.courier import Courier
from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def max_mission_policy(player):
    action_index_probs = []
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_repair(player, current_location, spaceship):
        action_index_probs.append((15, 0.1))
    if can_upgrade(player, current_location, spaceship):
        action_index_probs.append((16, 0.03))
    if can_move_planet(current_system):
        action_index_probs.append((1, 0.05))
    if can_move_moon(current_system):
        action_index_probs.append((3, 0.1))
    if can_move_stargate(current_system):
        action_index_probs.append((4, 0.01))
    if can_travel(current_location):
        if can_move_moon(current_system):
            action_index_probs.append((6, 0.01))
        else:
            action_index_probs.append((6, 1))
    if can_unload(current_location, spaceship):
        action_index_probs.append((9, 0.01))
    if can_load(player, current_location, spaceship):
        action_index_probs.append((39, 0.001))
    if can_sell_material(player, current_location):
        action_index_probs.append((11, 0.2))
    if can_set_home(player, current_system, current_location):
        action_index_probs.append((22, 0.001))
    if can_invest(player, current_location, "factory"):
        action_index_probs.append((12, 0.001))
    if can_invest(player, current_location, "drydock"):
        action_index_probs.append((32, 0.001))
    if can_invest(player, current_location, "marketplace"):
        action_index_probs.append((40, 0.001))
    if can_collect(player, current_location):
        action_index_probs.append((13, 0.01))
    if can_set_home(player, current_system, current_location):
        action_index_probs.append((22, 0.0005))

    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 3500000
        and not isinstance(spaceship, Destroyer)
    ):
        action_index_probs.append((49, 0.2))
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 70000
        and not isinstance(spaceship, Frigate)
    ):
        action_index_probs.append((48, 0.4))
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 1400
        and not isinstance(spaceship, Corvette)
    ):
        action_index_probs.append((23, 0.2))
    if (
        can_buy_spaceship(player, current_location)
        and player.wallet >= 1400
        and not isinstance(spaceship, Courier)
    ):
        action_index_probs.append((45, 0.1))

    if can_pilot(player, current_location, "corvette"):
        if (isinstance(spaceship, (Explorer, Miner, Courier))) or (
            isinstance(spaceship, (Frigate, Destroyer))
            and spaceship.is_damaged()
            and player.wallet <= spaceship.calc_repair_cost()
        ):
            action_index_probs.append((29, 1))

    if can_pilot(player, current_location, "frigate") and player.wallet >= 500000:
        action_index_probs.append((30, 1))
    if can_pilot(player, current_location, "destroyer") and player.wallet >= 1250000:
        action_index_probs.append((34, 1))
    if can_pilot(player, current_location, "courier"):
        action_index_probs.append((47, 0.01))

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
        if (
            isinstance(spaceship, Corvette)
            and spaceship.level < spaceship.max_level * 0.75
        ):
            action_index_probs.append((14, 0.01))
        else:
            action_index_probs.append((14, 1))

    return action_index_probs

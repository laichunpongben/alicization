import logging

from ...locations.planet import Planet
from ...locations.moon import Moon
from ...locations.asteroid_belt import AsteroidBelt
from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()

SET_HOME_COST = 1000


def set_home(player):
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    if can_set_home(player, current_system, current_location):
        player_manager.update_home_system(player.name, current_system)
        player.spend(SET_HOME_COST)
        logger.info(f"{player.name} set home to {current_system.name}.")
    else:
        logger.warning("Cannot set home from this location.")


def explore(player):
    current_location = player_manager.get_location(player.name)
    if can_explore(current_location):
        logger.info(
            f"{player.name} explored {current_location.name}. This has no effect yet."
        )
    else:
        logger.warning(f"No resources found on {current_location.name}")


def can_set_home(player, current_system, current_location):
    home_system = player_manager.get_home_system(player.name)
    return (
        isinstance(current_location, Planet)
        and player.wallet >= SET_HOME_COST
        and current_system != home_system
    )


def can_explore(current_location):
    return isinstance(current_location, (Planet, Moon, AsteroidBelt))

# players/actions/material.py

import logging

from ...managers.player_manager import PlayerManager
from ...locations.mineable import Mineable
from ...locations.debris import Debris

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def mine(player):
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_mine(current_location, spaceship):
        current_location.mine(player, spaceship)
        logger.debug(f"{player.name} mined from {current_location.name}")
    else:
        logger.warning("Cannot mine from this location.")


def salvage(player):
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_salvage(current_location, spaceship):
        current_location.salvage(player, spaceship)
        logger.debug(f"{player.name} salvaged debris at {current_location.name}")
    else:
        logger.warning("Cannot upgrade spaceship from this location.")


def can_mine(current_location, spaceship):
    return (
        isinstance(current_location, Mineable)
        and not spaceship.is_cargo_full()
        and spaceship.weapon <= 0
        and any(amount > 0 for amount in current_location.get_resources().values())
    )


def can_salvage(current_location, spaceship):
    return (
        isinstance(current_location, Debris)
        and not current_location.is_empty()
        and not spaceship.is_cargo_full()
    )

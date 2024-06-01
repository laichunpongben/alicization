# players/actions/spaceship_maintenance.py

import logging

from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def repair(player) -> None:
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_repair(player, current_location, spaceship):
        current_location.drydock.repair_spaceship(player, spaceship)
        logger.debug(f"{player.name} repaired spaceship at {current_location.name}")
    else:
        logger.warning("Cannot repair spaceship from this location.")


def upgrade(player) -> None:
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_upgrade(player, current_location, spaceship):
        current_location.drydock.upgrade_spaceship(player, spaceship)
        logger.debug(f"{player.name} upgraded spaceship at {current_location.name}")
    else:
        logger.warning("Cannot upgrade spaceship from this location.")


def can_repair(player, current_location, spaceship) -> bool:
    return current_location.has_drydock() and current_location.drydock.can_repair(
        player, spaceship
    )


def can_upgrade(player, current_location, spaceship) -> bool:
    return current_location.has_drydock() and current_location.drydock.can_upgrade(
        player, spaceship
    )

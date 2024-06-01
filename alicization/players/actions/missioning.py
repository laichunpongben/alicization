# players/actions/missioning.py

import logging

from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def do_mission(player, difficulty: str):
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_mission(current_location):
        mission_center = current_location.mission_center
        if difficulty == "easy":
            order_by = 1
        elif difficulty == "hard":
            order_by = -1
        else:
            order_by = 0

        mission = mission_center.apply_mission(order_by)
        if mission:
            result = mission_center.do_mission(player, spaceship, mission)
            if result > 0:
                logger.debug(
                    f"{player.name} completed mission {mission.description} at {current_location.name}"
                )
            else:
                logger.debug(f"{player.name} failed mission {mission.description}")
    else:
        logger.warning("Cannot do mission from this location.")


def can_mission(current_location):
    return (
        current_location.has_mission_center()
        and len(current_location.mission_center.get_available_missions()) > 0
    )

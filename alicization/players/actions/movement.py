# players/actions/movement.py

import random
import logging

from ...managers.player_manager import PlayerManager
from ...locations.stargate import Stargate

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def move(player, current_location, target_location) -> None:
    current_location.remove_player(player)
    target_location.add_player(player)
    logger.debug(
        f"{player.name} moved from {current_location.name} to {target_location.name}"
    )


def move_random(player, current_location, target_locations) -> None:
    if current_location in target_locations:
        target_locations.remove(current_location)
    if target_locations:
        target_location = random.choice(target_locations)
        move(player, current_location, target_location)


def move_to_random_planet(player) -> None:
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    if can_move_planet(current_system):
        planets = current_system.planets[:]
        move_random(player, current_location, planets)


def move_to_random_moon(player) -> None:
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    if can_move_moon(current_system):
        moons = current_system.moons[:]
        move_random(player, current_location, moons)


def move_to_random_asteroid_belt(player) -> None:
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    if can_move_asteroid_belt(current_system):
        asteroid_belts = current_system.asteroid_belts[:]
        move_random(player, current_location, asteroid_belts)


def move_to_random_stargate(player) -> None:
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    if can_move_stargate(current_system):
        stargates = current_system.stargates[:]
        move_random(player, current_location, stargates)


def move_to_random_debris(player) -> None:
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    if can_move_debris(current_system):
        debrises = current_system.debrises[:]
        move_random(player, current_location, debrises)


def activate_stargate(player) -> None:
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_travel(current_location):
        current_location.activate(player, spaceship)
    else:
        logger.warning("Cannot activate stargate from this location.")


def can_move_planet(current_system) -> bool:
    return len(current_system.planets) > 0


def can_move_moon(current_system) -> bool:
    return len(current_system.moons) > 0


def can_move_asteroid_belt(current_system) -> bool:
    return len(current_system.asteroid_belts) > 0


def can_move_stargate(current_system) -> bool:
    return len(current_system.stargates) > 0


def can_move_debris(current_system) -> bool:
    return len(current_system.debrises) > 0


def can_travel(current_location) -> bool:
    return isinstance(current_location, Stargate)

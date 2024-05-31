# stargate.py

import math
import logging

from .location import Location

logger = logging.getLogger(__name__)


class Stargate(Location):
    def __init__(self, origin, destination, distance):
        name = f"Stargate: {origin.name} -> {destination.name}"
        Location.__init__(self, name)
        self.origin = origin
        self.destination = destination
        self.distance = distance

    def activate(self, player):
        # system change
        self.origin.remove_player(player)
        self.destination.add_player(player)

        self.remove_player(player)
        target_stargate = self.find_target_stargate(self.destination, self.origin)
        if target_stargate is not None:
            target_stargate.add_player(player)
        else:
            self.destination.empty_space.add_player(player)

        player.distance_traveled += self.distance
        player.turns_until_idle += int(
            math.ceil(self.distance / min(player.spaceship.engine, 1))
        )
        player.universe.total_distance_traveled += self.distance
        logger.debug(
            f"{player.name} traveled from {self.origin.name} to {self.destination.name}"
        )

    def find_target_stargate(self, target_system, current_system):
        if len(target_system.stargates) > 0:
            for stargate in target_system.stargates:
                if stargate.destination == current_system:
                    return stargate
        return None

    def __str__(self):
        return self.name

    def to_json(self):
        return {"origin": self.origin.name, "destination": self.destination.name}

    def debug_print(self):
        logger.info(f"Stargate: {self.name}")
        logger.info(f"Players: {self.players}")

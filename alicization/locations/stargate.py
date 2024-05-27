# stargate.py

import logging

from .location import Location

logger = logging.getLogger(__name__)


class Stargate(Location):
    def __init__(self, origin, destination, distance):
        Location.__init__(self)
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
        player.turns_until_idle = self.distance
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

    def add_player(self, player):
        self.players.append(player)
        player.current_location = self
        logger.info(f"Player {player} added to {self.name}.")

    def remove_player(self, player):
        self.players.remove(player)
        player.current_location = None
        logger.info(f"Player {player} removed from {self.name}.")

    @property
    def name(self):
        return str(self)

    def __str__(self):
        return f"Stargate: {self.origin.name} -> {self.destination.name}"

    def to_json(self):
        return {"origin": self.origin.name, "destination": self.destination.name}

    def debug_print(self):
        logger.info(f"Stargate: {self.name}")
        logger.info(f"Players: {self.players}")
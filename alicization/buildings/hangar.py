# hangar.py

import uuid
from typing import List
import logging

from .building import Building

logger = logging.getLogger(__name__)


class Hangar(Building):
    def __init__(self):
        Building.__init__(self)
        self.name = f"Hangar {uuid.uuid4().hex}"
        self.spaceships = {}

    def add_spaceship(self, player, spaceship) -> None:
        if player.name not in self.spaceships:
            self.spaceships[player.name] = []
        else:
            self.spaceships[player.name].append(spaceship)

        logger.info(f"Added spaceship to player {player.name}'s hangar.")

    def remove_spaceship(self, player, spaceship_class: str):
        if player.name not in self.spaceships:
            self.spaceships[player.name] = []
        else:
            for spaceship in self.spaceships[player.name]:
                if spaceship.ship_class == spaceship_class:
                    self.spaceships[player.name].remove(spaceship)
                    logger.info(
                        f"Removed spaceship from player {player.name}'s hangar."
                    )
                    return spaceship
        return None

    def has_spaceship(self, player, spaceship_class: str) -> bool:
        if player.name not in self.spaceships:
            self.spaceships[player.name] = []
        else:
            for spaceship in self.spaceships[player.name]:
                if spaceship.ship_class == spaceship_class:
                    return True
        return False

    def get_spaceships(self, player) -> List:
        return self.spaceships.get(player.name, [])

    def reset(self):
        self._hull = self._max_hull
        self._cooldown = 10000
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

# locations/debris.py

import random
from collections import defaultdict
import uuid
import math
import logging

from .location import Location


logger = logging.getLogger(__name__)

P_DEBRIS_ADD = 0.9


class Debris(Location):
    def __init__(self):
        name = f"Debris {uuid.uuid4().hex}"
        Location.__init__(self, name)
        self._resources = defaultdict(int)

    @property
    def resources(self):
        return self._resources

    def add(self, cargo: dict) -> None:
        if cargo:
            for item, count in cargo.items():
                if random.random() < P_DEBRIS_ADD:
                    self._resources[item] += count

    def salvage(self, player, spaceship):
        if self._resources and not spaceship.is_cargo_full():
            item = random.choice(list(self._resources.keys()))
            qty = self._resources[item]
            skill_level = player.skills["salvaging"]
            if self._salvage_success(skill_level):
                spaceship.cargo_hold[item] += qty
                self._resources.pop(item)
                player.salvage_completed += 1
                player.turn_production += qty
                player.skills["salvaging"] = (
                    int(math.log(player.salvage_completed) / math.log(math.sqrt(2)))
                    if player.salvage_completed > 0
                    else 0
                )
        else:
            logger.warning("Empty debris!")

    def _salvage_success(self, skill_level: int):
        success_chance = max(0, min(0.9 * (1 + skill_level * 0.001), 0.9999))
        return random.random() < success_chance

    def is_empty(self):
        return not self._resources

    def __str__(self):
        return self.name

    def debug_print(self):
        logger.info(f"Debris: {self.name}")
        logger.info(f"Resources: {self._resources}")
        logger.info(f"Players: {self.players}")

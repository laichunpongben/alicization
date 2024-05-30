# debris.py

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
        Location.__init__(self)
        self.resources = defaultdict(int)

    def add(self, cargo):
        if cargo:
            for item, count in cargo.items():
                if random.random() < P_DEBRIS_ADD:
                    self.resources[item] += count

    def salvage(self, player):
        if self.resources and not player.spaceship.is_cargo_full():
            item = random.choice(list(self.resources.keys()))
            count = self.resources[item]
            skill_level = player.skills["salvaging"]
            if self.salvage_success(skill_level):
                player.spaceship.cargo_hold[item] += count
                self.resources.pop(item)
                player.salvage_completed += 1
                player.turn_material_gain += count
                player.skills["salvaging"] = (
                    int(math.log(player.salvage_completed) / math.log(math.sqrt(2)))
                    if player.salvage_completed > 0
                    else 0
                )
        else:
            logger.warning("Empty debris!")

    def salvage_success(self, skill_level):
        success_chance = max(0, min(0.9 * (1 + skill_level * 0.001), 0.9999))
        return random.random() < success_chance

    def is_empty(self):
        return not self.resources

    @property
    def name(self):
        return str(self)

    def __str__(self):
        return f"Debris {uuid.uuid4().hex}"

    def debug_print(self):
        logger.info(f"Debris: {self.name}")
        logger.info(f"Resources: {self.resources}")
        logger.info(f"Players: {self.players}")

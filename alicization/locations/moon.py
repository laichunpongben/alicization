# moon.py

import random
import math
import logging

from .location import Location
from .mineable import Mineable
from ..buildings.drydock import Drydock
from ..buildings.mission_center import MissionCenter
from ..managers.material_manager import MaterialManager

logger = logging.getLogger(__name__)

material_manager = MaterialManager()

BASE_MINE_AMOUNT = 100


class Moon(Location, Mineable):
    def __init__(self, name):
        Location.__init__(self)
        Mineable.__init__(self)
        self.name = name
        self.resources = self.load_initial_resources()
        self.drydock = Drydock()
        self.mission_center = MissionCenter()
        self._buildings = [self.drydock, self.mission_center]

    def load_initial_resources(self):
        resources = {}
        moon_resource_ranges = {
            "helium": (1, 1000000000),
            "rare_earth_minerals": (1, 500000000),
            "water_ice": (1, 1000000000),
        }
        for material_name, range in moon_resource_ranges.items():
            material = material_manager.get_material(material_name)
            resources[material.name] = random.randint(range[0], range[1])
        return resources

    def mine(self, player):
        if player.spaceship.is_cargo_full():
            return 0

        available_resources = [
            resource for resource in self.resources if self.resources[resource] > 0
        ]
        if not available_resources:
            return 0

        resource_to_mine = random.choice(available_resources)
        material = material_manager.get_material(resource_to_mine)
        if not material:
            return 0

        max_mined_amount = int(
            max(
                0,
                (
                    BASE_MINE_AMOUNT
                    * (player.spaceship.mining + player.spaceship.level / 10)
                    * (1 + player.skills["mining"] * 0.001)
                )
                // material.rarity,
            )
        )
        mined_amount = random.randint(0, max_mined_amount)
        mined_amount = min(mined_amount, self.resources[resource_to_mine])
        self.resources[resource_to_mine] -= mined_amount
        player.spaceship.cargo_hold[resource_to_mine] += mined_amount

        player.mining_completed += 1
        player.mined += mined_amount
        player.universe.total_mined += mined_amount
        player.skills["mining"] = (
            int(math.log(player.mining_completed) / math.log(math.sqrt(2)))
            if player.mining_completed > 0
            else 0
        )

        return 1

    def get_resources(self):
        return self.resources

    def add_player(self, player):
        self.players.append(player)
        player.current_location = self

    def remove_player(self, player):
        self.players.remove(player)
        player.current_location = None

    def debug_print(self):
        logger.info(f"Moon: {self.name}")
        logger.info(f"Resources: {self.resources}")
        logger.info(f"Players: {self.players}")

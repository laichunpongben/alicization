# locations/moon.py

import random
import math
import logging

import numpy as np

from .location import Location
from .mineable import Mineable
from ..buildings.hangar import Hangar
from ..buildings.drydock import Drydock
from ..buildings.mission_center import MissionCenter
from ..managers.player_manager import PlayerManager
from ..managers.material_manager import MaterialManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()
material_manager = MaterialManager()

BASE_MINE_AMOUNT = 100


class Moon(Location, Mineable):
    def __init__(self):
        Location.__init__(self)
        Mineable.__init__(self)
        self._resources = self._load_initial_resources()
        self.hangar = Hangar()
        self.drydock = Drydock()
        self.mission_center = MissionCenter()
        self._buildings = [self.hangar, self.drydock, self.mission_center]

    @property
    def resources(self):
        return self._resources

    def _load_initial_resources(self):
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

    def mine(self, player, spaceship):
        if spaceship.is_cargo_full():
            return 0

        available_resources = [
            resource for resource in self._resources if self._resources[resource] > 0
        ]
        if not available_resources:
            return 0

        resource_to_mine = random.choice(available_resources)
        material = material_manager.get_material(resource_to_mine)
        if not material:
            return 0

        base_mined_amount = max(
            BASE_MINE_AMOUNT
            * spaceship.mining
            * (1 + spaceship.level / 10)
            * (1 + player.skills["mining"] * 0.001),
            0,
        )
        rarity_effect = 1 / (1 + np.log1p(material.rarity))
        mined_amount = np.random.binomial(base_mined_amount / 10, rarity_effect) * 10
        mined_amount = min(mined_amount, self._resources[resource_to_mine])

        self._resources[resource_to_mine] -= mined_amount
        spaceship.cargo_hold[resource_to_mine] += mined_amount

        player.mining_completed += 1
        player.mined += mined_amount
        player.turn_production += mined_amount

        universe = player_manager.get_universe(player.name)
        universe.total_mined += mined_amount
        player.skills["mining"] = (
            int(math.log(player.mining_completed) / math.log(math.sqrt(2)))
            if player.mining_completed > 0
            else 0
        )

        return 1

    def debug_print(self):
        logger.info(f"Moon: {self.name}")
        logger.info(f"Resources: {self._resources}")
        logger.info(f"Players: {self.players}")

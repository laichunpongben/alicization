# planet.py

import random
import math
import logging

import numpy as np

from .location import Location
from .mineable import Mineable
from ..buildings.hangar import Hangar
from ..buildings.storage import Storage
from ..buildings.marketplace import Marketplace
from ..buildings.factory import Factory
from ..buildings.drydock import Drydock
from ..buildings.planetary_defense import PlanetaryDefense
from ..managers.material_manager import MaterialManager

logger = logging.getLogger(__name__)

material_manager = MaterialManager()

NUM_MATERIAL_TYPE = 10
RARIRY_DECAY_SELECTION = 0.25
RARIRY_DECAY_QTY = 0.25
BASE_QTY = 1e9  # large init qty but no refill
MAX_QTY = 1e12
BASE_MINE_AMOUNT = 100


class Planet(Location, Mineable):
    def __init__(self, name):
        Location.__init__(self)
        Mineable.__init__(self)
        self.name = name
        self.hangar = Hangar()
        self.storage = Storage()
        self.drydock = Drydock()
        self.marketplace = Marketplace()
        self.factory = Factory()
        self.defense = PlanetaryDefense()
        self.resources = self.load_initial_resources()
        self._buildings = [
            self.hangar,
            self.drydock,
            self.marketplace,
            self.factory,
            self.defense,
        ]

    def load_initial_resources(self):
        resources = {}
        available_materials = list(material_manager.materials.values())
        sorted_materials = sorted(available_materials, key=lambda x: x.rarity)

        probabilities = []
        for material in sorted_materials:
            rarity = material.rarity
            probability = RARIRY_DECAY_SELECTION ** (rarity - 1)
            probabilities.append(probability)

        total_probability = sum(probabilities)
        normalized_probabilities = [p / total_probability for p in probabilities]

        selected_materials = random.choices(
            sorted_materials, weights=normalized_probabilities, k=NUM_MATERIAL_TYPE
        )

        for material in selected_materials:
            rarity = material.rarity
            mean = BASE_QTY * RARIRY_DECAY_QTY ** (rarity - 1)
            resources[material.name] = min(np.random.poisson(mean), MAX_QTY)

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

        base_mined_amount = max(
            BASE_MINE_AMOUNT
            * player.spaceship.mining
            * (1 + player.spaceship.level / 10)
            * (1 + player.skills["mining"] * 0.001),
            0,
        )
        rarity_effect = 1 / (1 + np.log1p(material.rarity))
        mined_amount = np.random.binomial(base_mined_amount / 10, rarity_effect) * 10
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

    def debug_print(self):
        logger.info(f"Planet: {self.name}")
        logger.info(f"Resources: {self.resources}")
        logger.info(f"Players: {self.players}")

    def to_json(self):
        return {"name": self.name, "resources": self.resources}

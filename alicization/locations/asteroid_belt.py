# asteroid_belt.py

import random
import math
import logging

import numpy as np

from .location import Location
from .mineable import Mineable
from ..managers.material_manager import MaterialManager
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

material_manager = MaterialManager()
leaderboard = Leaderboard()


NUM_MATERIAL_TYPE = 5
RARIRY_DECAY_SELECTION = 0.5
RARIRY_DECAY_QTY = 0.25
BASE_QTY = 1e6
P_RESWAPN = 0.01
P_CRASH_BASE = 0.005
CRASH_MEAN_DAMAGE = 200
BASE_MINE_AMOUNT = 100
MAX_QTY = 1e12


class AsteroidBelt(Location, Mineable):
    def __init__(self, name):
        Location.__init__(self)
        Mineable.__init__(self)
        self.name = name
        self.resources = self.load_initial_resources()

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
        self.check_crash(player)

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

    def check_crash(self, player):
        skill_level = player.skills["mining"]
        p_crash = P_CRASH_BASE * max(1 - skill_level * 0.001, 0.01)
        if random.random() < p_crash:
            damage = np.random.poisson(CRASH_MEAN_DAMAGE)
            logger.debug(f"{self.name} crashed! Causing {damage} damage!")
            player.spaceship.take_damage(damage)
            if player.spaceship.destroyed:
                leaderboard.log_achievement(player.name, "death", 1)
                player.die()

    def get_resources(self):
        return self.resources

    def respawn_resources(self):
        if all(
            amount == 0 for amount in self.resources.values()
        ):  # All resources depleted
            if random.random() < P_RESWAPN:
                self.resources = self.load_initial_resources()
                logger.debug(
                    f"Resources respawned in {self.name} with {self.resources}"
                )

    def debug_print(self):
        logger.info(f"Asteroid Belt: {self.name}")
        logger.info(f"Resources: {self.resources}")
        logger.info(f"Players: {self.players}")

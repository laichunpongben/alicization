# factory.py

import uuid
from collections import defaultdict
import random
import logging

from .building import Building
from .investable import Investable
from ..managers.blueprint_manager import BlueprintManager
from ..managers.spaceship_manager import SpaceshipManager
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

blueprint_manager = BlueprintManager()
spaceship_manager = SpaceshipManager()
leaderboard = Leaderboard()

JOB_COST_RATIO = 0.1
DEFAULT_SPACESHIP_COST = 1
P_JOB_SUCCESS_BASE = 0.9
BASE_EARNING_RATIO = 0.5
PRODUCTION_ESTIMATE = 0.285714


class Factory(Building, Investable):
    def __init__(self):
        Building.__init__(self)
        Investable.__init__(self)
        self.name = f"Factory {uuid.uuid4().hex}"

    def manufacture(self, player, blueprint_name):
        if self._cooldown > 0:
            return False

        spaceship_info = spaceship_manager.get_spaceship(blueprint_name)
        if spaceship_info:
            base_price = spaceship_info.base_price
        else:
            base_price = DEFAULT_SPACESHIP_COST

        blueprint = blueprint_manager.get_blueprint(blueprint_name)
        job_cost = base_price * JOB_COST_RATIO

        missing_materials = []
        for material, qty in blueprint.components.items():
            if player.current_location.storage.get_item(player.name, material) < qty:
                missing_materials.append((material, qty))

        if player.wallet >= job_cost and not missing_materials:
            for material, qty in blueprint.components.items():
                player.current_location.storage.remove_item(player.name, material, qty)

            player.spend(job_cost)
            earning = job_cost * min(BASE_EARNING_RATIO * (1 + self.level * 0.01), 1)
            self._distribute_earnings(earning)

            if self.job_success():
                player.current_location.storage.add_item(player.name, blueprint_name, 1)
                player.build += 1
                player.turn_production += int(base_price * PRODUCTION_ESTIMATE)
                player.universe.total_build += 1

                scores = {
                    "miner": 1,
                    "corvette": 2,
                    "extractor": 50,
                    "frigate": 100,
                    "destroyer": 5000,
                }
                score = scores.get(blueprint_name, 0)
                leaderboard.log_achievement(player.name, "build", score)
                logger.info(
                    f"{blueprint_name} manufacturing job success at {self.name}!"
                )
                return True

        return False

    def job_success(self):
        return random.random() < min(
            P_JOB_SUCCESS_BASE * (1 + self.level * 0.01), 0.9999
        )

    def reset(self):
        self.level = 0
        self.investment = 0
        self.equities = defaultdict(float)
        self.last_payout_turns = defaultdict(int)
        self.monopoly = False
        self.owner = None
        self.owner_investment = 0
        self._hull = self._max_hull
        self._cooldown = (
            int(self._max_hull / self._self_repair_hull)
            if self._self_repair_hull > 0
            else 10000
        )
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

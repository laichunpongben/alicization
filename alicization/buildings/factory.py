# factory.py

import uuid
from collections import defaultdict
import random
import logging

from .building import Building
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


class Factory(Building):
    def __init__(self):
        Building.__init__(self)
        self.name = f"Factory {uuid.uuid4().hex}"
        self.level = 0
        self.investment = 0
        self.undistributed_earning = 0
        self.equities = defaultdict(float)
        self.earnings = defaultdict(float)
        self.monopoly = False
        self.owner = None
        self.owner_investment = 0

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
            if player.inventory.get(material, 0) < qty:
                missing_materials.append((material, qty))

        if player.wallet >= job_cost and not missing_materials:
            for material, qty in blueprint.components.items():
                player.inventory[material] -= qty

            player.spend(job_cost)
            self._distribute_earnings(job_cost)

            if self.job_success():
                player.inventory[blueprint_name] += 1
                player.build += 1
                player.universe.total_build += 1

                scores = {
                    "miner": 1,
                    "corvette": 2,
                    "frigate": 100,
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

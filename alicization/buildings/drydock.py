# drydock.py

import uuid
from collections import defaultdict
import logging

from .building import Building
from ..managers.blueprint_manager import BlueprintManager
from ..managers.spaceship_manager import SpaceshipManager
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

blueprint_manager = BlueprintManager()
spaceship_manager = SpaceshipManager()
leaderboard = Leaderboard()

MONOPOLY_SCORE = 100
MONOPOLY_THRESHOLD = 0.995
NUM_BOMBARD_ROUND = 10
P_BOMBARD_HIT = 0.5
DESTROY_SCORE = 1000
BASE_EARNING_RATIO = 0.5


class Drydock(Building):
    def __init__(self):
        super().__init__()
        self.name = f"Drydock {uuid.uuid4().hex}"
        self.level = 0
        self.investment = 0
        self.undistributed_earning = 0
        self.equities = defaultdict(float)
        self.earnings = defaultdict(float)
        self.monopoly = False
        self.owner = None
        self.owner_investment = 0

    def can_repair(self, player):
        return (
            player.spaceship.is_damaged()
            and player.wallet >= player.spaceship.calc_upgrade_cost()
        )

    def can_upgrade(self, player):
        return (
            player.spaceship.level < player.spaceship.max_level
            and player.wallet >= player.spaceship.calc_upgrade_cost()
        )

    def repair_spaceship(self, player):
        if self._cooldown > 0:
            return False

        if self.can_repair(player):
            repair_cost = player.spaceship.calc_repair_cost()
            player.spend(repair_cost)
            player.spaceship.repair()
            self._distribute_earnings(repair_cost)
            logger.info(
                f"{player.spaceship.ship_class} repaired at {self.name} for {repair_cost}."
            )
            return True

        return False

    def upgrade_spaceship(self, player):
        if self._cooldown > 0:
            return False

        if self.can_upgrade(player):
            upgrade_cost = player.spaceship.calc_upgrade_cost()
            player.spend(upgrade_cost)
            player.spaceship.upgrade()
            self._distribute_earnings(upgrade_cost)
            logger.info(
                f"{player.spaceship.ship_class} upgraded at {self.name} for {upgrade_cost}."
            )
            return True

        return False

    def _calculate_repair_cost(self, spaceship):
        return spaceship.base_price * (1 - spaceship.health_ratio) * self.level

    def _calculate_upgrade_cost(self, spaceship):
        return spaceship.base_price * 0.2 * self.level

    def _distribute_earnings(self, amount):
        earning = amount * min(BASE_EARNING_RATIO * (1 + self.level * 0.01), 1)
        self.undistributed_earning += earning
        if sum(self.equities.values()) > 0 and self.investment > 0:
            for shareholder, equity in self.equities.items():
                ratio = equity / self.investment
                self.earnings[shareholder] += max(self.undistributed_earning * ratio, 0)
            self.undistributed_earning = 0
            logger.info(f"{self.name} updated earning for {earning}.")

    def reset(self):
        if self.monopoly and self.owner:
            leaderboard.log_achievement(self.owner, "monopoly", -MONOPOLY_SCORE)

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

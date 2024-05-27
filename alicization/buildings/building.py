# building.py

from abc import ABC, abstractmethod
import math
import logging

import numpy as np

from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

leaderboard = Leaderboard()

MONOPOLY_THRESHOLD = 0.995
MONOPOLY_SCORE = 100
NUM_BOMBARD_ROUND = 10
P_BOMBARD_HIT = 0.5
DESTROY_SCORE = 10000


class Building(ABC):
    def __init__(self, hull: int = 1e6):
        self._max_hull = hull
        self._hull = hull
        self._self_repair_hull = 100
        self._cooldown = 0
        self._base_earning_ratio = 0.5

    @property
    def max_hull(self):
        return self._max_hull

    @max_hull.setter
    def max_hull(self, value):
        self._max_hull = value

    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = value

    @property
    def cooldown(self):
        return self._cooldown

    @cooldown.setter
    def cooldown(self, value):
        self._cooldown = value

    @property
    def base_earning_ratio(self):
        return self._base_earning_ratio

    @base_earning_ratio.setter
    def base_earning_ratio(self, value):
        self._base_earning_ratio = value

    @property
    def self_repair_hull(self):
        return self._self_repair_hull

    @self_repair_hull.setter
    def self_repair_hull(self, value):
        self._self_repair_hull = value

    def repair(self):
        self._hull = min(self._hull + self._self_repair_hull, self._max_hull)
        self._cooldown = max(self._cooldown - 1, 0)

    @abstractmethod
    def bombard(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    def _distribute_earnings(self, amount):
        earning = amount * min(self.base_earning_ratio * (1 + self.level * 0.01), 1)
        self.undistributed_earning += earning
        if sum(self.equities.values()) > 0 and self.investment > 0:
            for shareholder, equity in self.equities.items():
                ratio = equity / self.investment
                self.earnings[shareholder] += max(self.undistributed_earning * ratio, 0)
            self.undistributed_earning = 0
            logger.info(f"{self.name} updated earning for {earning}.")

    def invest(self, player, amount):
        if self._cooldown > 0:
            return

        if player.wallet < amount:
            logger.warning(f"{player.name} does not have enough funds to invest.")
            return

        before_monopoly = self.monopoly
        before_owner = self.owner

        player.spend(amount)
        player.total_investment += amount
        self.equities[player.name] += amount
        self.investment += amount
        self.level = self._calculate_level(self.investment)

        self._update_monopoly_status(player, before_monopoly, before_owner)

    def profit(self, player):
        if self._cooldown > 0:
            return 0

        payout = self.earnings[player.name]
        if payout > 0:
            player.wallet += payout
            player.profit_collected += payout
            self.earnings[player.name] = 0

        return payout

    def _calculate_level(self, investment):
        return int(math.log10(investment)) if investment > 0 else 0

    def _get_investment_ratio(self, player):
        return (
            self.equities[player.name] / self.investment if self.investment > 0 else 0
        )

    def _update_monopoly_status(self, player, before_monopoly, before_owner):
        ratio = self._get_investment_ratio(player)
        if ratio >= MONOPOLY_THRESHOLD:
            self._set_monopoly(player)
            if before_monopoly:
                leaderboard.log_achievement(before_owner, "monopoly", -MONOPOLY_SCORE)
        elif (
            self.investment > 0
            and self.owner_investment / self.investment >= MONOPOLY_THRESHOLD
        ):
            self.monopoly = True
        else:
            self._clear_monopoly(before_monopoly, before_owner)

    def _set_monopoly(self, player):
        self.owner = player.name
        self.owner_investment = self.equities[player.name]
        self.monopoly = True
        leaderboard.log_achievement(player.name, "monopoly", MONOPOLY_SCORE)
        logger.warning(f"{player.name} gained monopoly on {self.name}")

    def _clear_monopoly(self, before_monopoly, before_owner):
        self.monopoly = False
        self.owner = None
        self.owner_investment = 0
        if before_monopoly and before_owner:
            leaderboard.log_achievement(before_owner, "monopoly", -MONOPOLY_SCORE)
            logger.warning(f"{before_owner} lost monopoly on {self.name}")

    def bombard(self, player):
        if self._cooldown > 0:
            logger.warning(f"{self.name} is still in cooldown!")
            return

        damage = (
            np.random.binomial(NUM_BOMBARD_ROUND, P_BOMBARD_HIT)
            * player.spaceship.weapon
        )
        player.total_damage += damage
        player.universe.total_damage_dealt += damage
        self._hull = max(self._hull - damage, 0)
        logger.info(f"{self.name} was bombarded and took {damage} damage!")
        if self._hull <= 0:
            player.destroy += 1
            player.universe.total_destroy += 1
            leaderboard.log_achievement(player.name, "destroy", DESTROY_SCORE)
            if self.monopoly and self.owner:
                leaderboard.log_achievement(self.owner, "monopoly", -MONOPOLY_SCORE)

            self.reset()
            player.universe.full_check_all_players()
        else:
            if (
                hasattr(player.current_location, "defense")
                and player.current_location.defense is not None
            ):
                defensive_damage = player.current_location.defense.attack()
                player.spaceship.take_damage(defensive_damage)
                if player.spaceship.destroyed:
                    player.current_system.make_debris(player.spaceship.cargo_hold)
                    player.die()
                    leaderboard.log_achievement(player.name, "death", 1)

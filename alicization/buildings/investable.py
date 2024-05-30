# investable.py

from abc import ABC, abstractmethod
import math
from collections import defaultdict
import logging

from ..managers.leaderboard import Leaderboard


logger = logging.getLogger(__name__)

leaderboard = Leaderboard()

MONOPOLY_THRESHOLD = 0.995
MONOPOLY_SCORE = 1000


class Investable(ABC):
    """Interface for investable buildings."""

    def __init__(self):
        self._level = 0
        self._investment = 0
        self._undistributed_earning = 0
        self._equities = defaultdict(float)
        self._earnings = defaultdict(float)
        self._monopoly = False
        self._owner = None
        self._owner_investment = 0

    @property
    def level(self):
        return self._level

    @property
    def investment(self):
        return self._investment

    @property
    def undistributed_earning(self):
        return self._undistributed_earning

    @property
    def equities(self):
        return self._equities

    @property
    def earnings(self):
        return self._earnings

    @property
    def monopoly(self):
        return self._monopoly

    @property
    def owner(self):
        return self._owner

    def invest(self, player, amount: float):
        if self.cooldown > 0:
            return

        if player.wallet < amount:
            logger.warning(f"{player.name} does not have enough funds to invest.")
            return

        before_monopoly = self._monopoly
        before_owner = self._owner

        player.spend(amount)
        player.total_investment += amount
        self._equities[player.name] += amount
        self._investment += amount
        self._level = self._calculate_level(self.investment)

        self._update_monopoly_status(player, before_monopoly, before_owner)

    def profit(self, player):
        if self.cooldown > 0:
            return 0

        payout = self._earnings[player.name]
        if payout > 0:
            player.earn(payout)
            player.profit_collected += payout
            self._earnings[player.name] = 0

        return payout

    def _calculate_level(self, investment):
        return int(math.log10(investment)) if investment > 0 else 0

    def _get_investment_ratio(self, player):
        return (
            self._equities[player.name] / self._investment
            if self._investment > 0
            else 0
        )

    def _update_monopoly_status(self, player, before_monopoly, before_owner):
        ratio = self._get_investment_ratio(player)
        if ratio >= MONOPOLY_THRESHOLD:
            self._set_monopoly(player)
            if before_monopoly:
                leaderboard.log_achievement(before_owner, "monopoly", -MONOPOLY_SCORE)
        elif (
            self._investment > 0
            and self._owner_investment / self._investment >= MONOPOLY_THRESHOLD
        ):
            self._monopoly = True
        else:
            self._clear_monopoly(before_monopoly, before_owner)

    def _set_monopoly(self, player):
        self._owner = player.name
        self._owner_investment = self._equities[player.name]
        self._monopoly = True
        leaderboard.log_achievement(player.name, "monopoly", MONOPOLY_SCORE)
        logger.warning(f"{player.name} gained monopoly on {self.name}")

    def _clear_monopoly(self, before_monopoly, before_owner):
        self._monopoly = False
        self._owner = None
        self._owner_investment = 0
        if before_monopoly and before_owner:
            leaderboard.log_achievement(before_owner, "monopoly", -MONOPOLY_SCORE)
            logger.warning(f"{before_owner} lost monopoly on {self.name}")

    def _distribute_earnings(self, earning: float):
        self._undistributed_earning += earning
        if sum(self._equities.values()) > 0 and self._investment > 0:
            for shareholder, equity in self._equities.items():
                ratio = equity / self._investment
                self._earnings[shareholder] += max(
                    self._undistributed_earning * ratio, 0
                )
            self._undistributed_earning = 0
            logger.info(f"{self.name} updated earning for {earning}.")

    def destroy(self):
        before_monopoly = self._monopoly
        before_owner = self._owner
        self._clear_monopoly(before_monopoly, before_owner)

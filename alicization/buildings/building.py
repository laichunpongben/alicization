# building.py

from abc import ABC, abstractmethod
import logging

import numpy as np

from ..managers.player_manager import PlayerManager
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

player_manager = PlayerManager()
leaderboard = Leaderboard()

NUM_BOMBARD_ROUND = 10
P_BOMBARD_HIT = 0.5
DESTROY_SCORE = 10000


class Building(ABC):
    def __init__(self, hull: int = 1e6):
        self._max_hull = hull
        self._hull = hull
        self._self_repair_hull = 100
        self._cooldown = 0

    @property
    def max_hull(self):
        return self._max_hull

    @property
    def hull(self):
        return self._hull

    @property
    def cooldown(self):
        return self._cooldown

    @property
    def self_repair_hull(self):
        return self._self_repair_hull

    def repair(self):
        self._hull = min(self._hull + self._self_repair_hull, self._max_hull)
        self._cooldown = max(self._cooldown - 1, 0)

    def bombard(self, player, spaceship):
        if self._cooldown > 0:
            logger.warning(f"{self.name} is still in cooldown!")
            return

        damage = np.random.binomial(NUM_BOMBARD_ROUND, P_BOMBARD_HIT) * spaceship.weapon
        player.total_damage += damage

        universe = player_manager.get_universe(player.name)
        universe.total_damage_dealt += damage
        self._hull = max(self._hull - damage, 0)
        logger.info(f"{self.name} was bombarded and took {damage} damage!")
        if self._hull <= 0:
            player.destroy += 1
            universe.total_destroy += 1
            leaderboard.log_achievement(player.name, "destroy", DESTROY_SCORE)
            self.destroy()
            self.reset()
            universe.full_check_all_players()
        else:
            current_location = player_manager.get_location(player.name)
            if (
                hasattr(current_location, "defense")
                and current_location.defense is not None
            ):
                defensive_damage = current_location.defense.attack()
                spaceship.take_damage(defensive_damage)
                if spaceship.destroyed:
                    current_system = player_manager.get_system(player.name)
                    current_system.make_debris(spaceship.cargo_hold)
                    player.die()
                    leaderboard.log_achievement(player.name, "death", 1)

    def destroy(self):
        pass

    def reset(self):
        pass

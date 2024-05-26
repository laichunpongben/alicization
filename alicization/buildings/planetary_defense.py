# planetary_defense.py

import uuid
import logging

import numpy as np

from .building import Building
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

leaderboard = Leaderboard()

NUM_BOMBARD_ROUND = 10
P_BOMBARD_HIT = 0.5
DESTROY_SCORE = 1000


class PlanetaryDefense(Building):
    def __init__(self):
        Building.__init__(self)
        self.name = f"Planetary Defense {uuid.uuid4().hex}"
        self.weapon = 25
        self.attack_round = 8
        self.hit_chance = 0.5

    def attack(self):
        if self.cooldown <= 0:
            functional_factor = (
                max(self._hull / self._max_hull, 0.1) if self._max_hull > 0 else 1
            )
            damage = int(
                np.random.binomial(self.attack_round, self.hit_chance)
                * self.weapon
                * functional_factor
            )
        else:
            damage = 0
        return damage

    def bombard(self, player):
        damage = (
            np.random.binomial(NUM_BOMBARD_ROUND, P_BOMBARD_HIT)
            * player.spaceship.weapon
        )
        player.total_damage += damage
        player.universe.total_damage_dealt += damage
        logger.info(f"{self.name} was bombarded and took {damage} damage!")
        if self._hull <= 0:
            player.destroy += 1
            player.universe.total_destroy += 1
            leaderboard.log_achievement(player.name, "destroy", DESTROY_SCORE)
            self.reset()
        else:
            defensive_damage = self.attack()
            player.spaceship.take_damage(defensive_damage)
            if player.spaceship.destroyed:
                player.current_system.make_debris(player.spaceship.cargo_hold)
                player.die()
                leaderboard.log_achievement(player.name, "death", 1)

    def reset(self):
        self._hull = self._max_hull
        self.cooldown = (
            int(self._max_hull / self._self_repair_hull)
            if self._self_repair_hull > 0
            else 10000
        )
        logger.warning(f"{self.name} exploded!")

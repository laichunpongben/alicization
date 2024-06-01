# star_system.py

import random
import logging

from .locations.planet import Planet
from .locations.moon import Moon
from .locations.asteroid_belt import AsteroidBelt
from .locations.debris import Debris
from .locations.empty_space import EmptySpace
from .managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


class StarSystem:
    def __init__(self, name: str):
        self.name = name
        self.planets = [Planet() for _ in range(random.randint(0, 5))]
        self.moons = (
            [Moon() for _ in range(random.randint(0, 5))]
            if len(self.planets) > 0
            else []
        )
        self.asteroid_belts = [AsteroidBelt() for _ in range(random.randint(1, 10))]
        self.debrises = []
        self.empty_space = EmptySpace()
        self._players = []
        self.stargates = []
        self.explored = 0

    @property
    def players(self):
        return self._players

    def add_player(self, player):
        self._players.append(player)
        self.explored += 1
        player_manager.update_system(player.name, self)

    def remove_player(self, player):
        self._players.remove(player)
        player_manager.update_system(player.name, None)

    def add_stargate(self, stargate):
        if stargate not in self.stargates:
            self.stargates.append(stargate)

    def make_debris(self, cargo: dict):
        debris = Debris()
        debris.add(cargo)
        self.debrises.append(debris)
        logger.debug(f"Debris created in {self.name}")

    def get_available_locations(self):
        return (
            self.planets[:]
            + self.moons[:]
            + self.asteroid_belts[:]
            + self.stargates[:]
            + self.debrises[:]
        )

    def __str__(self):
        return self.name

    def __lt__(self, other):
        return self.name < other.name

    def to_json(self):
        return {
            "name": self.name,
            "planets": [planet.to_json() for planet in self.planets],
            "stargates": [stargate.to_json() for stargate in self.stargates],
        }

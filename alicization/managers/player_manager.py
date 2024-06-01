# player_manager.py

import logging

logger = logging.getLogger(__name__)


class PlayerManager:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(PlayerManager, cls).__new__(cls)
            cls.__instance._players = {}
            cls.__instance._universes = {}
            cls.__instance._home_systems = {}
            cls.__instance._systems = {}
            cls.__instance._locations = {}
            cls.__instance._spaceships = {}
        return cls.__instance

    @property
    def players(self):
        return self._players

    @property
    def universes(self):
        return self._universes

    @property
    def home_systems(self):
        return self._home_systems

    @property
    def systems(self):
        return self._systems

    @property
    def locations(self):
        return self._locations

    @property
    def spaceships(self):
        return self._spaceships

    def get_player(self, player_name: str):
        return self._players.get(player_name)

    def add_player(self, player) -> None:
        if not player.name in self._players:
            self._players[player.name] = player
        else:
            logger.error(f"Player {player.name} already exists!")

    def get_universe(self, player_name: str):
        return self._universes.get(player_name)

    def update_universe(self, player_name: str, new_universe) -> None:
        self._universes[player_name] = new_universe

    def get_home_system(self, player_name: str):
        return self._home_systems.get(player_name)

    def update_home_system(self, player_name: str, new_system) -> None:
        self._home_systems[player_name] = new_system

    def get_system(self, player_name: str):
        return self._systems.get(player_name)

    def update_system(self, player_name: str, new_system) -> None:
        self._systems[player_name] = new_system

    def get_location(self, player_name: str):
        return self._locations.get(player_name)

    def update_location(self, player_name: str, new_location) -> None:
        self._locations[player_name] = new_location

    def get_spaceship(self, player_name: str):
        return self._spaceships.get(player_name)

    def update_spaceship(self, player_name: str, new_spaceship) -> None:
        self._spaceships[player_name] = new_spaceship

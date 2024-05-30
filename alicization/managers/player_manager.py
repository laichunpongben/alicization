# player_manager.py

import logging

logger = logging.getLogger(__name__)


class PlayerManager:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(PlayerManager, cls).__new__(cls)
            cls.__instance._map = {}
        return cls.__instance

    @property
    def map(self):
        return self._map

    def get_player(self, player_name):
        return self._map.get(player_name)

    def add_player(self, player):
        if not player.name in self._map:
            self._map[player.name] = player
        else:
            logger.error(f"Player {player.name} already exists in map!")

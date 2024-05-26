# empty_space.py

import uuid
import logging

from .location import Location

logger = logging.getLogger(__name__)


class EmptySpace(Location):
    def __init__(self):
        super().__init__()
        self.name = f"Empty Space {uuid.uuid4().hex}"

    def add_player(self, player):
        self.players.append(player)
        player.current_location = self
        logger.info(f"Player {player} added to {self.name}.")

    def remove_player(self, player):
        self.players.remove(player)
        player.current_location = None
        logger.info(f"Player {player} removed from {self.name}.")

    def debug_print(self):
        logger.info(f"Empty Space: {self.name}")
        logger.info(f"Players: {self.players}")

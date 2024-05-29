# location.py

from abc import ABC, abstractmethod
import logging

from ..buildings.hangar import Hangar
from ..buildings.drydock import Drydock
from ..buildings.storage import Storage
from ..buildings.marketplace import Marketplace
from ..buildings.mission_center import MissionCenter
from ..buildings.factory import Factory

logger = logging.getLogger(__name__)


class Location(ABC):
    def __init__(self):
        self._players = []
        self._buildings = []

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, value):
        if not isinstance(value, list):
            raise ValueError("Players must be a list")
        self._players = value

    @property
    def buildings(self):
        return self._buildings

    @buildings.setter
    def buildings(self, value):
        if not isinstance(value, list):
            raise ValueError("Buildings must be a list")
        self._buildings = value

    def add_player(self, player):
        self.players.append(player)
        player.current_location = self
        logger.debug(f"Player {player} added to {self.name}.")

    def remove_player(self, player):
        self.players.remove(player)
        player.current_location = None
        logger.debug(f"Player {player} removed from {self.name}.")

    def has_hangar(self):
        return (
            hasattr(self, "hangar")
            and isinstance(self.hangar, Hangar)
            and self.hangar.cooldown <= 0
        )

    def has_drydock(self):
        return (
            hasattr(self, "drydock")
            and isinstance(self.drydock, Drydock)
            and self.drydock.cooldown <= 0
        )

    def has_storage(self):
        return (
            hasattr(self, "storage")
            and isinstance(self.storage, Storage)
            and self.storage.cooldown <= 0
        )

    def has_marketplace(self):
        return (
            hasattr(self, "marketplace")
            and isinstance(self.marketplace, Marketplace)
            and self.marketplace.cooldown <= 0
        )

    def has_mission_center(self):
        return (
            hasattr(self, "mission_center")
            and isinstance(self.mission_center, MissionCenter)
            and self.mission_center.cooldown <= 0
        )

    def has_factory(self):
        return (
            hasattr(self, "factory")
            and isinstance(self.factory, Factory)
            and self.factory.cooldown <= 0
        )

# location.py

from abc import ABC, abstractmethod


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

    @abstractmethod
    def add_player(self, player):
        pass

    @abstractmethod
    def remove_player(self, player):
        pass

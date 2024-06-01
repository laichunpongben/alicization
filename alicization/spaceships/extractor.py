# spaceships/extractor.py

from .spaceship import Spaceship


class Extractor(Spaceship):
    def __init__(self):
        Spaceship.__init__(self)
        self._ship_class = "extractor"
        self._max_shield = 50
        self._shield = 50
        self._shield_upgrade = 5
        self._max_armor = 50
        self._armor = 50
        self._armor_upgrade = 5
        self._max_hull = 200
        self._hull = 200
        self._hull_upgrade = 20
        self._max_power = 100
        self._power = 100
        self._weapon = 0
        self._weapon_upgrade = 0
        self._engine = 10
        self._evasion = 0
        self._max_cargo_size = 200000
        self._cargo_size = 0
        self._base_repair_cost = 1250
        self._base_upgrade_cost = 5000
        self._max_level = 20
        self._mining = 3

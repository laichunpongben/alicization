# destroyer.py

from .spaceship import Spaceship


class Destroyer(Spaceship):
    def __init__(self):
        Spaceship.__init__(self)
        self._ship_class = "destroyer"
        self._max_shield = 3600
        self._shield = 3600
        self._shield_upgrade = 360
        self._max_armor = 3600
        self._armor = 3600
        self._armor_upgrade = 360
        self._max_hull = 3600
        self._hull = 3600
        self._hull_upgrade = 360
        self._max_power = 3600
        self._power = 3700
        self._weapon = 1800
        self._weapon_upgrade = 180
        self._engine = 3600
        self._max_cargo_size = 80000
        self._base_repair_cost = 125000
        self._base_upgrade_cost = 1000000
        self._max_level = 40
        self._mining = 0

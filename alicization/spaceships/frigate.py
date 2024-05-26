# frigate.py

from .spaceship import Spaceship


class Frigate(Spaceship):
    def __init__(self):
        Spaceship.__init__(self)
        self._ship_class = "frigate"
        self._max_shield = 300
        self._shield = 300
        self._shield_upgrade = 30
        self._max_armor = 300
        self._armor = 300
        self._armor_upgrade = 30
        self._max_hull = 300
        self._hull = 300
        self._hull_upgrade = 30
        self._max_power = 300
        self._power = 300
        self._weapon = 150
        self._weapon_upgrade = 15
        self._engine = 300
        self._max_cargo_size = 40000
        self._base_repair_cost = 10000
        self._base_upgrade_cost = 20000
        self._max_level = 30
        self._mining = 0

# explorer.py

from .spaceship import Spaceship


class Explorer(Spaceship):
    def __init__(self):
        Spaceship.__init__(self)
        self._ship_class = "explorer"
        self._max_shield = 20
        self._shield = 20
        self._shield_upgrade = 0
        self._max_armor = 20
        self._armor = 20
        self._armor_upgrade = 0
        self._max_hull = 20
        self._hull = 20
        self._hull_upgrade = 0
        self._max_power = 20
        self._power = 20
        self._weapon = 0
        self._weapon_upgrade = 0
        self._engine = 10
        self._evasion = 0
        self._max_cargo_size = 10000
        self._base_repair_cost = 10
        self._base_upgrade_cost = 0
        self._max_level = 0
        self._mining = 1

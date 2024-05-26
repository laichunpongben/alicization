# miner.py

from .spaceship import Spaceship


class Miner(Spaceship):
    def __init__(self):
        Spaceship.__init__(self)
        self._ship_class = "miner"
        self._max_shield = 50
        self._shield = 50
        self._shield_upgrade = 5
        self._max_armor = 50
        self._armor = 50
        self._armor_upgrade = 5
        self._max_hull = 50
        self._hull = 50
        self._hull_upgrade = 5
        self._max_power = 100
        self._power = 100
        self._weapon = 0
        self._weapon_upgrade = 0
        self._engine = 10
        self._max_cargo_size = 100000
        self._base_repair_cost = 100
        self._base_upgrade_cost = 200
        self._max_level = 10
        self._mining = 2

# corvette.py

from .spaceship import Spaceship


class Corvette(Spaceship):
    def __init__(self):
        Spaceship.__init__(self)
        self._ship_class = "corvette"
        self._max_shield = 100
        self._shield = 100
        self._shield_upgrade = 10
        self._max_armor = 100
        self._armor = 100
        self._armor_upgrade = 10
        self._max_hull = 100
        self._hull = 100
        self._hull_upgrade = 10
        self._max_power = 100
        self._power = 100
        self._weapon = 50
        self._weapon_upgrade = 5
        self._engine = 10
        self._evasion = 0.1
        self._max_cargo_size = 20000
        self._base_repair_cost = 200
        self._base_upgrade_cost = 400
        self._max_level = 20
        self._mining = 0

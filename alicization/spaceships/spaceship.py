# spaceship.py

from abc import ABC, abstractmethod
from collections import defaultdict
import logging

from ..managers.material_manager import MaterialManager

material_manager = MaterialManager()

logger = logging.getLogger(__name__)

DEFAULT_VOLUME = 10


class Spaceship(ABC):
    def __init__(self):
        self._ship_class = "<SHIP_CLASS>"
        self._max_shield = 0
        self._shield = 0
        self._shield_upgrade = 0
        self._max_armor = 0
        self._armor = 0
        self._armor_upgrade = 0
        self._max_hull = 0
        self._hull = 0
        self._hull_upgrade = 0
        self._max_power = 0
        self._power = 0
        self._weapon = 0
        self._weapon_upgrade = 0
        self._engine = 0
        self._evasion = 0
        self._max_cargo_size = 0
        self._base_repair_cost = 0
        self._base_upgrade_cost = 0
        self._max_level = 0
        self._level = 0
        self._mining = 1
        self._cargo_hold = defaultdict(int)
        self._destroyed = False

    @property
    def ship_class(self):
        return self._ship_class

    @property
    def max_shield(self):
        return self._max_shield

    @property
    def shield(self):
        return self._shield

    @shield.setter
    def shield(self, value):
        self._shield = value

    @property
    def shield_upgrade(self):
        return self._shield_upgrade

    @property
    def max_armor(self):
        return self._max_armor

    @property
    def armor(self):
        return self._armor

    @armor.setter
    def armor(self, value):
        self._armor = value

    @property
    def armor_upgrade(self):
        return self._armor_upgrade

    @property
    def max_hull(self):
        return self._max_hull

    @property
    def hull_upgrade(self):
        return self._hull_upgrade

    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = value

    @property
    def max_power(self):
        return self._max_power

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value):
        self._power = value

    @property
    def weapon(self):
        return self._weapon

    @weapon.setter
    def weapon(self, value):
        self._weapon = value

    @property
    def weapon_upgrade(self):
        return self._weapon_upgrade

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        self._engine = value

    @property
    def evasion(self):
        return self._evasion

    @property
    def max_cargo_size(self):
        return self._max_cargo_size

    @property
    def cargo_hold(self):
        return self._cargo_hold

    @cargo_hold.setter
    def cargo_hold(self, value):
        self._cargo_hold = value

    @property
    def base_repair_cost(self):
        return self._base_repair_cost

    @property
    def base_upgrade_cost(self):
        return self._base_upgrade_cost

    @property
    def level(self):
        return self._level

    @property
    def max_level(self):
        return self._max_level

    @property
    def mining(self):
        return self._mining

    @property
    def destroyed(self):
        return self._destroyed

    @destroyed.setter
    def destroyed(self, value):
        self._destroyed = value

    def is_damaged(self):
        return self._armor < self._max_armor or self._hull < self._max_hull

    def take_damage(self, damage):
        if damage >= self._shield:
            damage -= self._shield
            self._shield = 0
            if damage > 0:
                if damage >= self._armor:
                    damage -= self._armor
                    self._armor = 0
                    if damage > 0:
                        if damage > self._hull:
                            self._hull = 0
                            self._destroyed = True
                        else:
                            self._hull -= damage
                else:
                    self._armor -= damage
                    damage = 0
        else:
            self._shield -= damage
            damage = 0

    def recharge_shield(self):
        self._shield = min(self._shield + int(self._max_shield / 10), self._max_shield)

    def recharge_shield_full(self):
        self._shield = self._max_shield

    def calc_repair_cost(self):
        return (1 + self._level / 10) * self._base_repair_cost

    def repair(self):
        self._shield = self._max_shield
        self._armor = self._max_armor
        self._hull = self._max_hull
        logger.debug("Spaceship repair done!")

    def calc_upgrade_cost(self):
        return (1 + self._level / 2) * self._base_upgrade_cost

    def calculate_cargo_size(self):
        cargo_size = 0
        for item, quantity in self._cargo_hold.items():
            material = material_manager.get_material(item)
            if material:
                volume = (
                    material.volume if hasattr(material, "volume") else DEFAULT_VOLUME
                )
                cargo_size += volume * quantity

        return cargo_size

    def is_cargo_full(self):
        cargo_size = self.calculate_cargo_size()
        return cargo_size >= self._max_cargo_size

    def is_cargo_empty(self):
        cargo_size = self.calculate_cargo_size()
        return cargo_size <= 0

    def upgrade(self):
        if self._level < self._max_level:
            self._weapon += self._weapon_upgrade
            self._max_shield += self._shield_upgrade
            self._max_armor += self._armor_upgrade
            self._max_hull += self._hull_upgrade
            self._shield = self._max_shield
            self._armor = self._max_armor
            self._hull = self._max_hull
            self._level += 1
            logger.debug("Spaceship upgrade done!")
        else:
            logger.debug("Spaceship max upgrade reached!")

    def to_json(self):
        return {
            "shipClass": self.ship_class,
            "maxShield": self.max_shield,
            "shield": self.shield,
            "shieldUpgrade": self.shield_upgrade,
            "maxArmor": self.max_armor,
            "armor": self.armor,
            "armorUpgrade": self.armor_upgrade,
            "maxHull": self.max_hull,
            "hull": self.hull,
            "hullUpgrade": self.hull_upgrade,
            "maxPower": self.max_power,
            "power": self.power,
            "weapon": self.weapon,
            "weaponUpgrade": self.weapon_upgrade,
            "engine": self.engine,
            "maxCargoSize": self.max_cargo_size,
            "baseRepairCost": self.base_repair_cost,
            "baseUpgradeCost": self.base_upgrade_cost,
            "level": self.level,
            "maxLevel": self.max_level,
            "mining": self.mining,
            "cargoHold": dict(self.cargo_hold),
            "destroyed": self.destroyed,
        }

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
        self._base_shield_recharge = 0
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

    @ship_class.setter
    def ship_class(self, value):
        self._ship_class = value

    @property
    def max_shield(self):
        return self._max_shield

    @max_shield.setter
    def max_shield(self, value):
        self._max_shield = value

    @property
    def shield(self):
        return self._shield

    @shield.setter
    def shield(self, value):
        self._shield = value

    @property
    def shield_upgrade(self):
        return self._shield_upgrade

    @shield_upgrade.setter
    def shield_upgrade(self, value):
        self._shield_upgrade = value

    @property
    def max_armor(self):
        return self._max_armor

    @max_armor.setter
    def max_armor(self, value):
        self._max_armor = value

    @property
    def armor(self):
        return self._armor

    @armor.setter
    def armor(self, value):
        self._armor = value

    @property
    def armor_upgrade(self):
        return self._armor_upgrade

    @armor_upgrade.setter
    def armor_upgrade(self, value):
        self._armor_upgrade = value

    @property
    def max_hull(self):
        return self._max_hull

    @max_hull.setter
    def max_hull(self, value):
        self._max_hull = value

    @property
    def hull_upgrade(self):
        return self._hull_upgrade

    @hull_upgrade.setter
    def hull_upgrade(self, value):
        self._hull_upgrade = value

    @property
    def hull(self):
        return self._hull

    @hull.setter
    def hull(self, value):
        self._hull = value

    @property
    def max_power(self):
        return self._max_power

    @max_power.setter
    def max_power(self, value):
        self._max_power = value

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

    @weapon_upgrade.setter
    def weapon_upgrade(self, value):
        self._weapon_upgrade = value

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, value):
        self._engine = value

    @property
    def base_shield_recharge(self):
        return self._base_shield_recharge

    @base_shield_recharge.setter
    def base_shield_recharge(self, value):
        self._base_shield_recharge = value

    @property
    def max_cargo_size(self):
        return self._max_cargo_size

    @max_cargo_size.setter
    def max_cargo_size(self, value):
        self._max_cargo_size = value

    @property
    def cargo_hold(self):
        return self._cargo_hold

    @cargo_hold.setter
    def cargo_hold(self, value):
        self._cargo_hold = value

    @property
    def base_repair_cost(self):
        return self._base_repair_cost

    @base_repair_cost.setter
    def base_repair_cost(self, value):
        self._base_repair_cost = value

    @property
    def base_upgrade_cost(self):
        return self._base_upgrade_cost

    @base_upgrade_cost.setter
    def base_upgrade_cost(self, value):
        self._base_upgrade_cost = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value

    @property
    def max_level(self):
        return self._max_level

    @max_level.setter
    def max_level(self, value):
        self._max_level = value

    @property
    def mining(self):
        return self._mining

    @mining.setter
    def mining(self, value):
        self._mining = value

    @property
    def destroyed(self):
        return self._destroyed

    @destroyed.setter
    def destroyed(self, value):
        self._destroyed = value

    def is_damaged(self):
        return self.armor < self.max_armor or self.hull < self.max_hull

    def take_damage(self, damage):
        if damage >= self.shield:
            damage -= self.shield
            self.shield = 0
            if damage > 0:
                if damage >= self.armor:
                    damage -= self.armor
                    self.armor = 0
                    if damage > 0:
                        if damage > self.hull:
                            self.hull = 0
                            self.destroyed = True
                        else:
                            self.hull -= damage
                else:
                    self.armor -= damage
                    damage = 0
        else:
            self.shield -= damage
            damage = 0

    def recharge_shield(self):
        self.shield = min(self.shield + self.base_shield_recharge, self.max_shield)

    def calc_repair_cost(self):
        return (1 + self.level / 10) * self.base_repair_cost

    def repair(self):
        self.shield = self.max_shield
        self.armor = self.max_armor
        self.hull = self.max_hull
        logger.debug("Spaceship repair done!")

    def calc_upgrade_cost(self):
        return (1 + self.level / 2) * self.base_upgrade_cost

    def calculate_cargo_size(self):
        cargo_size = 0
        for item, quantity in self.cargo_hold.items():
            material = material_manager.get_material(item)
            if material:
                volume = (
                    material.volume if hasattr(material, "volume") else DEFAULT_VOLUME
                )
                cargo_size += volume * quantity
        return cargo_size

    def is_cargo_full(self):
        cargo_size = self.calculate_cargo_size()
        return cargo_size >= self.max_cargo_size

    def is_cargo_empty(self):
        cargo_size = self.calculate_cargo_size()
        return cargo_size <= 0

    def upgrade(self):
        if self.level < self.max_level:
            self.weapon += self.weapon_upgrade
            self.max_shield += self.shield_upgrade
            self.max_armor += self.armor_upgrade
            self.max_hull += self.hull_upgrade
            self.shield = self.max_shield
            self.armor = self.max_armor
            self.hull = self.max_hull
            self.level += 1
            logger.debug("Spaceship upgrade done!")
        else:
            logger.debug("Spaceship max upgrade reached!")

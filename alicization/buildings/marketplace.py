# marketplace.py

import math
import uuid
import logging

from .building import Building
from ..managers.material_manager import MaterialManager
from ..managers.spaceship_manager import SpaceshipManager
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)

material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()
leaderboard = Leaderboard()


class Marketplace(Building):
    def __init__(self):
        Building.__init__(self)
        self.name = f"Marketplace {uuid.uuid4().hex}"
        self.inventory = {}
        self.load_materials()
        self.load_spaceships()

    def load_materials(self):
        for material in material_manager.materials.values():
            rarity = material.rarity
            base_price = material_manager.guess_base_price(rarity)
            self.inventory[material.name] = {"quantity": 0, "price": base_price}

    def load_spaceships(self):
        for spaceship_info in spaceship_manager.spaceships.values():
            self.inventory[spaceship_info.ship_class] = {
                "quantity": 0,
                "price": spaceship_info.base_price,
            }

    def get_target_quantity(self, item_type):
        default_target_quantity = 50

        material = material_manager.get_material(item_type)
        if material:
            rarity_based_target_quantities = {
                1: 100,  # Common
                2: 75,  # Uncommon
                3: 50,  # Rare
                4: 25,  # Epic
                5: 10,  # Legendary
            }
            return rarity_based_target_quantities.get(
                material.rarity, default_target_quantity
            )

        spaceship = spaceship_manager.get_spaceship(item_type)
        if spaceship:
            return 5

        return default_target_quantity

    def update_price(self, item_type):
        data = self.inventory[item_type]
        quantity = data["quantity"]
        price = data["price"]

        scaling_factor = 0.01
        target_quantity = self.get_target_quantity(item_type)

        # Cap the price adjustment for shortage
        max_shortage_factor = 5
        if quantity > target_quantity:
            oversupply_factor = quantity / target_quantity
            price_adjustment = math.log(oversupply_factor)
            price = price / (1 + price_adjustment * scaling_factor)
        elif quantity < target_quantity:
            shortage_factor = target_quantity / max(quantity, 1)
            price_adjustment = min(math.log(shortage_factor), max_shortage_factor)
            price = price * (1 + price_adjustment * scaling_factor)

        self.inventory[item_type]["price"] = max(price, 0.01)

    def buy(self, player, item_type, quantity):
        if self._cooldown > 0:
            return False

        if item_type in self.inventory:
            item = self.inventory[item_type]
            total_cost = 0
            step = 10

            while quantity > 0 and item["quantity"] > 0:
                current_step = min(step, quantity)
                current_step = min(current_step, item["quantity"])
                unit_price = item["price"]
                step_cost = unit_price * current_step

                if player.wallet >= step_cost:
                    player.spend(step_cost)
                    player.current_location.storage.add_item(player, item_type, current_step)
                    item["quantity"] -= current_step
                    total_cost += step_cost
                    quantity -= current_step
                    self.update_price(item_type)
                else:
                    break

            return total_cost > 0
        return False

    def sell(self, player, item_type, quantity):
        if self._cooldown > 0:
            return False

        if item_type in self.inventory:
            item = self.inventory[item_type]
            total_income = 0
            step = 10

            while quantity > 0 and player.current_location.storage.get_item(player, item_type) > 0:
                current_step = min(step, quantity)
                current_step = min(current_step, player.current_location.storage.get_item(player, item_type))
                unit_price = item["price"]
                step_income = unit_price * current_step

                player.wallet += step_income
                player.current_location.storage.remove_item(player, item_type, current_step)
                item["quantity"] += current_step
                total_income += step_income
                quantity -= current_step
                self.update_price(item_type)

            return total_income > 0
        return False

    def reset(self):
        self._hull = self._max_hull
        self._cooldown = 10000
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

    def debug_print(self):
        logger.info("Marketplace:")
        for item_type, data in self.inventory.items():
            logger.info(
                f"{item_type}: {data['quantity']} units at {data['price']} each"
            )

# storage.py

import uuid
import logging

from .building import Building

logger = logging.getLogger(__name__)


class Storage(Building):
    def __init__(self):
        Building.__init__(self)
        self.name = f"Storage {uuid.uuid4().hex}"
        self.inventory = {}

    def add_item(self, player_name: str, item: str, qty: int):
        if player_name not in self.inventory:
            self.inventory[player_name] = {}

        if item in self.inventory[player_name]:
            self.inventory[player_name][item] += qty
        else:
            self.inventory[player_name][item] = qty

        logger.info(f"Added {qty} of {item} to player {player_name}'s storage.")

    def remove_item(self, player_name: str, item: str, qty: int):
        if player_name not in self.inventory or item not in self.inventory[player_name]:
            logger.warning(
                f"Player {player_name} does not have {item} in their storage."
            )
            return False

        if self.inventory[player_name][item] < qty:
            logger.warning(
                f"Player {player_name} does not have enough {item} to remove {qty}."
            )
            return False

        self.inventory[player_name][item] -= qty

        logger.info(f"Removed {qty} of {item} from player {player_name}'s storage.")
        return True

    def get_item(self, player_name: str, item: str):
        return self.inventory.get(player_name, {}).get(item, 0)

    def get_inventory(self, player_name: str):
        return self.inventory.get(player_name, {})

    def destroy(self):
        pass

    def reset(self):
        self._hull = self._max_hull
        self._cooldown = 10000
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

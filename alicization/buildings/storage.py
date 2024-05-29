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

    def add_item(self, player, item, qty):
        if player.name not in self.inventory:
            self.inventory[player.name] = {}

        if item in self.inventory[player.name]:
            self.inventory[player.name][item] += qty
        else:
            self.inventory[player.name][item] = qty

        logger.info(f"Added {qty} of {item} to player {player.name}'s storage.")

    def remove_item(self, player, item, qty):
        if player.name not in self.inventory or item not in self.inventory[player.name]:
            logger.warning(
                f"Player {player.name} does not have {item} in their storage."
            )
            return False

        if self.inventory[player.name][item] < qty:
            logger.warning(
                f"Player {player.name} does not have enough {item} to remove {qty}."
            )
            return False

        self.inventory[player.name][item] -= qty

        if self.inventory[player.name][item] == 0:
            del self.inventory[player.name][item]

        logger.info(f"Removed {qty} of {item} from player {player.name}'s storage.")
        return True

    def get_item(self, player, item):
        return self.inventory.get(player.name, {}).get(item, 0)

    def get_inventory(self, player):
        return self.inventory.get(player.name, {})

    def reset(self):
        self._hull = self._max_hull
        self._cooldown = 10000
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

# players/actions/spaceship_piloting.py

import random
import logging

from ...managers.player_manager import PlayerManager
from ...spaceships.explorer import Explorer
from ...spaceships.miner import Miner
from ...spaceships.extractor import Extractor
from ...spaceships.corvette import Corvette
from ...spaceships.frigate import Frigate
from ...spaceships.destroyer import Destroyer
from ...spaceships.courier import Courier

logger = logging.getLogger(__name__)

player_manager = PlayerManager()


def pilot(player, new_spaceship_class: str):
    current_location = player_manager.get_location(player.name)
    old_spaceship = player_manager.get_spaceship(player.name)
    if can_pilot(player, current_location, new_spaceship_class):
        if new_spaceship_class != "explorer":
            new_spaceship = current_location.hangar.remove_spaceship(
                player, new_spaceship_class
            )
            if new_spaceship is None:
                current_location.storage.remove_item(
                    player.name, new_spaceship_class, 1
                )
                new_spaceship = create_spaceship_instance(new_spaceship_class)
        else:
            new_spaceship = create_spaceship_instance(new_spaceship_class)

        if new_spaceship is not None:
            if old_spaceship is not None and not old_spaceship.destroyed:
                for item, count in old_spaceship.cargo_hold.items():
                    new_spaceship.cargo_hold[item] += count
                    old_spaceship.cargo_hold[item] = 0

                if not isinstance(old_spaceship, Explorer):
                    current_location.hangar.add_spaceship(player, old_spaceship)

            new_spaceship.recharge_shield()
            player_manager.update_spaceship(player.name, new_spaceship)

            logger.info(
                f"{player.name} piloted a {new_spaceship_class} spaceship at {current_location.name}"
            )
        else:
            logger.warning(f"No {new_spaceship_class} spaceship")
    else:
        logger.warning(
            f"Cannot pilot {new_spaceship_class} spaceship from this location."
        )


def unload(player):
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_unload(current_location, spaceship):
        for item, qty in spaceship.cargo_hold.items():
            current_location.storage.add_item(player.name, item, qty)
        spaceship.empty_cargo_hold()
        logger.info(f"{player.name} unloaded cargo at {current_location.name}")
    else:
        logger.warning("Cannot unload cargo from this location.")


def load(player):
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    if can_load(player, current_location, spaceship):
        for item, max_qty in current_location.storage.get_inventory(
            player.name
        ).items():
            qty = random.randint(0, max_qty)
            if not spaceship.is_cargo_full():
                spaceship.cargo_hold[item] += qty
                current_location.storage.remove_item(player.name, item, qty)
        logger.info(f"{player.name} loaded cargo at {current_location.name}")
    else:
        logger.warning("Cannot load cargo from this location.")


def can_pilot(player, current_location, spaceship_class: str):
    return (
        (
            current_location.has_hangar()
            and current_location.hangar.has_spaceship(player, spaceship_class)
        )
        or (
            current_location.has_storage()
            and current_location.storage.get_item(player.name, spaceship_class) > 0
        )
        or spaceship_class == "explorer"
    )


def can_unload(current_location, spaceship):
    return current_location.has_storage() and not spaceship.is_cargo_empty()


def can_load(player, current_location, spaceship):
    return (
        current_location.has_storage()
        and bool(current_location.storage.get_inventory(player.name))
        and not spaceship.is_cargo_full()
    )


def create_spaceship_instance(spaceship_class: str):
    cls_map = {
        "explorer": Explorer,
        "miner": Miner,
        "extractor": Extractor,
        "corvette": Corvette,
        "frigate": Frigate,
        "destroyer": Destroyer,
        "courier": Courier,
    }
    cls = cls_map.get(spaceship_class)
    return cls() if cls is not None else None

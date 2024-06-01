# players/actions/movement.py

import random
import logging

from ...managers.player_manager import PlayerManager
from ...managers.material_manager import MaterialManager
from ...managers.spaceship_manager import SpaceshipManager
from ...managers.economy import Economy

logger = logging.getLogger(__name__)

player_manager = PlayerManager()
material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()
economy = Economy()

DEFAULT_SPACESHIP_COST = 1
MIN_UNIT_PRICE = 0.0001
ASK_MARGIN = 0.5
BID_MARGIN = 0.2


def buy(player, item_type: str, quantity: int, price: float) -> None:
    current_location = player_manager.get_location(player.name)
    if can_buy(player, current_location, quantity, price):
        if current_location.marketplace.place_bid_order(
            player, item_type, quantity, price
        ):
            logger.debug(
                f"{player.name} placed bid order for {item_type}: {quantity}@{price}"
            )
            return True
        else:
            logger.warning(
                f"{player.name} failed to place bid order for {item_type}: {quantity}@{price}"
            )
            return False
    else:
        logger.warning("Cannot buy from this location.")
        return False


def sell(
    player, item_type: str, quantity: int, min_price: float, buyout_price: float
) -> None:
    current_location = player_manager.get_location(player.name)
    if can_sell(player, current_location, item_type, quantity):
        if current_location.marketplace.place_ask_order(
            player, item_type, quantity, min_price, buyout_price
        ):
            logger.debug(
                f"{player.name} placed ask order for {item_type}: {quantity}@{min_price}/{buyout_price}"
            )
            return True
        else:
            logger.warning(
                f"{player.name} failed to place ask order for {item_type}: {quantity}@{min_price}/{buyout_price}"
            )
            return False
    else:
        logger.warning("Cannot sell from this location.")
        return False


def buy_material(player, item_type: str, margin: float) -> None:
    current_location = player_manager.get_location(player.name)
    material = material_manager.get_material(item_type)
    if material:
        base_price = material_manager.guess_base_price(material.rarity)
    else:
        base_price = MIN_UNIT_PRICE

    bid_price = max(
        round(base_price * player.affordability * (1 + margin), 4), MIN_UNIT_PRICE
    )
    if can_buy(player, current_location, 1, bid_price):
        spend_factor = 0.1
        max_qty = max(int(player.wallet * spend_factor / bid_price), 0)
        if max_qty > 1:
            qty = random.randint(1, max_qty)
        elif max_qty == 1:
            qty = 1
        else:
            qty = 0

        if qty > 0 and buy(player, item_type, qty, bid_price):
            logger.info(
                f"{player.name} placed a bid order for {item_type} at {current_location.name}"
            )
        else:
            logger.warning(f"Not enough money to buy material {item_type}")
    else:
        logger.warning(f"Cannot buy material {item_type} from this location.")


def buy_random_material(player, margin: float) -> None:
    sampled_max_rarity = random.choices(
        [1, 2, 3, 4, 5], weights=[80, 32, 12, 4, 1], k=1
    )[0]
    material = material_manager.random_material(max_rarity=sampled_max_rarity)
    item_type = material.name
    buy_material(player, item_type, margin)


def buy_random_material_random_margin(player) -> None:
    margin = random_bid_margin()
    buy_random_material(player, margin)


def sell_material(
    player, item_type: str, lower_margin: float, upper_margin: float
) -> None:
    current_location = player_manager.get_location(player.name)
    if can_sell(player, current_location, item_type, 1):
        material = material_manager.get_material(item_type)
        if material:
            base_price = material_manager.guess_base_price(material.rarity)
        else:
            base_price = MIN_UNIT_PRICE

        buyout_price = max(
            round(base_price / player.productivity * (1 + upper_margin), 4),
            MIN_UNIT_PRICE,
        )
        min_price = max(
            round(base_price / player.productivity * (1 + lower_margin), 4),
            MIN_UNIT_PRICE,
        )

        max_qty = current_location.storage.get_item(player.name, item_type)
        if max_qty > 1:
            qty = random.randint(1, max_qty)
        elif max_qty == 1:
            qty = 1
        else:
            qty = 0

        if qty > 0 and sell(player, item_type, qty, min_price, buyout_price):
            logger.info(
                f"{player.name} placed an ask order for {item_type} at {current_location.name}"
            )
        else:
            logger.warning(f"Not enough material {item_type} for sell")
    else:
        logger.warning("No available material for selling")


def sell_random_material(player, lower_margin: float, upper_margin: float) -> None:
    current_location = player_manager.get_location(player.name)
    if current_location.has_storage():
        available_materials = [
            (item, qty)
            for item, qty in current_location.storage.get_inventory(player.name).items()
            if qty > 0 and material_manager.get_material(item)
        ]
        if available_materials:
            item_type, _ = random.choice(available_materials)
            sell_material(player, item_type, lower_margin, upper_margin)


def sell_random_material_random_margin(player) -> None:
    upper_margin = random_ask_margin()
    lower_margin = upper_margin - 1
    sell_random_material(player, lower_margin, upper_margin)


def buy_spaceship(player, spaceship_class: str, margin: float) -> None:
    current_location = player_manager.get_location(player.name)
    spaceship_info = spaceship_manager.get_spaceship(spaceship_class)
    if spaceship_info:
        base_price = spaceship_info.base_price
    else:
        base_price = DEFAULT_SPACESHIP_COST

    bid_price = max(
        round(base_price * player.affordability * (1 + margin), 4),
        MIN_UNIT_PRICE,
    )
    if can_buy(player, current_location, 1, bid_price):
        if buy(player, spaceship_class, 1, bid_price):
            logger.info(
                f"{player.name} placed a bid order for {spaceship_class} at {current_location.name}"
            )
        else:
            logger.warning(f"Not enough money to buy spaceship {spaceship_class}")
    else:
        logger.warning(f"Cannot buy spaceship {spaceship_class} from this location.")


def random_bid_margin() -> float:
    price_index = economy.galactic_price_index
    min_ = min(0, price_index * (1 + BID_MARGIN) - 1)
    max_ = max(0, price_index * (1 + BID_MARGIN) - 1)
    return max(random.uniform(min_, max_), 0)


def buy_spaceship_random_margin(player, spaceship_class: str) -> None:
    margin = random_bid_margin()
    return buy_spaceship(player, spaceship_class, margin)


def sell_spaceship(
    player, spaceship_class: str, lower_margin: float, upper_margin: float
) -> None:
    current_location = player_manager.get_location(player.name)
    if can_sell(player, current_location, spaceship_class, 1):
        spaceship_info = spaceship_manager.get_spaceship(spaceship_class)
        if spaceship_info:
            base_price = spaceship_info.base_price
        else:
            base_price = DEFAULT_SPACESHIP_COST

        min_price = max(
            round(base_price / player.productivity * (1 + lower_margin), 4),
            MIN_UNIT_PRICE,
        )
        buyout_price = max(
            round(base_price / player.productivity * (1 + upper_margin), 4),
            MIN_UNIT_PRICE,
        )

        max_qty = current_location.storage.get_item(player.name, spaceship_class)
        if max_qty > 1:
            qty = random.randint(1, max_qty)
        elif max_qty == 1:
            qty = 1

        if sell(player, spaceship_class, qty, min_price, buyout_price):
            logger.info(
                f"{player.name} sold a {spaceship_class} at {current_location.name}"
            )
    else:
        logger.warning("Cannot sell spaceship from this location.")


def random_ask_margin() -> float:
    price_index = economy.galactic_price_index
    min_ = min(price_index - 1, price_index * (1 + ASK_MARGIN) - 1)
    max_ = max(price_index - 1, price_index * (1 + ASK_MARGIN) - 1)
    return max(random.uniform(min_, max_), 0)


def sell_spaceship_random_margin(player, spaceship_class: str) -> bool:
    upper_margin = random_ask_margin()
    lower_margin = upper_margin - 1
    sell_spaceship(player, spaceship_class, lower_margin, upper_margin)


def can_buy(player, current_location, quantity: int, price: float) -> bool:
    return (
        current_location.has_marketplace()
        and current_location.has_storage()
        and player.wallet >= quantity * price
    )


def can_sell(player, current_location, item_type: str, quantity: int) -> bool:
    return (
        current_location.has_marketplace()
        and current_location.has_storage()
        and current_location.storage.get_item(player.name, item_type) >= quantity
    )


def can_buy_spaceship(player, current_location) -> bool:
    return (
        current_location.has_marketplace()
        and current_location.has_storage()
        and player.wallet >= 0
    )


def can_buy_material(player, current_location) -> bool:
    return (
        current_location.has_marketplace()
        and current_location.has_storage()
        and player.wallet >= 0
    )


def can_sell_material(player, current_location) -> bool:
    return (
        current_location.has_marketplace()
        and current_location.has_storage()
        and bool(current_location.storage.get_inventory(player.name))
    )

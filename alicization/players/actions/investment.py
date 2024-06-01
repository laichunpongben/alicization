# players/actions/investment.py

import random
import logging

from ...managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

player_manager = PlayerManager()

INVESTABLE_BUILDINGS = ["factory", "drydock", "marketplace"]
check_building_method_map = {
    "factory": "has_factory",
    "drydock": "has_drydock",
    "marketplace": "has_marketplace",
}


def invest(player, building_name: str, amount: float) -> None:
    current_location = player_manager.get_location(player.name)
    if can_invest(player, current_location, building_name):
        if player.wallet >= amount:
            building = getattr(current_location, building_name)
            building.invest(player, amount)
            logger.debug(
                f"{player.name} invested {amount} at the {building_name} at {current_location.name}"
            )
        else:
            logger.warning(f"{player.name} failed to invest {amount}")
    else:
        logger.warning("Cannot invest from this location.")


def invest_random_amount(player, building_name: str) -> None:
    spend_factor = 0.01
    amount = random.randint(0, max(int(player.wallet * spend_factor), 0))
    invest(player, building_name, amount)


def collect(player) -> None:
    current_location = player_manager.get_location(player.name)
    if can_collect(player, current_location):
        payout = 0
        for building_name in INVESTABLE_BUILDINGS:
            if hasattr(current_location, building_name):
                building = getattr(current_location, building_name)
                payout += building.profit(player)
        logger.debug(f"{player.name} collected {payout} at {current_location.name}")
    else:
        logger.warning("Cannot collect from this location.")


def can_invest(player, current_location, building_name: str) -> bool:
    method_name = check_building_method_map.get(building_name)
    if method_name is not None:
        method = getattr(current_location, method_name)
        return method() and player.wallet > 0
    return False


def can_collect(player, current_location) -> bool:
    checks = []
    for building_name in INVESTABLE_BUILDINGS:
        method_name = check_building_method_map.get(building_name)
        if method_name is not None:
            method = getattr(current_location, method_name)
            if method():
                building = getattr(current_location, building_name)
                check = building.equities[player.name] > 0
            else:
                check = False
        else:
            check = False
        checks.append(check)
    return any(checks)

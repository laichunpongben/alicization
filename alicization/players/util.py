# players/util.py

import math
import logging
from dataclasses import dataclass, field
from collections import deque

from ..locations.planet import Planet
from ..locations.moon import Moon
from ..locations.asteroid_belt import AsteroidBelt
from ..locations.stargate import Stargate
from ..locations.debris import Debris
from ..locations.empty_space import EmptySpace
from ..spaceships.explorer import Explorer
from ..spaceships.miner import Miner
from ..spaceships.extractor import Extractor
from ..spaceships.corvette import Corvette
from ..spaceships.frigate import Frigate
from ..spaceships.destroyer import Destroyer
from ..spaceships.courier import Courier
from ..managers.player_manager import PlayerManager
from ..managers.material_manager import MaterialManager
from ..managers.spaceship_manager import SpaceshipManager
from ..managers.economy import Economy
from ..managers.leaderboard import Leaderboard
from ..util import (
    calculate_minimum_distance,
)

logger = logging.getLogger(__name__)

player_manager = PlayerManager()
material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()
economy = Economy()
leaderboard = Leaderboard()

MIN_UNIT_PRICE = 0.0001


def get_current_spaceship_type(spaceship) -> int:
    if isinstance(spaceship, Explorer):
        return 1
    elif isinstance(spaceship, Miner):
        return 2
    elif isinstance(spaceship, Extractor):
        return 3
    elif isinstance(spaceship, Corvette):
        return 4
    elif isinstance(spaceship, Frigate):
        return 5
    elif isinstance(spaceship, Destroyer):
        return 6
    elif isinstance(spaceship, Courier):
        return 7
    else:
        return 0


def get_current_location_type(current_location) -> int:
    if isinstance(current_location, EmptySpace):
        return 1
    elif isinstance(current_location, Planet):
        return 2
    elif isinstance(current_location, AsteroidBelt):
        return 3
    elif isinstance(current_location, Moon):
        return 4
    elif isinstance(current_location, Stargate):
        return 5
    elif isinstance(current_location, Debris):
        return 6
    else:
        return 0


def calculate_distance_from_home(player, current_system, home_system) -> int:
    universe = player_manager.get_universe(player.name)
    star_systems = universe.star_systems
    distance = calculate_minimum_distance(star_systems, current_system, home_system)
    logger.debug(f"Distance from home is {distance}")
    return distance


def calculate_net_worth(player, universe) -> float:
    inventory_worth = calculate_inventory_worth(player, universe)
    spaceship_worth = calculate_spaceship_worth(player, universe)
    marketplace_reserve = calculate_marketplace_reserve(player, universe)
    net_worth = (
        player.wallet
        + inventory_worth
        + spaceship_worth
        + marketplace_reserve
        + player.total_investment * 0.1
    )
    return net_worth


def calculate_inventory_worth(player, universe) -> float:
    inventory_worth = 0
    base_price_cache = {}
    for system in universe.star_systems:
        for planet in system.planets:
            inventory = planet.storage.get_inventory(player.name)
            for item_type, quantity in inventory.items():
                if item_type not in base_price_cache:
                    material = material_manager.get_material(item_type)
                    if material:
                        base_price_cache[item_type] = material_manager.guess_base_price(
                            material.rarity
                        )
                    else:
                        spaceship_info = spaceship_manager.get_spaceship(item_type)
                        if spaceship_info:
                            base_price_cache[item_type] = spaceship_info.base_price
                        else:
                            logger.error(f"Missing price info: {item_type}")
                            base_price_cache[item_type] = MIN_UNIT_PRICE
                inventory_worth += (
                    base_price_cache[item_type]
                    * economy.galactic_price_index
                    * quantity
                )
    return inventory_worth


def calculate_spaceship_worth(player, universe) -> float:
    spaceship_worth = 0
    base_price_cache = {}
    for system in universe.star_systems:
        locations = system.planets + system.moons
        for location in locations:
            spaceships = location.hangar.get_spaceships(player)
            for spaceship in spaceships:
                ship_class = spaceship.ship_class
                if ship_class not in base_price_cache:
                    spaceship_info = spaceship_manager.get_spaceship(ship_class)
                    if spaceship_info:
                        base_price_cache[ship_class] = spaceship_info.base_price
                    else:
                        logger.error(f"Missing price info: {ship_class}")
                        base_price_cache[ship_class] = MIN_UNIT_PRICE
                spaceship_worth += (
                    base_price_cache[ship_class] * economy.galactic_price_index
                )
    return spaceship_worth


def calculate_marketplace_reserve(player, universe) -> float:
    reserve = 0
    for system in universe.star_systems:
        for planet in system.planets:
            marketplace = planet.marketplace
            reserve += (
                marketplace.wallet[player.name]
                + marketplace.inventory_estimate[player.name]
            )
    return reserve


def get_next_system_info(current_location):
    if isinstance(current_location, Stargate):
        distance = current_location.distance
        next_sys = current_location.destination
        return (
            distance,
            len(next_sys.stargates),
            len(next_sys.planets),
            len(next_sys.asteroid_belts),
            len(next_sys.moons),
        )
    else:
        return 0, 0, 0, 0, 0


def get_factory_info(current_location):
    return current_location.factory.level if current_location.has_factory() else 0


def get_mission_info(current_location):
    if current_location.has_mission_center():
        best_reward_mission = current_location.mission_center.get_best_reward_mission()
        if best_reward_mission is not None:
            difficulty = best_reward_mission.difficulty
            reward = (
                int(math.log(best_reward_mission.reward))
                if best_reward_mission.reward > 0
                else 0
            )
            return difficulty, reward
        else:
            return 0, 0
    else:
        return 0, 0


def calculate_roi(player) -> float:
    if player.total_investment > 0:
        return player.profit_collected / player.total_investment
    else:
        return 0


def calculate_total_investment(player, universe) -> float:
    investment = 0
    for system in universe.star_systems:
        for planet in system.planets:
            book = planet.factory.investment_book
            investment += book[player.name]
    return investment


def calculate_score(player) -> float:
    monopoly_score = leaderboard.get_achievement_score(player.name, "monopoly")
    mission_score = leaderboard.get_achievement_score(player.name, "mission")
    kill_score = leaderboard.get_achievement_score(player.name, "kill")
    destroy_score = leaderboard.get_achievement_score(player.name, "destroy")
    build_score = leaderboard.get_achievement_score(player.name, "build")
    score = monopoly_score + mission_score + kill_score + destroy_score + build_score
    return score


@dataclass
class EMAData:
    period: int
    ema: float = None
    k: float = field(default=None)

    def __post_init__(self):
        if self.k is None:
            self.k = 2 / (self.period + 1)


def calculate_ema_ratio(
    history: deque, turn_gain: float, short_ema_data: EMAData, long_ema_data: EMAData
) -> float:
    if len(history) >= short_ema_data.period:
        short_ema_data.ema = update_ema(short_ema_data.ema, turn_gain, short_ema_data.k)

    if len(history) >= long_ema_data.period:
        long_ema_data.ema = update_ema(long_ema_data.ema, turn_gain, long_ema_data.k)

    return compute_ema_ratio(short_ema_data.ema, long_ema_data.ema, history)


def update_ema(current_ema: float, new_value: float, k: int) -> float:
    return new_value if current_ema is None else new_value * k + current_ema * (1 - k)


def compute_ema_ratio(short_ema: float, long_ema: float, history: deque) -> float:
    if len(history) == history.maxlen and long_ema and short_ema and long_ema > 0:
        return min(max(short_ema / long_ema, 0.0001), 10000)
    return 1

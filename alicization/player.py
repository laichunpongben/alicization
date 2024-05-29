# player.py

import random
from collections import defaultdict, deque
import math
import logging

import numpy as np

from .agents.dqn_agent import DQNAgent
from .enums.control import Control
from .enums.goal import Goal
from .enums.action import Action
from .locations.planet import Planet
from .locations.moon import Moon
from .locations.asteroid_belt import AsteroidBelt
from .locations.stargate import Stargate
from .locations.debris import Debris
from .locations.empty_space import EmptySpace
from .locations.mineable import Mineable
from .managers.blueprint_manager import BlueprintManager
from .managers.material_manager import MaterialManager
from .managers.spaceship_manager import SpaceshipManager
from .managers.leaderboard import Leaderboard
from .spaceships.explorer import Explorer
from .spaceships.miner import Miner
from .spaceships.extractor import Extractor
from .spaceships.corvette import Corvette
from .spaceships.frigate import Frigate
from .spaceships.destroyer import Destroyer

logger = logging.getLogger(__name__)

blueprint_manager = BlueprintManager()
material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()
leaderboard = Leaderboard()

ACTION_ENUMS = [
    Action.IDLE,
    Action.MOVE_PLANET,
    Action.MOVE_ASTEROID_BELT,
    Action.MOVE_MOON,
    Action.MOVE_STARGATE,
    Action.MOVE_DEBRIS,
    Action.TRAVEL,
    Action.EXPLORE,
    Action.MINE,
    Action.UNLOAD,
    Action.BUY,
    Action.SELL,
    Action.INVEST_FACTORY,
    Action.COLLECT,
    Action.EASY_MISSION,
    Action.REPAIR,
    Action.UPGRADE,
    Action.SALVAGE,
    Action.ATTACK_RANDOM,
    Action.ATTACK_STRONGEST,
    Action.ATTACK_WEAKEST,
    Action.BOMBARD,
    Action.SET_HOME,
    Action.BUY_WARSHIP,
    Action.SELL_WARSHIP,
    Action.BUILD_MINER,
    Action.BUILD_CORVETTE,
    Action.BUILD_FRIGATE,
    Action.PILOT_MINER,
    Action.PILOT_CORVETTE,
    Action.PILOT_FRIGATE,
    Action.PLACE_BOUNTY,
    Action.INVEST_DRYDOCK,
    Action.BUILD_DESTROYER,
    Action.PILOT_DESTROYER,
    Action.BUILD_EXTRACTOR,
    Action.PILOT_EXTRACTOR,
    Action.BUY_MINING_SPACESHIP,
    Action.SELL_MINING_SPACESHIP,
]
ACTIONS = [action.value for action in ACTION_ENUMS]
NUM_ATTACK_ROUND = 10
NUM_DEFENSE_ROUND = 8
P_ATTACK_HIT = 0.25
P_DEFENSE_HIT = 0.2
DEFAULT_RARITY = 1
DEFAULT_VOLUME = 10
P_SALVAGE = 0.95
DEFAULT_SPACESHIP_COST = 1
SET_HOME_COST = 1000
MIN_BOUNTY = 1000
NUM_RESPAWN_IDLE_TURN = 10


class Player:
    def __init__(
        self, name, universe, control=Control.HUMAN, goal=None, willingness=1, memory=2
    ):
        self.name = name
        self.universe = universe
        self.universe.add_player(self)
        self.control = control
        self.explored_systems = set()
        self.home_system = universe.get_random_system_with_planet()
        self.home_system.add_player(self)
        self.home_system.empty_space.add_player(self)
        self.wallet = 0
        self.turns_until_idle = 0
        self.spaceship = Explorer()
        self.skills = defaultdict(int)
        self.goal = goal
        self.willingness = willingness
        if self.control == Control.NEURAL_AI:
            self.learning_agent = DQNAgent(
                actions=ACTIONS,
                input_size=71,  # Adjust based on the state representation
                hidden_sizes=[128, 256, 128],  # Adjust as needed
                output_size=len(ACTIONS),
                batch_size=128,
                # ... other hyperparameters for DQN agent ...
            )
            self.state_memory = deque(maxlen=memory)
        else:
            self.learning_agent = None
            self.state_memory = None
        self.last_action_index = 0
        self.action_history = defaultdict(int)
        self.death = 0
        self.kill = 0
        self.destroy = 0
        self.build = 0
        self.mined = 0
        self.total_damage = 0
        self.total_investment = 0
        self.profit_collected = 0
        self.roi = 0
        self.distance_traveled = 0
        self.mission_completed = 0
        self.salvage_completed = 0
        self.mining_completed = 0
        self.net_worth = self.calculate_net_worth()
        self.score = self.calculate_score()
        self.last_killed_by = None

    def move(self, location):
        self.current_location.remove_player(self)
        location.add_player(self)
        logger.debug(
            f"{self.name} moved to {location.name} within {self.current_system.name}"
        )

    def move_to_random_planet(self):
        available_locations = self.current_system.planets[:]
        if self.current_location in available_locations:
            available_locations.remove(self.current_location)
        if available_locations:
            target_location = random.choice(available_locations)
            self.move(target_location)

    def move_to_random_asteroid_belt(self):
        available_locations = self.current_system.asteroid_belts[:]
        if self.current_location in available_locations:
            available_locations.remove(self.current_location)
        if available_locations:
            target_location = random.choice(available_locations)
            self.move(target_location)

    def move_to_random_moon(self):
        available_locations = self.current_system.moons[:]
        if self.current_location in available_locations:
            available_locations.remove(self.current_location)
        if available_locations:
            target_location = random.choice(available_locations)
            self.move(target_location)

    def move_to_random_stargate(self):
        available_locations = self.current_system.stargates[:]
        if self.current_location in available_locations:
            available_locations.remove(self.current_location)
        if available_locations:
            target_location = random.choice(available_locations)
            self.move(target_location)

    def move_to_random_debris(self):
        available_locations = self.current_system.debrises[:]
        if self.current_location in available_locations:
            available_locations.remove(self.current_location)
        if available_locations:
            target_location = random.choice(available_locations)
            self.move(target_location)

    def activate_stargate(self):
        if isinstance(self.current_location, Stargate):
            self.current_location.activate(self)
        else:
            logger.warning("Cannot activate stargate from this location.")

    def explore(self):
        logger.debug(
            f"{self.name} is exploring {self.current_location.name} in {self.current_system.name}."
        )
        if self.can_explore():
            resources = self.current_location.get_resources()
            logger.debug(f"Resources found on {self.current_location.name}:")
            for resource, amount in resources.items():
                if amount > 0:
                    logger.debug(f"  {resource}: {amount}")
        else:
            logger.warning(f"No resources found on {self.current_location.name}:")

    def mine(self):
        if self.can_mine():
            self.current_location.mine(self)
            logger.debug(f"{self.name} mined from {self.current_location.name}")
        else:
            logger.warning("Cannot mine from this location.")

    def unload(self):
        if self.current_location.has_storage():
            for item, qty in self.spaceship.cargo_hold.items():
                self.current_location.storage.add_item(self, item, qty)
            self.spaceship.cargo_hold = defaultdict(int)
            logger.info(
                f"{self.name} unloaded cargo at {self.current_system.name} - {self.current_location.name}"
            )
        else:
            logger.warning("Cannot unload cargo from this location.")

    def buy(self, resource, quantity):
        if (
            self.current_location.has_marketplace()
            and self.current_location.has_storage()
        ):
            if self.current_location.marketplace.buy(self, resource, quantity):
                logger.debug(f"{self.name} bought {quantity} of {resource}")
                return True
            else:
                logger.warning(f"{self.name} failed to buy {quantity} of {resource}")
                return False
        else:
            logger.warning("Cannot buy from this location.")
            return False

    def buy_random_resource(self):
        if (
            self.current_location.has_marketplace()
            and self.current_location.has_storage()
        ):
            available_resources = [
                res
                for res, data in self.current_location.marketplace.inventory.items()
                if data["quantity"] > 0
            ]
            if available_resources:
                resource = random.choice(available_resources)
                max_qty = max(
                    min(
                        self.current_location.marketplace.inventory[resource][
                            "quantity"
                        ],
                        int(
                            self.wallet
                            / self.current_location.marketplace.inventory[resource][
                                "price"
                            ]
                        ),
                    ),
                    0,
                )
                qty = random.randint(0, max_qty)
                self.buy(resource, qty)

    def sell(self, resource, quantity):
        if (
            self.current_location.has_marketplace()
            and self.current_location.has_storage()
        ):
            if self.current_location.marketplace.sell(self, resource, quantity):
                logger.debug(f"{self.name} sold {quantity} of {resource}")
                return True
            else:
                logger.warning(f"{self.name} failed to sell {quantity} of {resource}")
                return False
        else:
            logger.warning("Cannot sell from this location.")
            return False

    def sell_random_resource(self):
        if (
            self.current_location.has_marketplace()
            and self.current_location.has_storage()
        ):
            available_resources = [
                (res, qty)
                for res, qty in self.current_location.storage.get_inventory(
                    self
                ).items()
                if qty > 0
            ]
            if available_resources:
                resource, qty = random.choice(available_resources)
                qty_sell = random.randint(1, qty)
                self.sell(resource, qty_sell)

    def manufacture(self, blueprint_name):
        if self.current_location.factory.manufacture(self, blueprint_name):
            logger.info(f"{self.name} built {blueprint_name}.")
        else:
            logger.warning(f"{blueprint_name} manufacturing job failed!")

    def build_miner(self):
        blueprint_name = "miner"
        if self.can_build_miner():
            self.manufacture(blueprint_name)
            logger.debug(f"Building {blueprint_name}")
        else:
            logger.warning(f"No enough materials to build {blueprint_name} spaceship!")

    def build_corvette(self):
        blueprint_name = "corvette"
        if self.can_build_corvette():
            self.manufacture(blueprint_name)
            logger.debug(f"Building {blueprint_name}")
        else:
            logger.warning(f"No enough materials to build {blueprint_name} spaceship!")

    def build_frigate(self):
        blueprint_name = "frigate"
        if self.can_build_frigate():
            self.manufacture(blueprint_name)
            logger.debug(f"Building {blueprint_name}")
        else:
            logger.warning(f"No enough materials to build {blueprint_name} spaceship!")

    def build_destroyer(self):
        blueprint_name = "destroyer"
        if self.can_build_destroyer():
            self.manufacture(blueprint_name)
            logger.debug(f"Building {blueprint_name}")
        else:
            logger.warning(f"No enough materials to build {blueprint_name} spaceship!")

    def build_extractor(self):
        blueprint_name = "extractor"
        if self.can_build_extractor():
            self.manufacture(blueprint_name)
            logger.debug(f"Building {blueprint_name}")
        else:
            logger.warning(f"No enough materials to build {blueprint_name} spaceship!")

    def invest_factory(self, amount):
        if self.current_location.has_factory():
            if self.wallet >= amount:
                self.current_location.factory.invest(self, amount)
                logger.debug(
                    f"{self.name} invested {amount} at the factory at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning(f"{self.name} failed to invest {amount}")
        else:
            logger.warning("Cannot invest from this location.")

    def invest_factory_random_amount(self):
        spend_factor = 0.01
        investment = random.randint(0, max(int(self.wallet * spend_factor), 0))
        self.invest_factory(investment)

    def invest_drydock(self, amount):
        if self.current_location.has_drydock():
            if self.wallet >= amount:
                self.current_location.drydock.invest(self, amount)
                logger.debug(
                    f"{self.name} invested {amount} at the drydock at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning(f"{self.name} failed to invest {amount}")
        else:
            logger.warning("Cannot invest from this location.")

    def invest_drydock_random_amount(self):
        spend_factor = 0.01
        investment = random.randint(0, max(int(self.wallet * spend_factor), 0))
        self.invest_drydock(investment)

    def collect(self):
        if self.can_collect():
            payout = 0
            if hasattr(self.current_location, "factory"):
                payout += self.current_location.factory.profit(self)
            if hasattr(self.current_location, "drydock"):
                payout += self.current_location.drydock.profit(self)
            logger.debug(
                f"{self.name} collected {payout} at {self.current_system.name} - {self.current_location.name}"
            )
        else:
            logger.warning("Cannot collect from this location.")

    def easy_mission(self):
        if self.current_location.has_mission_center():
            mission_ = self.current_location.mission_center.apply_mission_easiet()
            if mission_:
                result = self.current_location.mission_center.do_mission(self, mission_)
                if result > 0:
                    logger.debug(
                        f"{self.name} completed mission {mission_.description} at {self.current_system.name} - {self.current_location.name}"
                    )
                else:
                    logger.debug(f"{self.name} failed mission {mission_.description}")
        else:
            logger.warning("Cannot do mission from this location.")

    def difficult_mission(self):
        if self.current_location.has_mission_center():
            mission_ = self.current_location.mission_center.apply_mission_hardest()
            if mission_:
                result = self.current_location.mission_center.do_mission(self, mission_)
                if result > 0:
                    logger.debug(
                        f"{self.name} completed mission {mission_.description} at {self.current_system.name} - {self.current_location.name}"
                    )
                else:
                    logger.debug(f"{self.name} failed mission {mission_.description}")
        else:
            logger.warning("Cannot do mission from this location.")

    def repair(self):
        if self.can_repair():
            self.current_location.drydock.repair_spaceship(self)
            logger.debug(
                f"{self.name} repaired spaceship at {self.current_system.name} - {self.current_location.name}"
            )
        else:
            logger.warning("Cannot repair spaceship from this location.")

    def upgrade(self):
        if self.can_upgrade():
            self.current_location.drydock.upgrade_spaceship(self)
            logger.debug(
                f"{self.name} upgraded spaceship at {self.current_system.name} - {self.current_location.name}"
            )
        else:
            logger.warning("Cannot upgrade spaceship from this location.")

    def salvage(self):
        if isinstance(self.current_location, Debris):
            self.current_location.salvage(self)
            logger.debug(
                f"{self.name} salvaged debris at {self.current_system.name} - {self.current_location.name}"
            )
        else:
            logger.warning("Cannot upgrade spaceship from this location.")

    def attack(self, target_player):
        damage = (
            np.random.binomial(
                NUM_ATTACK_ROUND,
                max(P_ATTACK_HIT * (1 + self.spaceship.level * 0.01), 1),
            )
            * self.spaceship.weapon
        )
        self.total_damage += damage
        self.universe.total_damage_dealt += damage
        target_player.spaceship.take_damage(damage)
        logger.debug(
            f"{self.name} attacked {target_player.name} and caused {damage} damage!"
        )
        if target_player.spaceship.destroyed:
            if not self.spaceship.is_cargo_full():
                for item, count in target_player.spaceship.cargo_hold.items():
                    if random.random() < P_SALVAGE:
                        self.spaceship.cargo_hold[item] += count
                target_player.spaceship.cargo_hold = defaultdict(int)
            else:
                self.current_system.make_debris(target_player.spaceship.cargo_hold)

            self.kill += 1
            self.universe.total_kill += 1
            leaderboard.log_achievement(self.name, "kill", 1)
            target_player.die()
            target_player.last_killed_by = self.name
            leaderboard.log_achievement(target_player.name, "death", 1)

            logger.warning(
                f"{self.name} killed {target_player.name}! at {self.current_system.name} - {self.current_location.name}"
            )

            bounty = leaderboard.get_achievement_score(target_player.name, "bounty")
            if bounty > 0:
                self.wallet += bounty
                leaderboard.log_achievement(
                    target_player.name, "bounty", 0, overwrite=True
                )
                logger.info(f"{self.name} earned {bounty} bounty!")
        else:
            defensive_damage = (
                np.random.binomial(
                    NUM_DEFENSE_ROUND,
                    max(P_DEFENSE_HIT * (1 + target_player.spaceship.level * 0.01), 1),
                )
                * target_player.spaceship.weapon
            )
            target_player.total_damage += defensive_damage
            target_player.universe.total_damage_dealt += damage
            self.spaceship.take_damage(defensive_damage)
            logger.debug(
                f"{target_player.name} returned fire at {self.name} and caused {damage} damage!"
            )
            if self.spaceship.destroyed:
                self.current_system.make_debris(self.spaceship.cargo_hold)

                target_player.kill += 1
                target_player.universe.total_kill += 1
                leaderboard.log_achievement(target_player.name, "kill", 1)
                self.die()
                self.last_killed_by = target_player.name
                leaderboard.log_achievement(self.name, "death", 1)
                logger.warning(
                    f"{target_player.name} killed {self.name}! at {self.current_system.name} - {self.current_location.name}"
                )

                bounty = leaderboard.get_achievement_score(self.name, "bounty")
                if bounty > 0:
                    target_player.wallet += bounty
                    leaderboard.log_achievement(self.name, "bounty", 0, overwrite=True)
                    logger.info(f"{target_player.name} earned {bounty} bounty!")

    def attack_random_player(self):
        if self.spaceship.weapon > 0:
            available_target_players = [
                player for player in self.current_location.players if player != self
            ]
            if len(available_target_players) > 0:
                target_player = random.choice(available_target_players)
                self.attack(target_player)
            else:
                logger.warning("No other player to attack from this location.")
        else:
            logger.warning("Spaceship has no weapon!")

    def attack_strongest_player(self):
        if self.spaceship.weapon > 0:
            available_target_players = [
                player for player in self.current_location.players if player != self
            ]
            if len(available_target_players) > 0:
                available_target_players.sort(key=lambda p: p.kill, reverse=True)
                target_player = available_target_players[0]
                self.attack(target_player)
            else:
                logger.warning("No other player to attack from this location.")
        else:
            logger.warning("Spaceship has no weapon!")

    def attack_weakest_player(self):
        if self.spaceship.weapon > 0:
            available_target_players = [
                player for player in self.current_location.players if player != self
            ]
            if len(available_target_players) > 0:
                available_target_players.sort(key=lambda p: p.kill, reverse=False)
                target_player = available_target_players[0]
                self.attack(target_player)
            else:
                logger.warning("No other player to attack from this location.")
        else:
            logger.warning("Spaceship has no weapon!")

    def bombard(self, target_building):
        if self.can_bombard():
            target_building.bombard(self)
        else:
            logger.warning("Cannot bombard from this location.")

    def bombard_random_building(self):
        if self.spaceship.weapon > 0:
            available_target_buildings = [
                building for building in self.current_location.buildings
            ]
            if len(available_target_buildings) > 0:
                target_building = random.choice(available_target_buildings)
                self.bombard(target_building)
            else:
                logger.warning("No building to bombard from this location.")
        else:
            logger.warning("Spaceship has no weapon!")

    def set_home(self):
        if (
            isinstance(self.current_location, Planet)
            and self.wallet >= SET_HOME_COST
            and self.current_system != self.home_system
        ):
            self.home_system = self.current_system
            self.spend(SET_HOME_COST)
            logger.info(f"{self.name} set home to {self.current_system.name}.")
        else:
            logger.warning("Cannot set home from this location.")

    def buy_warship(self):
        if self.can_buy_warship():
            for spaceship in ["destroyer", "frigate", "corvette"]:
                if self.buy(spaceship, 1):
                    logger.info(
                        f"{self.name} bought a {spaceship} at {self.current_system.name} - {self.current_location.name}"
                    )
                    break
        else:
            logger.warning("Cannot buy warship from this location.")

    def sell_warship(self):
        if self.can_sell_warship():
            for spaceship in ["destroyer", "frigate", "corvette"]:
                if self.sell(spaceship, 1):
                    logger.info(
                        f"{self.name} sold a {spaceship} at {self.current_system.name} - {self.current_location.name}"
                    )
                    break
        else:
            logger.warning("Cannot sell warship from this location.")

    def buy_mining_spaceship(self):
        if self.can_buy_mining_spaceship():
            for spaceship in ["extractor", "miner"]:
                if self.buy(spaceship, 1):
                    logger.info(
                        f"{self.name} bought a {spaceship} at {self.current_system.name} - {self.current_location.name}"
                    )
                    break
        else:
            logger.warning("Cannot buy mining ship from this location.")

    def sell_mining_spaceship(self):
        if self.can_sell_mining_spaceship():
            for spaceship in ["extractor", "miner"]:
                if self.sell(spaceship, 1):
                    logger.info(
                        f"{self.name} sold a {spaceship} at {self.current_system.name} - {self.current_location.name}"
                    )
                    break
        else:
            logger.warning("Cannot sell mining ship from this location.")

    def pilot_miner(self):
        if self.can_pilot_miner():
            new_spaceship = self.current_location.hangar.remove_spaceship(self, "miner")
            if new_spaceship is None:
                self.current_location.storage.remove_item(self, "miner", 1)
                new_spaceship = Miner()

            if new_spaceship is not None:
                for item, count in self.spaceship.cargo_hold.items():
                    new_spaceship.cargo_hold[item] += count
                    self.spaceship.cargo_hold[item] = 0

                if not isinstance(self.spaceship, Explorer):
                    self.current_location.hangar.add_spaceship(self, self.spaceship)
                self.spaceship = new_spaceship
                self.spaceship.recharge_shield()
                logger.info(
                    f"{self.name} piloted a miner spaceship at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning("No miner spaceship")
        else:
            logger.warning("Cannot pilot miner spaceship from this location.")

    def pilot_corvette(self):
        if self.can_pilot_corvette():
            new_spaceship = self.current_location.hangar.remove_spaceship(
                self, "corvette"
            )
            if new_spaceship is None:
                self.current_location.storage.remove_item(self, "corvette", 1)
                new_spaceship = Corvette()

            if new_spaceship is not None:
                for item, count in self.spaceship.cargo_hold.items():
                    new_spaceship.cargo_hold[item] += count
                    self.spaceship.cargo_hold[item] = 0

                if not isinstance(self.spaceship, Explorer):
                    self.current_location.hangar.add_spaceship(self, self.spaceship)
                self.spaceship = new_spaceship
                self.spaceship.recharge_shield()
                logger.info(
                    f"{self.name} piloted a corvette spaceship at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning("No corvette spaceship")
        else:
            logger.warning("Cannot pilot corvette spaceship from this location.")

    def pilot_frigate(self):
        if self.can_pilot_frigate():
            new_spaceship = self.current_location.hangar.remove_spaceship(
                self, "frigate"
            )
            if new_spaceship is None:
                self.current_location.storage.remove_item(self, "frigate", 1)
                new_spaceship = Frigate()

            if new_spaceship is not None:
                for item, count in self.spaceship.cargo_hold.items():
                    new_spaceship.cargo_hold[item] += count
                    self.spaceship.cargo_hold[item] = 0

                if not isinstance(self.spaceship, Explorer):
                    self.current_location.hangar.add_spaceship(self, self.spaceship)
                self.spaceship = new_spaceship
                self.spaceship.recharge_shield()
                logger.info(
                    f"{self.name} piloted a frigate spaceship at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning("No frigate spaceship")
        else:
            logger.warning("Cannot pilot frigate spaceship from this location.")

    def pilot_destroyer(self):
        if self.can_pilot_destroyer():
            new_spaceship = self.current_location.hangar.remove_spaceship(
                self, "destroyer"
            )
            if new_spaceship is None:
                self.current_location.storage.remove_item(self, "destroyer", 1)
                new_spaceship = Destroyer()

            if new_spaceship is not None:
                for item, count in self.spaceship.cargo_hold.items():
                    new_spaceship.cargo_hold[item] += count
                    self.spaceship.cargo_hold[item] = 0

                if not isinstance(self.spaceship, Explorer):
                    self.current_location.hangar.add_spaceship(self, self.spaceship)
                self.spaceship = new_spaceship
                self.spaceship.recharge_shield()
                logger.info(
                    f"{self.name} piloted a destroyer spaceship at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning("No destroyer spaceship")
        else:
            logger.warning("Cannot pilot destroyer spaceship from this location.")

    def pilot_extractor(self):
        if self.can_pilot_extractor():
            new_spaceship = self.current_location.hangar.remove_spaceship(
                self, "extractor"
            )
            if new_spaceship is None:
                self.current_location.storage.remove_item(self, "extractor", 1)
                new_spaceship = Extractor()

            if new_spaceship is not None:
                for item, count in self.spaceship.cargo_hold.items():
                    new_spaceship.cargo_hold[item] += count
                    self.spaceship.cargo_hold[item] = 0

                if not isinstance(self.spaceship, Explorer):
                    self.current_location.hangar.add_spaceship(self, self.spaceship)
                self.spaceship = new_spaceship
                self.spaceship.recharge_shield()
                logger.info(
                    f"{self.name} piloted a extractor spaceship at {self.current_system.name} - {self.current_location.name}"
                )
            else:
                logger.warning("No extractor spaceship")
        else:
            logger.warning("Cannot pilot extractor spaceship from this location.")

    def place_bounty(self):
        if self.can_place_bounty():
            spend_factor = 0.01
            upper_bound = max(MIN_BOUNTY, int(self.wallet * spend_factor))
            bounty = random.randint(MIN_BOUNTY, upper_bound)
            self.spend(bounty)
            target_player_name = self.last_killed_by
            leaderboard.log_achievement(target_player_name, "bounty", bounty)
            self.last_killed_by = None
            logger.info(
                f"{self.name} placed a bounty of {bounty} on {target_player_name}!"
            )
        else:
            logger.warning("Cannot place bounty.")

    def spend(self, money: float):
        self.wallet -= money
        self.universe.total_money_spent += money

    def die(self):
        logger.warning(
            f"{self.name} died at {self.current_system.name} - {self.current_location.name}"
        )
        self.death += 1
        self.spend(DEFAULT_SPACESHIP_COST)
        self.current_system.remove_player(self)
        self.current_location.remove_player(self)
        self.home_system.add_player(self)
        self.home_system.empty_space.add_player(self)
        self.spaceship = Explorer()
        self.turns_until_idle += NUM_RESPAWN_IDLE_TURN
        logger.warning(f"{self.name} respawned at {self.current_system.name}")

    def act(self):
        # Handle different control types
        if self.control in [
            Control.NEURAL_AI,
            Control.SYMBOLIC_AI,
            Control.RANDOM_WALK_AI,
        ]:
            action_index = self.choose_action_index()
            if self.control == Control.NEURAL_AI:
                state_before_action = self.get_reduced_state()
            self.perform_action(action_index)
            self.health_check()
            self.update_stats()
            if self.control == Control.NEURAL_AI:
                self.update_memory_and_learn(state_before_action, action_index)
        else:
            pass  # Or handle other cases

    def choose_action_index(self):
        # Decide action index based on control type
        if self.control == Control.NEURAL_AI:
            return self.choose_action_index_neural_ai()
        elif self.control == Control.SYMBOLIC_AI:
            return self.choose_action_index_symbolic_ai()
        else:
            return self.choose_action_index_random_walk_ai()

    def choose_action_index_neural_ai(self):
        state = self.get_reduced_state()
        if self.turns_until_idle <= 0:
            return self.learning_agent.choose_action(state)
        else:
            return self.last_action_index

    def choose_action_index_symbolic_ai(self):
        if self.turns_until_idle <= 0:
            # Choose action using rules
            if self.goal == Goal.MAX_DESTROY:
                action_index_probs = []
                if self.can_repair():
                    action_index_probs.append((15, 0.1))
                if self.can_upgrade():
                    action_index_probs.append((16, 0.03))
                if self.can_move_planet():
                    action_index_probs.append((1, 0.05))
                if self.can_travel():
                    action_index_probs.append((6, 0.001))
                if self.can_mine():
                    action_index_probs.append((8, 0.2))
                if self.can_unload():
                    action_index_probs.append((9, 0.01))
                if self.can_sell():
                    action_index_probs.append((11, 0.01))
                if self.can_buy_warship():
                    action_index_probs.append((23, 0.01))
                if self.can_invest_factory():
                    action_index_probs.append((12, 0.001))
                if self.can_invest_drydock():
                    action_index_probs.append((32, 0.001))
                if self.can_collect():
                    action_index_probs.append((13, 0.001))

                if self.can_pilot_corvette():
                    if (isinstance(self.spaceship, (Explorer, Miner))) or (
                        isinstance(self.spaceship, (Frigate, Destroyer))
                        and self.spaceship.is_damaged()
                        and self.wallet <= self.spaceship.calc_repair_cost()
                    ):
                        action_index_probs.append((29, 1))
                if self.can_pilot_frigate():
                    action_index_probs.append((30, 1))
                if self.can_pilot_destroyer():
                    action_index_probs.append((34, 1))

                ready_to_bombard = (
                    self.can_bombard()
                    and isinstance(self.spaceship, (Destroyer, Frigate, Corvette))
                    and math.isclose(self.spaceship.hull, self.spaceship.max_hull)
                )

                if ready_to_bombard:
                    action_index_probs.append((21, 1))
                action_indexes, probs = zip(*action_index_probs)
                return random.choices(action_indexes, weights=probs, k=1)[0]
            if self.goal == Goal.MAX_MISSION:
                action_index_probs = []
                if self.can_repair():
                    action_index_probs.append((15, 0.1))
                if self.can_upgrade():
                    action_index_probs.append((16, 0.03))
                if self.can_move_planet():
                    action_index_probs.append((1, 0.05))
                if self.can_move_moon():
                    action_index_probs.append((3, 0.1))
                if self.can_move_stargate():
                    action_index_probs.append((4, 0.01))
                if self.can_travel():
                    if self.can_move_moon():
                        action_index_probs.append((6, 0.01))
                    else:
                        action_index_probs.append((6, 1))
                if self.can_unload():
                    action_index_probs.append((9, 0.01))
                if self.can_sell():
                    action_index_probs.append((11, 0.01))
                if self.can_buy_warship():
                    action_index_probs.append((23, 1))
                if self.can_set_home():
                    action_index_probs.append((22, 0.001))
                if self.can_invest_factory():
                    action_index_probs.append((12, 0.001))
                if self.can_invest_drydock():
                    action_index_probs.append((32, 0.001))
                if self.can_collect():
                    action_index_probs.append((13, 0.01))
                if self.can_set_home():
                    action_index_probs.append((22, 0.0005))

                if self.can_pilot_corvette():
                    if isinstance(self.spaceship, Explorer):
                        action_index_probs.append((29, 1))
                    else:
                        if (
                            self.spaceship.is_damaged()
                            and self.wallet <= self.spaceship.calc_repair_cost()
                        ):
                            action_index_probs.append((29, 0.1))

                if self.can_pilot_frigate() and self.wallet >= 500000:
                    action_index_probs.append((30, 1))
                if self.can_pilot_destroyer() and self.wallet >= 1250000:
                    action_index_probs.append((34, 1))

                ready_to_mission = (
                    self.can_mission()
                    and isinstance(
                        self.spaceship, (Destroyer, Frigate, Corvette, Explorer)
                    )
                    and math.isclose(self.spaceship.armor, self.spaceship.max_armor)
                    and math.isclose(self.spaceship.hull, self.spaceship.max_hull)
                )

                if ready_to_mission:
                    action_index_probs.append((14, 1))
                action_indexes, probs = zip(*action_index_probs)
                return random.choices(action_indexes, weights=probs, k=1)[0]
            elif self.goal == Goal.MAX_KILL:
                action_index_probs = []
                if self.can_repair():
                    action_index_probs.append((15, 0.1))
                if self.can_upgrade():
                    action_index_probs.append((16, 0.03))
                if self.can_move_planet():
                    action_index_probs.append((1, 0.05))
                if self.can_move_asteroid_belt():
                    action_index_probs.append((2, 0.01))
                if self.can_move_moon():
                    action_index_probs.append((3, 0.01))
                if self.can_move_stargate():
                    action_index_probs.append((4, 0.01))
                if self.can_move_debris():
                    action_index_probs.append((5, 0.01))
                if self.can_travel():
                    action_index_probs.append((6, 0.01))
                if self.can_mine():
                    action_index_probs.append((8, 0.2))
                if self.can_salvage():
                    action_index_probs.append((17, 0.10))
                if self.can_unload():
                    action_index_probs.append((9, 0.01))
                if self.can_sell():
                    action_index_probs.append((11, 0.01))
                if self.can_buy_warship():
                    action_index_probs.append((23, 0.1))
                if self.can_buy_mining_spaceship():
                    action_index_probs.append((37, 0.0001))
                if self.can_set_home():
                    action_index_probs.append((22, 0.0005))
                if self.can_invest_factory():
                    action_index_probs.append((12, 0.001))
                if self.can_invest_drydock():
                    action_index_probs.append((32, 0.001))
                if self.can_collect():
                    action_index_probs.append((13, 0.001))

                if self.can_pilot_miner() and (
                    self.wallet < 10000
                    or (
                        not self.can_pilot_corvette()
                        and not isinstance(self.spaceship, Corvette)
                    )
                ):
                    action_index_probs.append((28, 0.01))

                if self.can_pilot_extractor() and (
                    self.wallet < 10000
                    or (
                        not self.can_pilot_corvette()
                        and not isinstance(self.spaceship, Corvette)
                    )
                ):
                    action_index_probs.append((36, 0.02))

                if self.can_pilot_corvette():
                    if (isinstance(self.spaceship, (Explorer, Miner))) or (
                        isinstance(self.spaceship, (Frigate, Destroyer))
                        and self.spaceship.is_damaged()
                        and self.wallet <= self.spaceship.calc_repair_cost()
                    ):
                        action_index_probs.append((29, 1))
                if self.can_pilot_frigate():
                    action_index_probs.append((30, 1))
                if self.can_pilot_destroyer():
                    action_index_probs.append((34, 1))

                ready_to_mission = (
                    self.can_mission()
                    and isinstance(self.spaceship, (Destroyer, Frigate, Corvette))
                    and math.isclose(self.spaceship.hull, self.spaceship.max_hull)
                    and math.isclose(self.spaceship.armor, self.spaceship.max_armor)
                )
                if ready_to_mission:
                    action_index_probs.append((14, 1))

                ready_to_kill = (
                    self.can_attack()
                    and isinstance(self.spaceship, (Destroyer, Frigate, Corvette))
                    and math.isclose(self.spaceship.hull, self.spaceship.max_hull)
                    and math.isclose(self.spaceship.armor, self.spaceship.max_armor)
                )
                if ready_to_kill:
                    action_index_probs.append((20, 1))

                action_indexes, probs = zip(*action_index_probs)
                return random.choices(action_indexes, weights=probs, k=1)[0]
            elif self.goal == Goal.MAX_BOUNTY:
                action_index_probs = []
                if self.can_repair():
                    action_index_probs.append((15, 0.1))
                if self.can_upgrade():
                    action_index_probs.append((16, 0.03))
                if self.can_move_planet():
                    action_index_probs.append((1, 0.05))
                if self.can_move_asteroid_belt():
                    action_index_probs.append((2, 0.01))
                if self.can_move_moon():
                    action_index_probs.append((3, 0.01))
                if self.can_move_stargate():
                    action_index_probs.append((4, 0.01))
                if self.can_move_debris():
                    action_index_probs.append((5, 0.01))
                if self.can_travel():
                    action_index_probs.append((6, 0.01))
                if self.can_mine():
                    action_index_probs.append((8, 0.2))
                if self.can_salvage():
                    action_index_probs.append((17, 0.10))
                if self.can_unload():
                    action_index_probs.append((9, 0.01))
                if self.can_sell():
                    action_index_probs.append((11, 0.01))
                if self.can_buy_warship():
                    action_index_probs.append((23, 0.1))
                if self.can_buy_mining_spaceship():
                    action_index_probs.append((37, 0.0001))
                if self.can_invest_factory():
                    action_index_probs.append((12, 0.001))
                if self.can_invest_drydock():
                    action_index_probs.append((32, 0.001))
                if self.can_collect():
                    action_index_probs.append((13, 0.001))

                if self.can_pilot_miner() and (
                    self.wallet < 10000
                    or (
                        not self.can_pilot_corvette()
                        and not isinstance(self.spaceship, Corvette)
                    )
                ):
                    action_index_probs.append((28, 0.01))

                if self.can_pilot_extractor() and (
                    self.wallet < 10000
                    or (
                        not self.can_pilot_corvette()
                        and not isinstance(self.spaceship, Corvette)
                    )
                ):
                    action_index_probs.append((36, 0.02))

                if self.can_pilot_corvette():
                    if (isinstance(self.spaceship, (Explorer, Miner))) or (
                        isinstance(self.spaceship, (Frigate, Destroyer))
                        and self.spaceship.is_damaged()
                        and self.wallet <= self.spaceship.calc_repair_cost()
                    ):
                        action_index_probs.append((29, 1))

                if self.can_pilot_frigate():
                    action_index_probs.append((30, 1))
                if self.can_pilot_destroyer():
                    action_index_probs.append((34, 1))

                ready_to_mission = (
                    self.can_mission()
                    and isinstance(self.spaceship, (Destroyer, Frigate, Corvette))
                    and math.isclose(self.spaceship.armor, self.spaceship.max_armor)
                    and math.isclose(self.spaceship.hull, self.spaceship.max_hull)
                )
                if ready_to_mission:
                    action_index_probs.append((14, 0.01))

                wanteds = [
                    x[0] for x in leaderboard.get_top_leaders("bounty", 10) if x[1] > 0
                ]
                kill_threshold = self.universe.total_kill * 0.05
                killers = [
                    x[0]
                    for x in leaderboard.get_top_leaders("kill", 10)
                    if x[1] > kill_threshold
                ]
                target_player_names = [
                    player.name
                    for player in self.current_location.players
                    if player != self
                ]
                killer_match = (
                    len(
                        set(wanteds)
                        .intersection(set(killers))
                        .intersection(set(target_player_names))
                    )
                    > 0
                )
                if killer_match:
                    logger.debug("Killer match!")
                should_police = (
                    self.can_attack()
                    and isinstance(self.spaceship, (Destroyer, Frigate, Corvette))
                    and math.isclose(self.spaceship.hull, self.spaceship.max_hull)
                    and killer_match
                )
                if should_police:
                    action_index_probs.append((19, 1))
                action_indexes, probs = zip(*action_index_probs)
                return random.choices(action_indexes, weights=probs, k=1)[0]
            elif self.goal == Goal.MAX_BUILD:
                action_index_probs = []
                if self.can_move_planet():
                    action_index_probs.append((1, 0.02))
                if self.can_move_asteroid_belt():
                    action_index_probs.append((2, 0.05))
                if self.can_move_moon():
                    action_index_probs.append((3, 0.01))
                if self.can_move_stargate():
                    action_index_probs.append((4, 0.01))
                if self.can_move_debris():
                    action_index_probs.append((5, 0.01))
                if self.can_travel():
                    action_index_probs.append((6, 0.01))
                if self.can_mine():
                    action_index_probs.append((8, 0.50))
                if self.can_salvage():
                    action_index_probs.append((17, 0.10))
                if self.can_buy():
                    action_index_probs.append((10, 0.01))
                if self.can_sell():
                    action_index_probs.append((11, 0.01))
                if self.can_buy_mining_spaceship():
                    action_index_probs.append((37, 0.02))
                if self.can_sell_warship():
                    action_index_probs.append((24, 0.03))
                if self.can_sell_mining_spaceship():
                    action_index_probs.append((38, 0.001))
                if self.can_set_home():
                    action_index_probs.append((22, 0.001))
                if self.can_place_bounty():
                    action_index_probs.append((31, 0.01))
                if self.can_invest_factory():
                    action_index_probs.append((12, 0.001))
                if self.can_invest_drydock():
                    action_index_probs.append((32, 0.001))
                if self.can_collect():
                    action_index_probs.append((13, 0.001))
                if self.can_repair():
                    action_index_probs.append((15, 0.1))
                if self.can_upgrade():
                    action_index_probs.append((16, 0.03))

                if self.can_unload() and self.spaceship.is_cargo_full():
                    action_index_probs.append((9, 1))

                if self.can_build_destroyer():
                    action_index_probs.append((33, 1))
                if self.can_build_frigate():
                    action_index_probs.append((27, 0.1))
                if self.can_build_corvette():
                    action_index_probs.append((26, 0.01))
                if self.can_build_extractor():
                    action_index_probs.append((35, 0.1))
                if self.can_build_miner():
                    action_index_probs.append((25, 0.01))

                if self.can_pilot_miner() and not isinstance(self.spaceship, Extractor):
                    action_index_probs.append((28, 1))
                if self.can_pilot_extractor:
                    action_index_probs.append((36, 1))

                action_indexes, probs = zip(*action_index_probs)
                return random.choices(action_indexes, weights=probs, k=1)[0]
            else:
                return {
                    0: 1,
                    1: 12,
                    2: 13,
                    3: 9,
                    4: 11,
                    5: 2,  # Map turns to action indexes
                }.get(
                    self.universe.current_turn % 10, 8
                )  # Default to mining

        return self.last_action_index

    def choose_action_index_random_walk_ai(self):
        if self.turns_until_idle <= 0:
            return random.randint(0, len(ACTIONS) - 1)
        else:
            return self.last_action_index

    def perform_action(self, action_index):
        action = ACTIONS[action_index]

        if action == Action.IDLE.value:
            pass
        elif action == Action.MOVE_PLANET.value:
            self.move_to_random_planet()
        elif action == Action.MOVE_ASTEROID_BELT.value:
            self.move_to_random_asteroid_belt()
        elif action == Action.MOVE_MOON.value:
            self.move_to_random_moon()
        elif action == Action.MOVE_STARGATE.value:
            self.move_to_random_stargate()
        elif action == Action.MOVE_DEBRIS.value:
            self.move_to_random_debris()
        elif action == Action.TRAVEL.value:
            self.activate_stargate()
        elif action == Action.EXPLORE.value:
            self.explore()
        elif action == Action.MINE.value:
            self.mine()
        elif action == Action.UNLOAD.value:
            self.unload()
        elif action == Action.BUY.value:
            self.buy_random_resource()
        elif action == Action.SELL.value:
            self.sell_random_resource()
        elif action == Action.INVEST_FACTORY.value:
            self.invest_factory_random_amount()
        elif action == Action.COLLECT.value:
            self.collect()
        elif action == Action.EASY_MISSION.value:
            self.easy_mission()
        elif action == Action.REPAIR.value:
            self.repair()
        elif action == Action.UPGRADE.value:
            self.upgrade()
        elif action == Action.SALVAGE.value:
            self.salvage()
        elif action == Action.ATTACK_RANDOM.value:
            self.attack_random_player()
        elif action == Action.ATTACK_STRONGEST.value:
            self.attack_strongest_player()
        elif action == Action.ATTACK_WEAKEST.value:
            self.attack_weakest_player()
        elif action == Action.BOMBARD.value:
            self.bombard_random_building()
        elif action == Action.SET_HOME.value:
            self.set_home()
        elif action == Action.BUY_WARSHIP.value:
            self.buy_warship()
        elif action == Action.SELL_WARSHIP.value:
            self.sell_warship()
        elif action == Action.BUILD_MINER.value:
            self.build_miner()
        elif action == Action.BUILD_CORVETTE.value:
            self.build_corvette()
        elif action == Action.BUILD_FRIGATE.value:
            self.build_frigate()
        elif action == Action.PILOT_MINER.value:
            self.pilot_miner()
        elif action == Action.PILOT_CORVETTE.value:
            self.pilot_corvette()
        elif action == Action.PILOT_FRIGATE.value:
            self.pilot_frigate()
        elif action == Action.PLACE_BOUNTY.value:
            self.place_bounty()
        elif action == Action.INVEST_DRYDOCK.value:
            self.invest_drydock_random_amount()
        elif action == Action.BUILD_DESTROYER.value:
            self.build_destroyer()
        elif action == Action.PILOT_DESTROYER.value:
            self.pilot_destroyer()
        elif action == Action.BUILD_EXTRACTOR.value:
            self.build_extractor()
        elif action == Action.PILOT_EXTRACTOR.value:
            self.pilot_extractor()
        elif action == Action.BUY_MINING_SPACESHIP.value:
            self.buy_mining_spaceship()
        elif action == Action.SELL_MINING_SPACESHIP.value:
            self.sell_mining_spaceship()
        else:
            logger.error("Not matching any action!!")
        self.action_history[ACTIONS[action_index]] += 1

    def health_check(self):
        self.spaceship.recharge_shield()

    def update_stats(self):
        self.net_worth = self.calculate_net_worth()
        self.roi = self.calculate_roi()
        self.score = self.calculate_score()
        self.turns_until_idle = max(self.turns_until_idle - 1, 0)

    def update_memory_and_learn(self, state_before_action, action_index):
        next_full_state = self.get_full_state()
        self.state_memory.append(next_full_state)

        reward = self.calculate_reward(self.goal, self.willingness, self.state_memory)
        next_state = self.get_reduced_state()

        self.learning_agent.memory.push(
            state_before_action, action_index, reward, next_state, False
        )
        self.learning_agent.learn()

    def calculate_net_worth(self):
        net_worth = self.wallet + self.total_investment * 0.1
        for system in self.universe.star_systems:
            for planet in system.planets:
                for item, quantity in planet.storage.get_inventory(self).items():
                    material = material_manager.get_material(item)
                    if material:
                        base_price_guess = material_manager.guess_base_price(
                            material.rarity
                        )
                        net_worth += (
                            base_price_guess
                            * quantity
                            * self.universe.global_price_index
                        )
        return net_worth

    def calculate_roi(self):
        if self.total_investment > 0:
            return self.profit_collected / self.total_investment
        else:
            return 0

    def calculate_total_investment(self):
        investment = 0
        for system in self.universe.star_systems:
            for planet in system.planets:
                book = planet.factory.investment_book
                investment += book[self.name]
        return investment

    def calculate_score(self):
        monopoly_score = leaderboard.get_achievement_score(self.name, "monopoly")
        mission_score = leaderboard.get_achievement_score(self.name, "mission")
        kill_score = leaderboard.get_achievement_score(self.name, "kill")
        destroy_score = leaderboard.get_achievement_score(self.name, "destroy")
        build_score = leaderboard.get_achievement_score(self.name, "build")
        score = (
            monopoly_score + mission_score + kill_score + destroy_score + build_score
        )
        return score

    def can_move_planet(self):
        return int(len(self.current_system.planets) > 0)

    def can_move_asteroid_belt(self):
        return int(len(self.current_system.asteroid_belts) > 0)

    def can_move_moon(self):
        return int(len(self.current_system.moons) > 0)

    def can_move_stargate(self):
        return int(len(self.current_system.stargates) > 0)

    def can_move_debris(self):
        return int(len(self.current_system.debrises) > 0)

    def can_travel(self):
        return int(isinstance(self.current_location, Stargate))

    def can_explore(self):
        return int(isinstance(self.current_location, (Planet, Moon, AsteroidBelt)))

    def can_unload(self):
        return (
            1
            if self.current_location.has_storage()
            and not self.spaceship.is_cargo_empty()
            else 0
        )

    def can_mine(self):
        if (
            isinstance(self.current_location, Mineable)
            and not self.spaceship.is_cargo_full()
            and self.spaceship.weapon <= 0
        ):
            return int(
                any(
                    amount > 0
                    for amount in self.current_location.get_resources().values()
                )
            )
        return 0

    def can_buy(self):
        return (
            1
            if self.current_location.has_marketplace()
            and self.current_location.has_storage()
            and self.wallet > 0
            and self.current_location.marketplace.inventory
            else 0
        )

    def can_sell(self):
        return int(
            self.current_location.has_marketplace()
            and self.current_location.has_storage()
            and bool(self.current_location.storage.get_inventory(self))
        )

    def can_invest_factory(self):
        return int(self.current_location.has_factory() and self.wallet > 0)

    def can_invest_drydock(self):
        return int(self.current_location.has_drydock() and self.wallet > 0)

    def can_collect(self):
        can_collect_factory = (
            self.current_location.has_factory()
            and self.current_location.factory.equities[self.name] > 0
        )
        can_collect_drydock = (
            self.current_location.has_drydock()
            and self.current_location.drydock.equities[self.name] > 0
        )
        return int(can_collect_factory or can_collect_drydock)

    def can_mission(self):
        return int(
            self.current_location.has_mission_center()
            and len(self.current_location.mission_center.get_available_missions()) > 0
        )

    def can_repair(self):
        return int(
            self.current_location.has_drydock()
            and self.current_location.drydock.can_repair(self)
        )

    def can_upgrade(self):
        return int(
            self.current_location.has_drydock()
            and self.current_location.drydock.can_upgrade(self)
        )

    def can_salvage(self):
        return (
            1
            if isinstance(self.current_location, Debris)
            and not self.current_location.is_empty()
            and not self.spaceship.is_cargo_full()
            else 0
        )

    def can_attack(self):
        return (
            1
            if len(self.current_location.players) > 1 and self.spaceship.weapon > 0
            else 0
        )

    def can_bombard(self):
        return (
            1
            if len(self.current_location.buildings) > 1
            and any(
                building.cooldown <= 0 for building in self.current_location.buildings
            )
            and self.spaceship.weapon > 0
            else 0
        )

    def can_set_home(self):
        return (
            1
            if isinstance(self.current_location, Planet)
            and self.wallet >= SET_HOME_COST
            and self.current_system != self.home_system
            else 0
        )

    def can_buy_warship(self):
        return (
            1
            if self.current_location.has_marketplace()
            and self.current_location.has_storage()
            and any(
                self.wallet
                >= self.current_location.marketplace.inventory[spaceship]["price"]
                and self.current_location.marketplace.inventory[spaceship]["quantity"]
                > 0
                for spaceship in ["destroyer", "frigate", "corvette"]
            )
            else 0
        )

    def can_sell_warship(self):
        return (
            1
            if self.current_location.has_marketplace()
            and self.current_location.has_storage()
            and any(
                self.current_location.storage.get_item(self, spaceship) > 0
                for spaceship in ["destroyer", "frigate", "corvette"]
            )
            else 0
        )

    def can_buy_mining_spaceship(self):
        return (
            1
            if self.current_location.has_marketplace()
            and self.current_location.has_storage()
            and any(
                self.wallet
                >= self.current_location.marketplace.inventory[spaceship]["price"]
                and self.current_location.marketplace.inventory[spaceship]["quantity"]
                > 0
                for spaceship in ["extractor", "miner"]
            )
            else 0
        )

    def can_sell_mining_spaceship(self):
        return (
            1
            if self.current_location.has_marketplace()
            and self.current_location.has_storage()
            and any(
                self.current_location.storage.get_item(self, spaceship) > 0
                for spaceship in ["extractor", "miner"]
            )
            else 0
        )

    def can_build_miner(self):
        return (
            1
            if self.current_location.has_factory()
            and self.current_location.has_storage()
            and self.current_location.storage.get_item(self, "cosmic_resin") >= 160
            and self.current_location.storage.get_item(self, "hyper_dust") >= 70
            and self.current_location.storage.get_item(self, "presolar_grain") >= 180
            and self.current_location.storage.get_item(self, "nebulite") >= 35
            and self.current_location.storage.get_item(self, "water_ice") >= 55
            else 0
        )

    def can_build_corvette(self):
        return (
            1
            if self.current_location.has_factory()
            and self.current_location.has_storage()
            and self.current_location.storage.get_item(self, "cosmic_ice") >= 320
            and self.current_location.storage.get_item(self, "helium") >= 360
            and self.current_location.storage.get_item(self, "hyper_dust") >= 140
            and self.current_location.storage.get_item(self, "nebulite") >= 70
            and self.current_location.storage.get_item(self, "water_ice") >= 110
            else 0
        )

    def can_build_frigate(self):
        return (
            1
            if self.current_location.has_factory()
            and self.current_location.has_storage()
            and self.current_location.storage.get_item(self, "cosmic_dust") >= 8000
            and self.current_location.storage.get_item(self, "cosmic_ice") >= 6000
            and self.current_location.storage.get_item(self, "helium") >= 5000
            and self.current_location.storage.get_item(self, "hyper_dust") >= 4000
            and self.current_location.storage.get_item(self, "spacetime_dust") >= 7000
            and self.current_location.storage.get_item(self, "astralite") >= 2500
            and self.current_location.storage.get_item(self, "hyperspace_flux") >= 1800
            and self.current_location.storage.get_item(self, "pulsar_residue") >= 2000
            and self.current_location.storage.get_item(self, "rare_earth_minerals")
            >= 1500
            and self.current_location.storage.get_item(self, "voidium") >= 2200
            else 0
        )

    def can_build_destroyer(self):
        return (
            1
            if self.current_location.has_factory()
            and self.current_location.has_storage()
            and self.current_location.storage.get_item(self, "cosmic_ice") >= 50000
            and self.current_location.storage.get_item(self, "presolar_grain") >= 80000
            and self.current_location.storage.get_item(self, "photon_dust") >= 100000
            and self.current_location.storage.get_item(self, "quantum_foam") >= 120000
            and self.current_location.storage.get_item(self, "solar_dust") >= 150000
            and self.current_location.storage.get_item(self, "antigravity_dust")
            >= 100000
            and self.current_location.storage.get_item(self, "etherium") >= 120000
            and self.current_location.storage.get_item(self, "hyperspace_flux") >= 50000
            and self.current_location.storage.get_item(self, "nullmetal") >= 150000
            and self.current_location.storage.get_item(self, "rare_earth_minerals")
            >= 80000
            and self.current_location.storage.get_item(self, "aetherium") >= 30000
            and self.current_location.storage.get_item(self, "chronomite") >= 70000
            and self.current_location.storage.get_item(self, "dimensional_rift_residue")
            >= 40000
            and self.current_location.storage.get_item(self, "warpflux") >= 60000
            and self.current_location.storage.get_item(self, "xylothium") >= 50000
            else 0
        )

    def can_build_extractor(self):
        return (
            1
            if self.current_location.has_factory()
            and self.current_location.has_storage()
            and self.current_location.storage.get_item(self, "cosmic_resin") >= 4000
            and self.current_location.storage.get_item(self, "hyper_dust") >= 3000
            and self.current_location.storage.get_item(self, "presolar_grain") >= 2500
            and self.current_location.storage.get_item(self, "nebulite") >= 2000
            and self.current_location.storage.get_item(self, "water_ice") >= 3500
            and self.current_location.storage.get_item(self, "astralite") >= 1250
            and self.current_location.storage.get_item(self, "etherium") >= 900
            and self.current_location.storage.get_item(self, "hyperspace_flux") >= 1000
            and self.current_location.storage.get_item(self, "pulsar_residue") >= 750
            and self.current_location.storage.get_item(self, "voidium") >= 1100
            else 0
        )

    def can_pilot(self, ship_class):
        return (
            1
            if (
                (
                    self.current_location.has_hangar()
                    and self.current_location.hangar.has_spaceship(self, ship_class)
                )
                or (
                    self.current_location.has_storage()
                    and self.current_location.storage.get_item(self, ship_class) > 0
                )
            )
            and self.spaceship.ship_class != ship_class
            else 0
        )

    def can_pilot_miner(self):
        return self.can_pilot("miner")

    def can_pilot_extractor(self):
        return self.can_pilot("extractor")

    def can_pilot_corvette(self):
        return self.can_pilot("corvette")

    def can_pilot_frigate(self):
        return self.can_pilot("frigate")

    def can_pilot_destroyer(self):
        return self.can_pilot("destroyer")

    def can_place_bounty(self):
        return 1 if self.wallet >= MIN_BOUNTY and self.last_killed_by is not None else 0

    def get_current_spaceship_type(self):
        if isinstance(self.spaceship, Explorer):
            return 1
        elif isinstance(self.spaceship, Miner):
            return 2
        elif isinstance(self.spaceship, Extractor):
            return 3
        elif isinstance(self.spaceship, Corvette):
            return 4
        elif isinstance(self.spaceship, Frigate):
            return 5
        elif isinstance(self.spaceship, Destroyer):
            return 6
        else:
            return 0

    def get_current_location_type(self):
        if isinstance(self.current_location, EmptySpace):
            return 1
        elif isinstance(self.current_location, Planet):
            return 2
        elif isinstance(self.current_location, AsteroidBelt):
            return 3
        elif isinstance(self.current_location, Moon):
            return 4
        elif isinstance(self.current_location, Stargate):
            return 5
        elif isinstance(self.current_location, Debris):
            return 6
        else:
            return 0

    def get_next_system_info(self):
        if isinstance(self.current_location, Stargate):
            distance = self.current_location.distance
            next_sys = self.current_location.destination
            return (
                distance,
                len(next_sys.stargates),
                len(next_sys.planets),
                len(next_sys.asteroid_belts),
                len(next_sys.moons),
            )
        else:
            return 0, 0, 0, 0, 0

    def calculate_price_index(self):
        if self.current_location.has_marketplace():
            overprice_count = 0
            market_items = self.current_location.marketplace.inventory.items()
            if len(market_items) > 0:
                for item, data in market_items:
                    price = data["price"]
                    material = material_manager.get_material(item)
                    if material:
                        base_price = material_manager.guess_base_price(material.rarity)
                    else:
                        spaceship_info = spaceship_manager.get_spaceship(item)
                        if spaceship_info:
                            base_price = spaceship_info.base_price
                        else:
                            base_price = DEFAULT_SPACESHIP_COST

                    if price > base_price * 2:
                        overprice_count += 3
                    elif price > base_price * 1.5:
                        overprice_count += 2
                    elif price > base_price:
                        overprice_count += 1
                    elif price < base_price * 0.25:
                        overprice_count -= 3
                    elif price < base_price * 0.5:
                        overprice_count -= 2
                    elif price < base_price:
                        overprice_count -= 1

                price_index = int(round(overprice_count / len(market_items) * 10, 0))
                if price_index != 0:
                    logger.debug(f"Price index: {price_index}")
                return price_index
            else:
                return 0
        else:
            return 0

    def calculate_distance_from_home(self):
        distance = self.universe.calculate_minimum_distance(
            self.current_system, self.home_system
        )
        logger.debug(f"Distance from home is {distance}")
        return distance

    def get_factory_info(self):
        if self.current_location.has_factory():
            level = self.current_location.factory.level
            return level
        else:
            return 0

    def get_mission_info(self):
        if self.current_location.has_mission_center():
            best_reward_mission = (
                self.current_location.mission_center.get_best_reward_mission()
            )
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

    def get_full_state(self):
        distance, next_stargate, next_planet, next_asteroid_belt, next_moon = (
            self.get_next_system_info()
        )
        factory_level = self.get_factory_info()
        mission_difficulty, mission_reward = self.get_mission_info()
        ship_cargo_size = self.spaceship.calculate_cargo_size()
        cargo_full = 1 if self.spaceship.is_cargo_full() else 0
        state = {
            "can_move_planet": self.can_move_planet(),
            "can_move_asteroid_belt": self.can_move_asteroid_belt(),
            "can_move_moon": self.can_move_moon(),
            "can_move_stargate": self.can_move_stargate(),
            "can_move_debris": self.can_move_debris(),
            "can_travel": self.can_travel(),
            "can_explore": self.can_explore(),
            "can_mine": self.can_mine(),
            "can_unload": self.can_unload(),
            "can_buy": self.can_buy(),
            "can_sell": self.can_sell(),
            "can_invest_factory": self.can_invest_factory(),
            "can_invest_drydock": self.can_invest_drydock(),
            "can_collect": self.can_collect(),
            "can_mission": self.can_mission(),
            "can_repair": self.can_repair(),
            "can_upgrade": self.can_upgrade(),
            "can_salvage": self.can_salvage(),
            "can_attack": self.can_attack(),
            "can_bombard": self.can_bombard(),
            "can_set_home": self.can_set_home(),
            "can_buy_warship": self.can_buy_warship(),
            "can_sell_warship": self.can_sell_warship(),
            "can_buy_mining_spaceship": self.can_buy_mining_spaceship(),
            "can_sell_mining_spaceship": self.can_sell_mining_spaceship(),
            "can_build_miner": self.can_build_miner(),
            "can_build_corvette": self.can_build_corvette(),
            "can_build_frigate": self.can_build_frigate(),
            "can_build_destroyer": self.can_build_destroyer(),
            "can_build_extractor": self.can_build_extractor(),
            "can_pilot_miner": self.can_pilot_miner(),
            "can_pilot_corvette": self.can_pilot_corvette(),
            "can_pilot_frigate": self.can_pilot_frigate(),
            "can_pilot_destroyer": self.can_pilot_destroyer(),
            "can_pilot_extractor": self.can_pilot_extractor(),
            "can_place_bounty": self.can_place_bounty(),
            "spaceship": self.get_current_spaceship_type(),
            "spaceship_level": self.spaceship.level,
            "weapon": self.spaceship.weapon,
            "shield": self.spaceship.shield,
            "armor": self.spaceship.armor,
            "hull": self.spaceship.hull,
            "strength": int(self.spaceship.weapon / 10),
            "health": int((self.spaceship.armor + self.spaceship.hull) / 10),
            "cargo_full": cargo_full,
            "stargate": len(self.current_system.stargates),
            "planet": len(self.current_system.planets),
            "asteroid_belt": len(self.current_system.asteroid_belts),
            "moon": len(self.current_system.moons),
            "debris": len(self.current_system.debrises),
            "location": self.get_current_location_type(),
            "system_player": len(self.current_system.players),
            "location_player": len(self.current_location.players),
            "distance_from_home": int(self.calculate_distance_from_home() / 10),
            "distance": distance,
            "next_stargate": next_stargate,
            "next_planet": next_planet,
            "next_asteroid_belt": next_asteroid_belt,
            "next_moon": next_moon,
            "factory_level": factory_level,
            "mission_difficulty": mission_difficulty,
            "mission_reward": mission_reward,
            "wallet": (
                round(int(math.log(self.wallet) * 100) / 100, 2)
                if self.wallet > 0
                else 0
            ),
            "net_worth": (
                round(int(math.log(self.net_worth) * 100) / 100, 2)
                if self.net_worth > 0
                else 0
            ),
            "ship_cargo_size": (
                round(int(math.log(ship_cargo_size) * 100) / 100, 2)
                if ship_cargo_size > 0
                else 0
            ),
            "total_investment": (
                round(int(math.log(self.total_investment) * 100) / 100, 2)
                if self.total_investment > 0
                else 0
            ),
            "rich": int(math.log10(self.wallet) if self.wallet > 0 else 0),
            "ship_fat": int(math.log10(ship_cargo_size) if ship_cargo_size > 0 else 0),
            "distance_traveled": self.distance_traveled,
            "mission_completed": self.mission_completed,
            "total_damage": (
                round(int(math.log(self.total_damage) * 100) / 100, 2)
                if self.total_damage > 0
                else 0
            ),
            "kill": self.kill,
            "destroy": self.destroy,
            "death": self.death,
            "score": self.score,
        }
        return state

    def get_reduced_state(self):
        state_dict = self.get_full_state()
        # reduce state space
        state_dict.pop("weapon")
        state_dict.pop("shield")
        state_dict.pop("armor")
        state_dict.pop("hull")
        state_dict.pop("score")
        state_dict.pop("wallet")
        state_dict.pop("net_worth")
        state_dict.pop("ship_cargo_size")
        state_dict.pop("total_investment")
        state_dict.pop("distance_traveled")
        state_dict.pop("mission_completed")
        state_dict.pop("total_damage")
        state_dict.pop("kill")
        state_dict.pop("destroy")
        state_dict.pop("death")
        net_worth_gain = (
            round(
                self.state_memory[-1]["net_worth"] - self.state_memory[0]["net_worth"],
                2,
            )
            if len(self.state_memory) > 1
            else 0
        )
        ship_cargo_size_gain = (
            round(
                self.state_memory[-1]["ship_cargo_size"]
                - self.state_memory[0]["ship_cargo_size"],
                2,
            )
            if len(self.state_memory) > 1
            else 0
        )
        investment_gain = (
            round(
                self.state_memory[-1]["total_investment"]
                - self.state_memory[0]["total_investment"],
                2,
            )
            if len(self.state_memory) > 1
            else 0
        )
        distance_gain = (
            self.state_memory[-1]["distance_traveled"]
            - self.state_memory[0]["distance_traveled"]
            if len(self.state_memory) > 1
            else 0
        )
        mission_gain = (
            self.state_memory[-1]["mission_completed"]
            - self.state_memory[0]["mission_completed"]
            if len(self.state_memory) > 1
            else 0
        )
        damage_gain = (
            round(
                self.state_memory[-1]["total_damage"]
                - self.state_memory[0]["total_damage"],
                2,
            )
            if len(self.state_memory) > 1
            else 0
        )
        kill_gain = (
            self.state_memory[-1]["kill"] - self.state_memory[0]["kill"]
            if len(self.state_memory) > 1
            else 0
        )
        destroy_gain = (
            self.state_memory[-1]["destroy"] - self.state_memory[0]["destroy"]
            if len(self.state_memory) > 1
            else 0
        )
        death_gain = (
            self.state_memory[-1]["death"] - self.state_memory[0]["death"]
            if len(self.state_memory) > 1
            else 0
        )
        health_gain = (
            self.state_memory[-1]["health"] - self.state_memory[0]["health"]
            if len(self.state_memory) > 1
            else 0
        )
        score_gain = (
            self.state_memory[-1]["score"] - self.state_memory[0]["score"]
            if len(self.state_memory) > 1
            else 0
        )
        state_dict["net_worth_gain"] = net_worth_gain
        state_dict["ship_cargo_size_gain"] = ship_cargo_size_gain
        state_dict["investment_gain"] = investment_gain
        state_dict["distance_gain"] = distance_gain
        state_dict["mission_gain"] = mission_gain
        state_dict["damage_gain"] = damage_gain
        state_dict["kill_gain"] = kill_gain
        state_dict["destroy_gain"] = destroy_gain
        state_dict["death_gain"] = death_gain
        state_dict["health_gain"] = health_gain
        state_dict["score_gain"] = score_gain

        state = np.array(list(state_dict.values()))

        return state

    def calculate_death_penalty(self, learning_rate, state_memory):
        return (
            0.01
            * learning_rate
            * (state_memory[-1]["death"] - state_memory[0]["death"])
            if len(state_memory) > 1
            else 0
        )

    def calculate_health_reward(self, learning_rate, state_memory):
        return (
            0.0001
            * learning_rate
            * (state_memory[-1]["health"] - state_memory[0]["health"])
            if len(state_memory) > 1
            else 0
        )

    def calculate_reward(self, goal, learning_rate, state_memory):
        if goal == Goal.MAX_WEALTH:
            net_worth_reward = (
                learning_rate
                * round(state_memory[-1]["net_worth"] - state_memory[0]["net_worth"], 2)
                if len(state_memory) > 1
                else 0
            )
            health_reward = self.calculate_health_reward(learning_rate, state_memory)
            death_penalty = self.calculate_death_penalty(learning_rate, state_memory)
            total_reward = net_worth_reward + health_reward - death_penalty - 0.0001
            logger.debug(f"{self.name} Total Reward: {total_reward}")
            return total_reward
        elif goal == Goal.MAX_KILL:
            kill_reward = (
                learning_rate * (state_memory[-1]["kill"] - state_memory[0]["kill"])
                if len(state_memory) > 1
                else 0
            )
            health_reward = self.calculate_health_reward(learning_rate, state_memory)
            death_penalty = self.calculate_death_penalty(learning_rate, state_memory)
            total_reward = kill_reward + health_reward - death_penalty - 0.0001
            logger.debug(f"{self.name} Total Reward: {total_reward}")
            return total_reward
        elif goal == Goal.MAX_DAMAGE:
            damage_reward = (
                learning_rate
                * round(
                    state_memory[-1]["total_damage"] - state_memory[0]["total_damage"],
                    2,
                )
                if len(state_memory) > 1
                else 0
            )
            health_reward = self.calculate_health_reward(learning_rate, state_memory)
            death_penalty = self.calculate_death_penalty(learning_rate, state_memory)
            total_reward = damage_reward + health_reward - death_penalty - 0.0001
            logger.debug(f"{self.name} Total Reward: {total_reward}")
            return total_reward
        elif goal == Goal.MAX_MISSION:
            mission_reward = (
                learning_rate
                * (
                    state_memory[-1]["mission_completed"]
                    - state_memory[0]["mission_completed"]
                )
                if len(state_memory) > 1
                else 0
            )
            health_reward = self.calculate_health_reward(learning_rate, state_memory)
            death_penalty = self.calculate_death_penalty(learning_rate, state_memory)
            total_reward = mission_reward + health_reward - death_penalty - 0.0001
            logger.debug(f"{self.name} Total Reward: {total_reward}")
            return total_reward
        elif goal == Goal.MAX_SCORE:
            score_reward = (
                learning_rate * (state_memory[-1]["score"] - state_memory[0]["score"])
                if len(state_memory) > 1
                else 0
            )
            health_reward = self.calculate_health_reward(learning_rate, state_memory)
            death_penalty = self.calculate_death_penalty(learning_rate, state_memory)
            total_reward = score_reward + health_reward - death_penalty - 0.0001
            logger.debug(f"{self.name} Total Reward: {total_reward}")
            return total_reward
        else:
            logger.debug("Random reward")
            return -0.0001

    def to_json(self):
        ship_cargo_size = self.spaceship.calculate_cargo_size()
        return {
            "name": self.name,
            "system": self.current_system.name,
            "location": self.current_location.name,
            "wallet": self.wallet,
            "netWorth": self.net_worth,
            "shipCargoSize": ship_cargo_size,
            "score": self.score,
            "investment": self.total_investment,
            "profit": self.profit_collected,
            "roi": self.roi,
            "distance": self.distance_traveled,
            "mission": self.mission_completed,
            "damage": self.total_damage,
            "kill": self.kill,
            "death": self.death,
            "destroy": self.destroy,
            "build": self.build,
            "mined": self.mined,
            "actionHistory": self.action_history,
            "spaceship": self.spaceship.to_json(),
        }

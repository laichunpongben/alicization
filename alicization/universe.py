# universe.py

import random
import heapq
import logging

import numpy as np

from .star_system import StarSystem
from .locations.stargate import Stargate
from .managers.time_keeper import TimeKeeper
from .managers.player_manager import PlayerManager
from .managers.economy import Economy

logger = logging.getLogger(__name__)

time_keeper = TimeKeeper()
player_manager = PlayerManager()
economy = Economy()

MAX_CONNECTIONS = 5
MIN_CONNECTIONS = 1
MAX_DISTANCE = 100


class Universe:
    def __init__(self, initial_systems: int):
        self.star_systems = []
        self._players = []

        self.total_distance_traveled = 0
        self.total_damage_dealt = 0
        self.total_kill = 0
        self.total_destroy = 0
        self.total_earning = 0
        self.total_spending = 0
        self.total_build = 0
        self.total_mined = 0
        self.total_mission_completed = 0
        self.total_transaction = 0
        self.total_trade_revenue = 0
        self.galactic_price_index = 1

        for _ in range(initial_systems):
            self.add_star_system()

        self.create_sparse_graph()

    @property
    def players(self):
        return self._players

    def add_player(self, player):
        self._players.append(player)
        player_manager.update_universe(player.name, self)

    def remove_player(self, player):
        self._players.remove(player)
        player_manager.update_universe(player.name, None)

    def add_star_system(self):
        new_system = StarSystem(f"System {len(self.star_systems)}")
        self.star_systems.append(new_system)

    def create_sparse_graph(self):
        # Use Prim's algorithm to create a Minimum Spanning Tree (MST)
        mst_edges = []
        visited = set()
        min_heap = [(0, random.choice(self.star_systems), None)]

        while min_heap and len(mst_edges) < len(self.star_systems) - 1:
            weight, current_system, previous_system = heapq.heappop(min_heap)
            if current_system not in visited:
                visited.add(current_system)
                if previous_system is not None:
                    mst_edges.append((weight, previous_system, current_system))
                for neighbor in self.star_systems:
                    if neighbor != current_system and neighbor not in visited:
                        heapq.heappush(
                            min_heap,
                            (random.randint(1, MAX_DISTANCE), neighbor, current_system),
                        )

        for system in self.star_systems:
            system.stargates = []

        for distance, system1, system2 in mst_edges:
            self.connect_systems(system1, system2, distance)

        remaining_edges = [
            (random.randint(1, 10), system1, system2)
            for system1 in self.star_systems
            for system2 in self.star_systems
            if system1 != system2 and (system1, system2) not in mst_edges
        ]

        additional_edges = min(len(remaining_edges), int(0.1 * len(self.star_systems)))
        for _ in range(additional_edges):
            if remaining_edges:
                distance, system1, system2 = random.choice(remaining_edges)
                self.connect_systems(system1, system2, distance)
                remaining_edges.remove((distance, system1, system2))

    def connect_systems(self, system, neighbor, distance: int):
        stargate_to = Stargate(system, neighbor, distance)
        system.add_stargate(stargate_to)
        stargate_from = Stargate(neighbor, system, distance)
        neighbor.add_stargate(stargate_from)

    def health_check(self):
        expand_threshold_small = 2 ** (len(self.star_systems) / 2)
        expand_threshold_large = 2 ** len(self.star_systems)
        if (
            self.total_distance_traveled >= expand_threshold_small
            or self.total_kill * 10 >= expand_threshold_small
            or self.total_damage_dealt >= expand_threshold_large
            or self.total_spending >= expand_threshold_large
        ):
            self.expand_universe()

        for system in self.star_systems:
            for belt in system.asteroid_belts:
                belt.respawn_resources()

            for planet in system.planets:
                for building in planet.buildings:
                    building.repair()

                for _, spaceships in planet.hangar.spaceships.items():
                    for spaceship in spaceships:
                        spaceship.recharge_shield()

                planet.marketplace.match_orders()
                planet.marketplace.clean_up()

            for moon in system.moons:
                for building in moon.buildings:
                    building.repair()

                moon.mission_center.respawn_missions()
                moon.mission_center.clean_up()

                for _, spaceships in moon.hangar.spaceships.items():
                    for spaceship in spaceships:
                        spaceship.recharge_shield()

            system.debrises = [d for d in system.debrises if not d.is_empty()]

        self.total_transaction = economy.total_transaction
        self.total_trade_revenue = economy.total_trade_revenue

        economy.update_stats()
        self.galactic_price_index = economy.galactic_price_index

        self.galactic_affordability = self.calculate_galactic_affordability()
        self.galactic_productivity = self.calculate_galactic_productivity()

        time_keeper.tick()

    def expand_universe(self):
        self.add_star_system()
        new_system = self.star_systems[-1]
        connected_systems = [
            s
            for s in self.star_systems
            if s != new_system and len(s.stargates) < MAX_CONNECTIONS
        ]

        if connected_systems:
            initial_connection = random.choice(connected_systems)
            distance = int(np.random.uniform(1, 10))
            self.connect_systems(new_system, initial_connection, distance)

            num_connections = min(
                np.random.poisson(0, 1)[0], len(connected_systems) - 1, MAX_CONNECTIONS
            )
            neighboring_systems = random.sample(
                [s for s in connected_systems if s != initial_connection],
                num_connections,
            )
            for system in neighboring_systems:
                # Ensure that the total number of connections in the graph remains sparse
                if (
                    len(system.stargates) < MAX_CONNECTIONS
                    and len(new_system.stargates) < MAX_CONNECTIONS
                ):
                    distance = random.randint(1, MAX_DISTANCE)
                    self.connect_systems(system, new_system, distance)

        logger.info(f"New star system added: {new_system.name}")

    def get_random_system(self):
        return random.choice(self.star_systems)

    def get_random_system_with_planet(self):
        return random.choice([sys for sys in self.star_systems if len(sys.planets) > 0])

    def full_check_all_players(self):
        for player in self._players:
            player.total_investment = player.calculate_total_investment()

    def calculate_galactic_affordability(self):
        return (
            sum(player.affordability for player in self._players) / len(self._players)
            if len(self._players) > 0
            else 1
        )

    def calculate_galactic_productivity(self):
        return (
            sum(player.productivity for player in self._players) / len(self._players)
            if len(self._players) > 0
            else 1
        )

    def debug_print(self):
        logger.info("Universe Debug Information:")
        logger.info(f"Number of star systems: {len(self.star_systems)}")
        for i, system in enumerate(self.star_systems):
            logger.info(f"Star System {i}: {system.name}")
            logger.info(
                f"Neighboring Systems: {[neighboring_system.name for neighboring_system in system.neighboring_systems]}"
            )

    def to_json(self):
        return {
            "numSystem": len(self.star_systems),
            "numPlayer": len(self.players),
            "totalDistanceTraveled": self.total_distance_traveled,
            "totalDamageDealt": self.total_damage_dealt,
            "totalKill": self.total_kill,
            "totalDestroy": self.total_destroy,
            "totalEarning": self.total_earning,
            "totalSpending": self.total_spending,
            "totalBuild": self.total_build,
            "totalMined": self.total_mined,
            "totalMissionCompleted": self.total_mission_completed,
            "totalTransaction": self.total_transaction,
            "totalTradeRevenue": self.total_trade_revenue,
            "galacticPriceIndex": self.galactic_price_index,
            "galacticAffordability": self.galactic_affordability,
            "galacticProductivity": self.galactic_productivity,
        }

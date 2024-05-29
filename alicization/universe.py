# universe.py

import random
import heapq
import logging

import numpy as np

from .star_system import StarSystem
from .locations.stargate import Stargate
from .managers.material_manager import MaterialManager
from .managers.spaceship_manager import SpaceshipManager

logger = logging.getLogger(__name__)

material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()

MAX_CONNECTIONS = 5
MIN_CONNECTIONS = 1


class Universe:
    def __init__(self, initial_systems):
        self.current_turn = 1
        self.star_systems = []
        self._players = []

        self.total_distance_traveled = 0
        self.total_damage_dealt = 0
        self.total_kill = 0
        self.total_destroy = 0
        self.total_money_spent = 0
        self.total_build = 0
        self.total_mined = 0
        self.total_mission_completed = 0
        self.global_price_index = 1

        for _ in range(initial_systems):
            self.add_star_system()

        self.create_sparse_graph()

    @property
    def players(self):
        return self._players

    @players.setter
    def players(self, value):
        if not isinstance(value, list):
            raise ValueError("Players must be a list")
        self._players = value

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        self.players.remove(player)

    def add_star_system(self):
        new_system = StarSystem(f"System {len(self.star_systems)}")
        self.star_systems.append(new_system)

    def create_sparse_graph(self):
        edges = [
            (int(np.random.uniform(1, 10)), system1, system2)
            for i, system1 in enumerate(self.star_systems)
            for j, system2 in enumerate(self.star_systems)
            if i < j
        ]
        edges.sort(key=lambda x: x[0])

        parent = {system: system for system in self.star_systems}
        rank = {system: 0 for system in self.star_systems}

        def find(system):
            if parent[system] != system:
                parent[system] = find(parent[system])
            return parent[system]

        def union(system1, system2):
            root1 = find(system1)
            root2 = find(system2)
            if root1 != root2:
                if rank[root1] > rank[root2]:
                    parent[root2] = root1
                else:
                    parent[root1] = root2
                    if rank[root1] == rank[root2]:
                        rank[root2] += 1

        mst_edges = []
        for distance, system1, system2 in edges:
            if find(system1) != find(system2):
                union(system1, system2)
                mst_edges.append((distance, system1, system2))

        for system in self.star_systems:
            system.stargates = []

        for distance, system1, system2 in mst_edges:
            self.connect_systems(system1, system2, distance)

        remaining_edges = [
            (distance, system1, system2)
            for distance, system1, system2 in edges
            if (system1, system2) not in mst_edges
        ]
        additional_edges = min(len(remaining_edges), int(0.1 * len(self.star_systems)))

        for _ in range(additional_edges):
            if remaining_edges:
                distance, system1, system2 = random.choice(remaining_edges)
                self.connect_systems(system1, system2, distance)
                remaining_edges.remove((distance, system1, system2))

    def connect_systems(self, system, neighbor, distance):
        stargate_to = Stargate(system, neighbor, distance)
        system.add_stargate(stargate_to)
        stargate_from = Stargate(neighbor, system, distance)
        neighbor.add_stargate(stargate_from)

    def calculate_minimum_distance(self, start_system, end_system):
        if start_system == end_system:
            return 0

        distances = {system: float("inf") for system in self.star_systems}
        distances[start_system] = 0
        priority_queue = [(0, start_system)]

        while priority_queue:
            current_distance, current_system = heapq.heappop(priority_queue)

            if current_distance > distances[current_system]:
                continue

            for stargate in current_system.stargates:
                neighbor = stargate.destination
                distance = stargate.distance
                new_distance = current_distance + distance

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    heapq.heappush(priority_queue, (new_distance, neighbor))

        return distances[end_system]

    def health_check(self):
        self.current_turn += 1
        expand_threshold_small = 2 ** (len(self.star_systems) / 2)
        expand_threshold_large = 2 ** len(self.star_systems)
        if (
            self.total_distance_traveled >= expand_threshold_small
            or self.total_kill * 10 >= expand_threshold_small
            or self.total_damage_dealt >= expand_threshold_large
            or self.total_money_spent >= expand_threshold_large
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

            for moon in system.moons:
                for building in moon.buildings:
                    building.repair()

                moon.mission_center.respawn_missions()
                moon.mission_center.clean_up()

                for _, spaceships in moon.hangar.spaceships.items():
                    for spaceship in spaceships:
                        spaceship.recharge_shield()

            system.debrises = [d for d in system.debrises if not d.is_empty()]

        self.global_price_index = self.calculate_global_price_index()

    def expand_universe(self):
        self.add_star_system()
        new_system = self.star_systems[-1]
        connected_systems = [
            s for s in self.star_systems if len(s.stargates) < MAX_CONNECTIONS
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
                    distance = int(np.random.uniform(1, 10))
                    self.connect_systems(system, new_system, distance)

        logger.info(f"New star system added: {new_system.name}")

    def get_random_system(self):
        return random.choice(self.star_systems)

    def get_random_system_with_planet(self):
        return random.choice([sys for sys in self.star_systems if len(sys.planets) > 0])

    def calculate_global_price_index(self):
        markets = []
        for system in self.star_systems:
            for planet in system.planets:
                markets.append(planet.marketplace)

        average_prices = {}
        total_deviation = 0
        num_items = 0

        for market in markets:
            for item_type, data in market.inventory.items():
                if item_type not in average_prices:
                    average_prices[item_type] = {"total_price": 0, "total_quantity": 0}

                total_quantity = data["quantity"]
                total_price = data["price"] * total_quantity

                average_prices[item_type]["total_price"] += total_price
                average_prices[item_type]["total_quantity"] += total_quantity

                # If total quantity is 0, assume average price is base price
                if total_quantity == 0:
                    material = material_manager.get_material(item_type)
                    spaceship = spaceship_manager.get_spaceship(item_type)
                    if material:
                        base_price = material_manager.guess_base_price(material.rarity)
                    elif spaceship:
                        base_price = spaceship.base_price
                    else:
                        continue
                    average_prices[item_type]["total_price"] += base_price
                    average_prices[item_type]["total_quantity"] += 1

        for item_type, avg_price_data in average_prices.items():
            material = material_manager.get_material(item_type)
            spaceship = spaceship_manager.get_spaceship(item_type)
            if material:
                base_price = material_manager.guess_base_price(material.rarity)
            elif spaceship:
                base_price = spaceship.base_price
            else:
                continue

            average_price = (
                avg_price_data["total_price"] / avg_price_data["total_quantity"]
            )
            deviation = average_price / base_price
            total_deviation += deviation
            num_items += 1

        if num_items == 0:
            return 1  # Default index if no items found
        else:
            return total_deviation / num_items

    def full_check_all_players(self):
        for player in self._players:
            player.total_investment = player.calculate_total_investment()

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
            "totalMoneySpent": self.total_money_spent,
            "totalBuild": self.total_build,
            "totalMined": self.total_mined,
            "totalMissionCompleted": self.total_mission_completed,
            "globalPriceIndex": self.global_price_index,
        }

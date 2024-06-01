# util.py

import heapq
from typing import List


def calculate_minimum_distance(star_systems: List, start_system, end_system):
    if start_system == end_system:
        return 0

    distances = {system: float("inf") for system in star_systems}
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

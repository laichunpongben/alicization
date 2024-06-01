# location_map.py

import logging

logger = logging.getLogger(__name__)


class LocationMap:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(LocationMap, cls).__new__(cls)
            cls.__instance._map = {}
        return cls.__instance

    @property
    def map(self):
        return self._map

    def get_location(self, location_name: str):
        return self._map.get(location_name)

    def add_location(self, location):
        if not location.name in self._map:
            self._map[location.name] = location
        else:
            logger.error(f"Location {location.name} already exists in map!")

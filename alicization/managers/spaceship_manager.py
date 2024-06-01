# spaceship_manager.py

import csv
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpaceshipInfo:
    ship_class: str
    max_shield: int
    shield_upgrade: int
    max_armor: int
    armor_upgrade: int
    max_hull: int
    hull_upgrade: int
    max_power: int
    weapon: int
    weapon_upgrade: int
    engine: int
    evasion: float
    max_cargo_size: int
    base_repair_cost: int
    base_upgrade_cost: int
    max_level: int
    mining: int
    base_price: float


class SpaceshipManager:
    __instance = None

    def __new__(cls, spaceships_file=None):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            if spaceships_file is None:
                spaceships_file = (
                    Path(__file__).resolve().parent.parent / "data" / "spaceships.csv"
                )
            cls.__instance.spaceships = cls.__instance._load_spaceships(spaceships_file)
        return cls.__instance

    def _load_spaceships(self, spaceships_file):
        spaceships = {}
        try:
            with open(spaceships_file, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    spaceship_info = SpaceshipInfo(
                        ship_class=row["ship_class"],
                        max_shield=int(row["max_shield"]),
                        shield_upgrade=int(row["shield_upgrade"]),
                        max_armor=int(row["max_armor"]),
                        armor_upgrade=int(row["armor_upgrade"]),
                        max_hull=int(row["max_hull"]),
                        hull_upgrade=int(row["hull_upgrade"]),
                        max_power=int(row["max_power"]),
                        weapon=int(row["weapon"]),
                        weapon_upgrade=int(row["weapon_upgrade"]),
                        engine=int(row["engine"]),
                        evasion=float(row["evasion"]),
                        max_cargo_size=int(row["max_cargo_size"]),
                        base_repair_cost=int(row["base_repair_cost"]),
                        base_upgrade_cost=int(row["base_upgrade_cost"]),
                        max_level=int(row["max_level"]),
                        mining=int(row["mining"]),
                        base_price=float(row["base_price"]),
                    )
                    spaceships[spaceship_info.ship_class] = spaceship_info
        except FileNotFoundError:
            logger.error(f"Error: Spaceships file '{spaceships_file}' not found.")
        except Exception as e:
            logger.error(f"Error loading spaceships: {e}")
        return spaceships

    def get_spaceship(self, spaceship_type):
        return self.spaceships.get(spaceship_type)

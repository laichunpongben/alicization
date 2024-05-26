# blueprint_manager.py

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Blueprint:
    name: str
    components: dict


class BlueprintManager:
    __instance = None

    def __new__(cls, blueprint_file=None):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            if blueprint_file is None:
                blueprint_file = (
                    Path(__file__).resolve().parent.parent / "data" / "blueprints.csv"
                )
            cls.__instance.blueprints = cls.__instance.load_blueprints(blueprint_file)
        return cls.__instance

    def load_blueprints(self, blueprint_file):
        blueprints = {}
        try:
            with open(blueprint_file, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    name = row["name"]
                    child = row["child"]
                    quantity = int(row["quantity"])
                    blueprints.setdefault(name, {})[child] = quantity
        except FileNotFoundError:
            logger.error(f"Error: Blueprint file '{blueprint_file}' not found.")
        except Exception as e:
            logger.error(f"Error loading blueprints: {e}")
        return blueprints

    def get_blueprint(self, name):
        components = self.blueprints.get(name, {})
        return Blueprint(name=name, components=components)

# material_manager.py

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Material:
    name: str
    rarity: int
    volume: int


class MaterialManager:
    __instance = None

    def __new__(cls, materials_file=None):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            if materials_file is None:
                materials_file = (
                    Path(__file__).resolve().parent.parent / "data" / "materials.csv"
                )
            cls.__instance.materials = cls.__instance._load_materials(materials_file)
        return cls.__instance

    def _load_materials(self, materials_file):
        materials = {}
        with open(materials_file, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                materials[row["name"]] = Material(
                    name=row["name"],
                    rarity=int(row["rarity"]),
                    volume=int(row["volume"]),
                )
        return materials

    def get_material(self, name):
        return self.materials.get(name)

    def get_rarity(self, name):
        material = self.get_material(name)
        if material:
            return material.rarity
        else:
            return 1

    def guess_base_price(self, rarity):
        return 2 ** (max(rarity - 1, 0))

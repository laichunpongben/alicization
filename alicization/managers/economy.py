# economy.py

from collections import deque, defaultdict
import logging

from .material_manager import MaterialManager
from .spaceship_manager import SpaceshipManager

logger = logging.getLogger(__name__)

material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()


class Economy:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Economy, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self._transactions = {}
        self._total_transaction = 0
        self._total_trade_quantity = defaultdict(int)
        self._weighted_averages = defaultdict(float)

    @property
    def transactions(self):
        return self._transactions

    @property
    def total_transaction(self):
        return self._total_transaction

    def push_transaction(self, transaction):
        item_type = transaction.item_type
        if item_type not in self._transactions:
            self._transactions[item_type] = deque(maxlen=100)
        self._transactions[item_type].append(transaction)
        self._total_transaction += 1

    def calculate_galactic_price_index(self):
        for item_type, transactions in self._transactions.items():
            total_quantity = sum(t.quantity for t in transactions)
            weighted_average = 0
            deviation_total = 0

            material = material_manager.get_material(item_type)
            spaceship = spaceship_manager.get_spaceship(item_type)
            if material:
                base_price = material_manager.guess_base_price(material.rarity)
            elif spaceship:
                base_price = spaceship.base_price
            else:
                base_price = 1

            for t in transactions:
                deviation = t.price / base_price
                deviation_total += deviation * t.quantity

            if total_quantity > 0:
                weighted_average = deviation_total / total_quantity

            self._total_trade_quantity[item_type] = total_quantity
            self._weighted_averages[item_type] = weighted_average

        total_weighted_average = 0
        total_item_types = 0
        for item_type, total_quantity in self._total_trade_quantity.items():
            if total_quantity > 0:
                total_weighted_average += self._weighted_averages[item_type]
                total_item_types += 1

        if total_item_types > 0:
            galactic_price_index = total_weighted_average / total_item_types
            return galactic_price_index
        else:
            return 1

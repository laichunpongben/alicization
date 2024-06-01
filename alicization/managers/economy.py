# economy.py

from collections import deque, defaultdict
from typing import List
import logging

from .time_keeper import TimeKeeper
from .material_manager import MaterialManager
from .spaceship_manager import SpaceshipManager

logger = logging.getLogger(__name__)

time_keeper = TimeKeeper()
material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()

PERIOD = 5000
MIN_UNIT_PRICE = 0.01


class Economy:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Economy, cls).__new__(cls)
        return cls.__instance

    def __init__(self):
        self._transactions = defaultdict(lambda: deque(maxlen=100))
        self._total_transaction = 0
        self._total_trade_revenue = 0
        self._galactic_price_index = 1

    @property
    def transactions(self):
        return self._transactions

    @property
    def total_transaction(self):
        return self._total_transaction

    @property
    def total_trade_revenue(self):
        return self._total_trade_revenue

    @property
    def galactic_price_index(self):
        return self._galactic_price_index

    def push_transaction(self, transaction):
        item_type = transaction.item_type
        self._transactions[item_type].append(transaction)
        self._total_transaction += 1
        self._total_trade_revenue += transaction.quantity * transaction.price

    def update_stats(self):
        self._galactic_price_index = self._calculate_galactic_price_index()

    def _calculate_galactic_price_index(self):
        total_weighted_average = 0
        total_item_types = 0

        for item_type, transactions in self._transactions.items():
            base_price = self._get_base_price(item_type)
            recent_transactions = [
                t for t in transactions if t.turn + PERIOD >= time_keeper.turn
            ]
            total_quantity, weighted_average = self._calculate_weighted_average(
                recent_transactions, base_price
            )
            if total_quantity > 0:
                total_weighted_average += weighted_average
                total_item_types += 1

        return total_weighted_average / total_item_types if total_item_types > 0 else 1

    def _get_base_price(self, item_type: str):
        material = material_manager.get_material(item_type)
        if material:
            base_price = material_manager.guess_base_price(material.rarity)
        else:
            spaceship_info = spaceship_manager.get_spaceship(item_type)
            if spaceship_info:
                base_price = spaceship_info.base_price
            else:
                logger.error(f"Missing price info: {item_type}")
                base_price = MIN_UNIT_PRICE
        return base_price

    def _calculate_weighted_average(self, transactions: List, base_price: float):
        total_quantity = sum(t.quantity for t in transactions)
        deviation_total = sum((t.price / base_price) * t.quantity for t in transactions)

        weighted_average = deviation_total / total_quantity if total_quantity > 0 else 0
        return total_quantity, weighted_average

# marketplace.py

import uuid
from dataclasses import dataclass
from collections import defaultdict
from bisect import insort
import math
import logging

from .building import Building
from .investable import Investable
from ..managers.time_keeper import TimeKeeper
from ..managers.location_map import LocationMap
from ..managers.player_manager import PlayerManager
from ..managers.material_manager import MaterialManager
from ..managers.spaceship_manager import SpaceshipManager
from ..managers.leaderboard import Leaderboard
from ..managers.economy import Economy

logger = logging.getLogger(__name__)

time_keeper = TimeKeeper()
location_map = LocationMap()
player_manager = PlayerManager()
material_manager = MaterialManager()
spaceship_manager = SpaceshipManager()
leaderboard = Leaderboard()
economy = Economy()


NUM_TURN_BID_ORDER_EXPIRY = 400
NUM_TURN_ASK_ORDER_EXPIRY = 100
BASE_SERVICE_FEE_RATIO = 0.005
MIN_UNIT_PRICE = 0.01


@dataclass
class AskOrder:
    player: str
    item_type: str
    quantity: int
    min_price: float
    buyout_price: float
    expiry: int
    system: str
    location: str

    def __lt__(self, other):
        if not isinstance(other, AskOrder):
            return NotImplemented
        if self.buyout_price == other.buyout_price:
            return self.expiry < other.expiry
        return self.buyout_price < other.buyout_price


@dataclass
class BidOrder:
    player: str
    item_type: str
    quantity: int
    price: float
    expiry: int
    system: str
    location: str

    def __lt__(self, other):
        if not isinstance(other, BidOrder):
            return NotImplemented
        if self.price == other.price:
            return self.expiry < other.expiry
        return self.price > other.price


@dataclass
class Transaction:
    item_type: str
    quantity: int
    price: float
    buyer: str
    seller: str
    turn: int
    system: str
    location: str


class Marketplace(Building, Investable):
    def __init__(self):
        Building.__init__(self)
        Investable.__init__(self)
        self.name = f"Marketplace {uuid.uuid4().hex}"
        self.inventory = defaultdict(int)
        self.wallet = defaultdict(float)
        self.inventory_estimate = defaultdict(float)
        self.ask_orders = defaultdict(list)
        self.bid_orders = defaultdict(list)

    def place_bid_order(self, player, item_type, quantity, price):
        expiry = time_keeper.turn + NUM_TURN_BID_ORDER_EXPIRY
        cost = quantity * price
        service_fee = (
            cost * BASE_SERVICE_FEE_RATIO * max(1 - player.skills["trading"] * 0.001, 0)
        )
        if player.wallet >= cost + service_fee:
            player.spend(cost + service_fee)
            bid_order = BidOrder(
                player.name,
                item_type,
                quantity,
                price,
                expiry,
                player.current_system.name,
                player.current_location.name,
            )
            insort(self.bid_orders[item_type], bid_order)
            self.wallet[player.name] += cost
            self._distribute_earnings(service_fee)
            return True
        else:
            return False

    def place_ask_order(self, player, item_type, quantity, min_price, buyout_price):
        expiry = time_keeper.turn + NUM_TURN_ASK_ORDER_EXPIRY
        if player.current_location.storage.get_item(player.name, item_type) >= quantity:
            player.current_location.storage.remove_item(
                player.name, item_type, quantity
            )
            ask_order = AskOrder(
                player.name,
                item_type,
                quantity,
                min_price,
                buyout_price,
                expiry,
                player.current_system.name,
                player.current_location.name,
            )
            insort(self.ask_orders[item_type], ask_order)
            self.inventory[item_type] += quantity
            base_price = self._get_base_price(item_type)
            self.inventory_estimate[player.name] += quantity * base_price
            return True
        else:
            return False

    def match_orders(self):
        for item_type, bid_orders in self.bid_orders.items():
            ask_orders = self.ask_orders[item_type]
            for bid_order in bid_orders:
                for ask_order in ask_orders:
                    if bid_order.price >= ask_order.buyout_price:
                        trade_quantity = min(bid_order.quantity, ask_order.quantity)
                        trade_price = min(bid_order.price, ask_order.buyout_price)

                        self.execute_order(
                            bid_order, ask_order, trade_quantity, trade_price
                        )

                        if ask_order.quantity == 0:
                            ask_orders.remove(ask_order)
                        if bid_order.quantity == 0:
                            break
                if bid_order.quantity == 0:
                    bid_orders.remove(bid_order)

    def execute_order(self, bid_order, ask_order, quantity: int, price: float):
        bid_order.quantity -= quantity
        ask_order.quantity -= quantity

        buyer = player_manager.get_player(bid_order.player)
        seller = player_manager.get_player(ask_order.player)

        # delivery
        item_type = bid_order.item_type
        storage = location_map.get_location(bid_order.location).storage
        storage.add_item(bid_order.player, item_type, quantity)
        self.inventory[item_type] -= quantity

        # sales revenue
        revenue = quantity * price
        seller.earn(revenue)
        service_fee = (
            revenue
            * BASE_SERVICE_FEE_RATIO
            * max(1 - seller.skills["trading"] * 0.001, 0)
        )
        seller.spend(service_fee)
        self._distribute_earnings(service_fee)

        # refund
        refund = quantity * max(bid_order.price - price, 0)
        buyer.unspend(refund)

        # reserve release
        self.wallet[buyer.name] -= revenue + refund
        base_price = self._get_base_price(item_type)
        self.inventory_estimate[seller.name] -= quantity * base_price

        transaction = Transaction(
            bid_order.item_type,
            quantity,
            price,
            bid_order.player,
            ask_order.player,
            time_keeper.turn,
            bid_order.system,
            bid_order.location,
        )
        economy.push_transaction(transaction)

        # skill up
        for p in [buyer, seller]:
            p.transaction_completed += 1
            p.skills["trading"] = (
                int(math.log(p.transaction_completed) / math.log(math.sqrt(2)))
                if p.transaction_completed > 0
                else 0
            )

        logger.debug(
            f"Transaction completed for {item_type}: {quantity}@{price} between {bid_order.player} and {ask_order.player}"
        )

    def cancel_bid_order(self, bid_order):
        buyer = player_manager.get_player(bid_order.player)
        refund = bid_order.quantity * bid_order.price
        buyer.unspend(refund)
        self.wallet[buyer.name] -= refund  # reserve release

    def cancel_ask_order(self, ask_order):
        storage = location_map.get_location(ask_order.location).storage
        seller_name = ask_order.player
        item_type = ask_order.item_type
        quantity = ask_order.quantity
        storage.add_item(seller_name, item_type, quantity)
        self.inventory[item_type] -= quantity
        base_price = self._get_base_price(item_type)
        self.inventory_estimate[seller_name] -= quantity * base_price  # reserve release

    def clean_up(self):
        for item_type, ask_orders in self.ask_orders.items():
            self.ask_orders[item_type] = [
                ask_order
                for ask_order in ask_orders
                if ask_order.expiry > time_keeper.turn
            ]
            expired_ask_orders = [
                ask_order
                for ask_order in ask_orders
                if ask_order.expiry <= time_keeper.turn
            ]
            for ask_order in expired_ask_orders:
                self.match_expired_ask_order(item_type, ask_order)
                self.cancel_ask_order(ask_order)

        for item_type, bid_orders in self.bid_orders.items():
            self.bid_orders[item_type] = [
                bid_order
                for bid_order in bid_orders
                if bid_order.expiry > time_keeper.turn
            ]
            expired_bid_orders = [
                bid_order
                for bid_order in bid_orders
                if bid_order.expiry <= time_keeper.turn
            ]
            for bid_order in expired_bid_orders:
                self.cancel_bid_order(bid_order)

    def match_expired_ask_order(self, item_type, ask_order):
        bid_orders = self.bid_orders[item_type]
        for bid_order in bid_orders:
            if bid_order.price >= ask_order.min_price:
                trade_quantity = min(bid_order.quantity, ask_order.quantity)
                trade_price = max(bid_order.price, ask_order.min_price)

                self.execute_order(bid_order, ask_order, trade_quantity, trade_price)

                if ask_order.quantity == 0:
                    break
                if bid_order.quantity == 0:
                    bid_orders.remove(bid_order)

    def _get_base_price(self, item_type):
        material = material_manager.get_material(item_type)
        if material:
            base_price = material_manager.guess_base_price(
                material.rarity
            )
        else:
            spaceship_info = spaceship_manager.get_spaceship(item_type)
            if spaceship_info:
                base_price = spaceship_info.base_price
            else:
                logger.error(f"Missing price info: {item_type}")
                base_price = MIN_UNIT_PRICE
        return base_price

    def reset(self):
        self._hull = self._max_hull
        self._cooldown = 10000
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

    def debug_print(self):
        logger.info("Marketplace:")
        logger.info("Ask Orders:")
        for _, ask_orders in self.ask_orders.items():
            for ask_order in ask_orders:
                logger.info(ask_order)
        logger.info("Bid Orders:")
        for _, bid_orders in self.bid_orders.items():
            for bid_order in bid_orders:
                logger.info(bid_order)

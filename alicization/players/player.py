# players/player.py

from collections import defaultdict, deque
import logging

from .enums.control import Control
from .enums.goal import Goal
from .policies.ai_action import (
    choose_action_index_symbolic_ai,
    choose_action_index_neural_ai,
    choose_action_index_random_walk_ai,
    perform_action,
    get_full_state,
    get_reduced_state,
    calculate_reward,
)
from .actions.spaceship_piloting import (
    pilot,
)
from .util import (
    EMAData,
    calculate_net_worth,
    calculate_roi,
    calculate_score,
    calculate_ema_ratio,
)
from ..managers.time_keeper import TimeKeeper
from ..managers.player_manager import PlayerManager

logger = logging.getLogger(__name__)

time_keeper = TimeKeeper()
player_manager = PlayerManager()


DEFAULT_RARITY = 1
DEFAULT_VOLUME = 10
DEFAULT_SPACESHIP_COST = 1
NUM_RESPAWN_IDLE_TURN = 10
EARNING_MEMORY = 10000
PRODUCTION_MEMORY = 10000


class Player:
    def __init__(
        self,
        name: str,
        control: Control = Control.HUMAN,
        goal: Goal = None,
        willingness: int = 1,
        memory: int = 2,
    ):
        self.name = name
        self.control = control
        self.wallet = 0
        self.turns_until_idle = 0
        self.skills = defaultdict(int)
        self.goal = goal
        self.willingness = willingness
        self.memory = memory
        self.state_memory = None
        self.learning_agent = None
        self.last_action_index = 0
        self.action_history = defaultdict(int)
        self.death = 0
        self.kill = 0
        self.destroy = 0
        self.build = 0
        self.mined = 0
        self.total_damage = 0
        self.total_investment = 0
        self.profit_collected = 0
        self.roi = 0
        self.distance_traveled = 0
        self.mission_completed = 0
        self.salvage_completed = 0
        self.mining_completed = 0
        self.transaction_completed = 0
        self.net_worth = 0
        self.score = 0
        self.last_killed_by = None
        self.affordability = 1
        self.earning_history = deque(maxlen=EARNING_MEMORY)
        self.turn_earning = 0
        self.long_earning_ema = EMAData(period=EARNING_MEMORY)
        self.short_earning_ema = EMAData(period=int(EARNING_MEMORY * 0.5))
        self.productivity = 1
        self.production_history = deque(maxlen=PRODUCTION_MEMORY)
        self.turn_production = 0
        self.long_production_ema = EMAData(period=EARNING_MEMORY)
        self.short_production_ema = EMAData(period=int(EARNING_MEMORY * 0.5))

    def born(self, universe) -> None:
        universe.add_player(self)
        home_system = universe.get_random_system_with_planet()
        home_system.add_player(self)
        home_system.empty_space.add_player(self)
        player_manager.update_home_system(self.name, home_system)
        pilot(self, "explorer")
        player_manager.add_player(self)

    def spend(self, money: float) -> None:
        self.wallet -= money
        universe = player_manager.get_universe(self.name)
        universe.total_spending += money

    def unspend(self, money: float) -> None:
        self.spend(-money)

    def earn(self, money: float) -> None:
        self.wallet += money
        self.turn_earning += money
        universe = player_manager.get_universe(self.name)
        universe.total_earning += money

    def die(self) -> None:
        current_system = player_manager.get_system(self.name)
        current_location = player_manager.get_location(self.name)
        home_system = player_manager.get_home_system(self.name)
        logger.warning(
            f"{self.name} died at {current_system.name} - {current_location.name}"
        )
        self.death += 1
        self.spend(DEFAULT_SPACESHIP_COST)
        current_system.remove_player(self)
        current_location.remove_player(self)
        home_system.add_player(self)
        home_system.empty_space.add_player(self)
        pilot(self, "explorer")
        self.turns_until_idle += NUM_RESPAWN_IDLE_TURN
        logger.warning(f"{self.name} respawned at {home_system.name}")

    def act(self) -> None:
        if self.control in [
            Control.NEURAL_AI,
            Control.SYMBOLIC_AI,
            Control.RANDOM_WALK_AI,
        ]:
            action_index = self._choose_action_index()
            if self.control == Control.NEURAL_AI:
                state_before_action = get_reduced_state(self)
            perform_action(self, action_index)
            self.health_check()
            self.update_stats()
            if self.control == Control.NEURAL_AI:
                self._update_memory_and_learn(state_before_action, action_index)
        else:
            pass

    def _choose_action_index(self):
        if self.turns_until_idle <= 0:
            if self.control == Control.NEURAL_AI:
                return choose_action_index_neural_ai(self)
            elif self.control == Control.SYMBOLIC_AI:
                return choose_action_index_symbolic_ai(self)
            else:
                return choose_action_index_random_walk_ai()
        else:
            return self.last_action_index

    def health_check(self) -> None:
        spaceship = player_manager.get_spaceship(self.name)
        spaceship.health_check()

    def update_stats(self) -> None:
        universe = player_manager.get_universe(self.name)
        self.net_worth = calculate_net_worth(self, universe)
        self.roi = calculate_roi(self)
        self.score = calculate_score(self)

        self.earning_history.append(self.turn_earning)
        self.affordability = calculate_ema_ratio(
            self.earning_history,
            self.turn_earning,
            self.short_production_ema,
            self.long_production_ema,
        )
        self.turn_earning = 0

        self.production_history.append(self.turn_production)
        self.productivity = calculate_ema_ratio(
            self.production_history,
            self.turn_production,
            self.short_production_ema,
            self.long_production_ema,
        )
        self.turn_production = 0

        self.turns_until_idle = max(self.turns_until_idle - 1, 0)

    def _update_memory_and_learn(self, state_before_action, action_index: int):
        next_full_state = get_full_state(self)
        self.state_memory.append(next_full_state)

        reward = calculate_reward(self, self.goal, self.willingness, self.state_memory)
        next_state = get_reduced_state(self)

        self.learning_agent.memory.push(
            state_before_action, action_index, reward, next_state, False
        )
        self.learning_agent.learn()

    def to_json(self):
        current_system = player_manager.get_system(self.name)
        current_location = player_manager.get_location(self.name)
        spaceship = player_manager.get_spaceship(self.name)
        return {
            "name": self.name,
            "system": current_system.name,
            "location": current_location.name,
            "spaceshipClass": spaceship.ship_class,
            "spaceshipLevel": spaceship.level,
            "spaceshipCargoSize": spaceship.cargo_size,
            "wallet": self.wallet,
            "netWorth": self.net_worth,
            "score": self.score,
            "investment": self.total_investment,
            "profit": self.profit_collected,
            "roi": self.roi,
            "distance": self.distance_traveled,
            "mission": self.mission_completed,
            "damage": self.total_damage,
            "kill": self.kill,
            "death": self.death,
            "destroy": self.destroy,
            "build": self.build,
            "mined": self.mined,
            "transaction": self.transaction_completed,
            "affordability": self.affordability,
            "productivity": self.productivity,
            "actionHistory": self.action_history,
        }

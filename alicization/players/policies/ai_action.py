# players/policies/ai_action.py

import math
import random
from collections import deque
import logging

import numpy as np

from .action_map import ACTIONS, ACTION_INDEX_MAP
from .max_mission import max_mission_policy
from .max_kill import max_kill_policy
from .max_bounty import max_bounty_policy
from .max_build import max_build_policy
from .max_local_trade import max_local_trade_policy
from ..actions.movement import (
    move_to_random_planet,
    move_to_random_moon,
    move_to_random_asteroid_belt,
    move_to_random_stargate,
    move_to_random_debris,
    activate_stargate,
    can_move_asteroid_belt,
    can_move_debris,
    can_move_moon,
    can_move_planet,
    can_move_stargate,
    can_travel,
)
from ..actions.spaceship_piloting import (
    pilot,
    unload,
    load,
    can_load,
    can_pilot,
    can_unload,
)
from ..actions.material import (
    mine,
    salvage,
    can_mine,
    can_salvage,
)
from ..actions.missioning import (
    do_mission,
    can_mission,
)
from ..actions.spaceship_maintenance import (
    repair,
    upgrade,
    can_repair,
    can_upgrade,
)
from ..actions.manufacturing import (
    manufacture,
    can_manufacture,
)
from ..actions.trade import (
    buy_random_material,
    buy_random_material_random_margin,
    buy_spaceship_random_margin,
    sell_random_material,
    sell_random_material_random_margin,
    sell_spaceship_random_margin,
    can_buy,
    can_buy_material,
    can_sell_material,
    can_buy_spaceship,
    can_sell,
)
from ..actions.investment import (
    invest_random_amount,
    collect,
    can_collect,
    can_invest,
)
from ..actions.battle import (
    attack_player,
    bombard_random_building,
    place_bounty,
    can_attack,
    can_bombard,
    can_place_bounty,
)
from ..actions.extension import (
    set_home,
    explore,
    can_explore,
    can_set_home,
)
from ..util import (
    get_current_location_type,
    get_current_spaceship_type,
    get_next_system_info,
    get_factory_info,
    get_mission_info,
    calculate_distance_from_home,
)
from ..enums.action import Action
from ..enums.goal import Goal
from ...agents.dqn_agent import DQNAgent
from ...managers.time_keeper import TimeKeeper
from ...managers.player_manager import PlayerManager


logger = logging.getLogger(__name__)

time_keeper = TimeKeeper()
player_manager = PlayerManager()


def choose_action_index_symbolic_ai(player):
    goal_policy_map = {
        Goal.MAX_MISSION: max_mission_policy,
        Goal.MAX_KILL: max_kill_policy,
        Goal.MAX_BOUNTY: max_bounty_policy,
        Goal.MAX_BUILD: max_build_policy,
        Goal.MAX_LOCAL_TRADE: max_local_trade_policy,
    }
    policy = goal_policy_map.get(player.goal)
    if policy is not None:
        action_index_probs = policy(player)
        action_indexes, probs = zip(*action_index_probs)
        return random.choices(action_indexes, weights=probs, k=1)[0]
    else:
        return {
            0: ACTION_INDEX_MAP[Action.MOVE_PLANET.value],
            1: ACTION_INDEX_MAP[Action.INVEST_FACTORY.value],
            2: ACTION_INDEX_MAP[Action.COLLECT.value],
            3: ACTION_INDEX_MAP[Action.UNLOAD.value],
            4: ACTION_INDEX_MAP[Action.SELL.value],
            5: ACTION_INDEX_MAP[Action.MOVE_ASTEROID_BELT.value],
        }.get(time_keeper.turn % 10, ACTION_INDEX_MAP[Action.MINE.value])


def choose_action_index_neural_ai(player):
    state = get_reduced_state(player)
    return player.learning_agent.choose_action(state)


def choose_action_index_random_walk_ai():
    return random.randint(0, len(ACTIONS) - 1)


def perform_action(player, action_index):
    action = ACTIONS[action_index]

    if action == Action.IDLE.value:
        pass
    elif action == Action.MOVE_PLANET.value:
        move_to_random_planet(player)
    elif action == Action.MOVE_ASTEROID_BELT.value:
        move_to_random_asteroid_belt(player)
    elif action == Action.MOVE_MOON.value:
        move_to_random_moon(player)
    elif action == Action.MOVE_STARGATE.value:
        move_to_random_stargate(player)
    elif action == Action.MOVE_DEBRIS.value:
        move_to_random_debris(player)
    elif action == Action.TRAVEL.value:
        activate_stargate(player)
    elif action == Action.EXPLORE.value:
        explore(player)
    elif action == Action.MINE.value:
        mine(player)
    elif action == Action.UNLOAD.value:
        unload(player)
    elif action == Action.BUY.value:
        buy_random_material_random_margin(player)
    elif action == Action.SELL.value:
        sell_random_material_random_margin(player)
    elif action == Action.INVEST_FACTORY.value:
        invest_random_amount(player, "factory")
    elif action == Action.COLLECT.value:
        collect(player)
    elif action == Action.EASY_MISSION.value:
        do_mission(player, "easy")
    elif action == Action.REPAIR.value:
        repair(player)
    elif action == Action.UPGRADE.value:
        upgrade(player)
    elif action == Action.SALVAGE.value:
        salvage(player)
    elif action == Action.ATTACK_RANDOM.value:
        attack_player(player, "random")
    elif action == Action.ATTACK_STRONGEST.value:
        attack_player(player, "strong")
    elif action == Action.ATTACK_WEAKEST.value:
        attack_player(player, "weak")
    elif action == Action.BOMBARD.value:
        bombard_random_building(player)
    elif action == Action.SET_HOME.value:
        set_home(player)
    elif action == Action.BUY_CORVETTE.value:
        buy_spaceship_random_margin(player, "corvette")
    elif action == Action.SELL_CORVETTE.value:
        sell_spaceship_random_margin(player, "corvette")
    elif action == Action.BUILD_MINER.value:
        manufacture(player, "miner")
    elif action == Action.BUILD_CORVETTE.value:
        manufacture(player, "corvette")
    elif action == Action.BUILD_FRIGATE.value:
        manufacture(player, "frigate")
    elif action == Action.PILOT_MINER.value:
        pilot(player, "miner")
    elif action == Action.PILOT_CORVETTE.value:
        pilot(player, "corvette")
    elif action == Action.PILOT_FRIGATE.value:
        pilot(player, "frigate")
    elif action == Action.PLACE_BOUNTY.value:
        place_bounty(player)
    elif action == Action.INVEST_DRYDOCK.value:
        invest_random_amount(player, "drydock")
    elif action == Action.BUILD_DESTROYER.value:
        manufacture(player, "destroyer")
    elif action == Action.PILOT_DESTROYER.value:
        pilot(player, "destroyer")
    elif action == Action.BUILD_EXTRACTOR.value:
        manufacture(player, "extractor")
    elif action == Action.PILOT_EXTRACTOR.value:
        pilot(player, "extractor")
    elif action == Action.BUY_MINER.value:
        buy_spaceship_random_margin(player, "miner")
    elif action == Action.SELL_MINER.value:
        sell_spaceship_random_margin(player, "miner")
    elif action == Action.LOAD.value:
        load(player)
    elif action == Action.INVEST_MARKETPLACE.value:
        invest_random_amount(player, "marketplace")
    elif action == Action.SELL_FRIGATE.value:
        sell_spaceship_random_margin(player, "frigate")
    elif action == Action.SELL_DESTROYER.value:
        sell_spaceship_random_margin(player, "destroyer")
    elif action == Action.SELL_EXTRACTOR.value:
        sell_spaceship_random_margin(player, "extractor")
    elif action == Action.BUILD_COURIER.value:
        manufacture(player, "courier")
    elif action == Action.BUY_COURIER.value:
        buy_spaceship_random_margin(player, "courier")
    elif action == Action.SELL_COURIER.value:
        sell_spaceship_random_margin(player, "courier")
    elif action == Action.PILOT_COURIER.value:
        pilot(player, "courier")
    elif action == Action.BUY_FRIGATE.value:
        buy_spaceship_random_margin(player, "frigate")
    elif action == Action.BUY_DESTROYER.value:
        buy_spaceship_random_margin(player, "destroyer")
    elif action == Action.BUY_EXTRACTOR.value:
        buy_spaceship_random_margin(player, "extractor")
    elif action == Action.BUY_MATERIAL_LOW.value:
        buy_random_material(player, -0.5)
    elif action == Action.SELL_MATERIAL_HIGH.value:
        sell_random_material(player, -0.5, 0.5)
    else:
        logger.error(f"Not matching any action: {action}!!")
    player.action_history[ACTIONS[action_index]] += 1


def add_learning_agent(player):
    player.learning_agent = DQNAgent(
        actions=ACTIONS,
        input_size=77,  # Adjust based on the state representation
        hidden_sizes=[128, 256, 128],  # Adjust as needed
        output_size=len(ACTIONS),
        batch_size=128,
        # ... other hyperparameters for DQN agent ...
    )
    player.state_memory = deque(maxlen=player.memory)


def calculate_reward(player, goal, learning_rate, state_memory):
    if goal == Goal.MAX_WEALTH:
        net_worth_reward = (
            learning_rate
            * round(state_memory[-1]["net_worth"] - state_memory[0]["net_worth"], 2)
            if len(state_memory) > 1
            else 0
        )
        health_reward = calculate_health_reward(learning_rate, state_memory)
        death_penalty = calculate_death_penalty(learning_rate, state_memory)
        total_reward = net_worth_reward + health_reward - death_penalty - 0.0001
        logger.debug(f"{player.name} Total Reward: {total_reward}")
        return total_reward
    elif goal == Goal.MAX_KILL:
        kill_reward = (
            learning_rate * (state_memory[-1]["kill"] - state_memory[0]["kill"])
            if len(state_memory) > 1
            else 0
        )
        health_reward = calculate_health_reward(learning_rate, state_memory)
        death_penalty = calculate_death_penalty(learning_rate, state_memory)
        total_reward = kill_reward + health_reward - death_penalty - 0.0001
        logger.debug(f"{player.name} Total Reward: {total_reward}")
        return total_reward
    elif goal == Goal.MAX_DAMAGE:
        damage_reward = (
            learning_rate
            * round(
                state_memory[-1]["total_damage"] - state_memory[0]["total_damage"],
                2,
            )
            if len(state_memory) > 1
            else 0
        )
        health_reward = calculate_health_reward(learning_rate, state_memory)
        death_penalty = calculate_death_penalty(learning_rate, state_memory)
        total_reward = damage_reward + health_reward - death_penalty - 0.0001
        logger.debug(f"{player.name} Total Reward: {total_reward}")
        return total_reward
    elif goal == Goal.MAX_MISSION:
        mission_reward = (
            learning_rate
            * (
                state_memory[-1]["mission_completed"]
                - state_memory[0]["mission_completed"]
            )
            if len(state_memory) > 1
            else 0
        )
        health_reward = calculate_health_reward(learning_rate, state_memory)
        death_penalty = calculate_death_penalty(learning_rate, state_memory)
        total_reward = mission_reward + health_reward - death_penalty - 0.0001
        logger.debug(f"{player.name} Total Reward: {total_reward}")
        return total_reward
    elif goal == Goal.MAX_SCORE:
        score_reward = (
            learning_rate * (state_memory[-1]["score"] - state_memory[0]["score"])
            if len(state_memory) > 1
            else 0
        )
        health_reward = calculate_health_reward(learning_rate, state_memory)
        death_penalty = calculate_death_penalty(learning_rate, state_memory)
        total_reward = score_reward + health_reward - death_penalty - 0.0001
        logger.debug(f"{player.name} Total Reward: {total_reward}")
        return total_reward
    else:
        logger.debug("Random reward")
        return -0.0001


def calculate_death_penalty(learning_rate, state_memory):
    return (
        0.01 * learning_rate * (state_memory[-1]["death"] - state_memory[0]["death"])
        if len(state_memory) > 1
        else 0
    )


def calculate_health_reward(learning_rate, state_memory):
    return (
        0.0001
        * learning_rate
        * (state_memory[-1]["health"] - state_memory[0]["health"])
        if len(state_memory) > 1
        else 0
    )


def get_full_state(player):
    current_system = player_manager.get_system(player.name)
    current_location = player_manager.get_location(player.name)
    spaceship = player_manager.get_spaceship(player.name)
    home_system = player_manager.get_home_system(player.name)
    distance, next_stargate, next_planet, next_asteroid_belt, next_moon = (
        get_next_system_info(current_location)
    )
    factory_level = get_factory_info(current_location)
    mission_difficulty, mission_reward = get_mission_info(current_location)
    cargo_full = 1 if spaceship.is_cargo_full() else 0
    state = {
        "can_move_planet": can_move_planet(current_system),
        "can_move_asteroid_belt": can_move_asteroid_belt(current_system),
        "can_move_moon": can_move_moon(current_system),
        "can_move_stargate": can_move_stargate(current_system),
        "can_move_debris": can_move_debris(current_system),
        "can_travel": can_travel(current_location),
        "can_explore": can_explore(current_location),
        "can_mine": can_mine(current_location, spaceship),
        "can_unload": can_unload(current_location, spaceship),
        "can_buy": can_buy_material(player, current_location),
        "can_sell": can_sell_material(player, current_location),
        "can_invest_factory": can_invest(player, current_location, "factory"),
        "can_invest_drydock": can_invest(player, current_location, "drydock"),
        "can_invest_marketplace": can_invest(player, current_location, "marketplace"),
        "can_collect": can_collect(player, current_location),
        "can_mission": can_mission(current_location),
        "can_repair": can_repair(player, current_location, spaceship),
        "can_upgrade": can_upgrade(player, current_location, spaceship),
        "can_salvage": can_salvage(current_location, spaceship),
        "can_attack": can_attack(current_location, spaceship),
        "can_bombard": can_bombard(current_location, spaceship),
        "can_set_home": can_set_home(player, current_system, current_location),
        "can_buy_corvette": can_buy_spaceship(player, current_location),
        "can_sell_corvette": can_sell(player, current_location, "corvette", 1),
        "can_sell_frigate": can_sell(player, current_location, "frigate", 1),
        "can_sell_destroyer": can_sell(player, current_location, "destroyer", 1),
        "can_sell_miner": can_sell(player, current_location, "miner", 1),
        "can_sell_extractor": can_sell(player, current_location, "extractor", 1),
        "can_sell_courier": can_sell(player, current_location, "courier", 1),
        "can_build_miner": can_manufacture(player, current_location, "miner"),
        "can_build_corvette": can_manufacture(player, current_location, "corvette"),
        "can_build_frigate": can_manufacture(player, current_location, "frigate"),
        "can_build_destroyer": can_manufacture(player, current_location, "destroyer"),
        "can_build_extractor": can_manufacture(player, current_location, "extractor"),
        "can_build_courier": can_manufacture(player, current_location, "courier"),
        "can_pilot_miner": can_pilot(player, current_location, "miner"),
        "can_pilot_corvette": can_pilot(player, current_location, "corvette"),
        "can_pilot_frigate": can_pilot(player, current_location, "frigate"),
        "can_pilot_destroyer": can_pilot(player, current_location, "destroyer"),
        "can_pilot_extractor": can_pilot(player, current_location, "extractor"),
        "can_pilot_courier": can_pilot(player, current_location, "courier"),
        "can_place_bounty": can_place_bounty(player),
        "spaceship": get_current_spaceship_type(spaceship),
        "spaceship_level": spaceship.level,
        "weapon": spaceship.weapon,
        "shield": spaceship.shield,
        "armor": spaceship.armor,
        "hull": spaceship.hull,
        "strength": int(spaceship.weapon / 10),
        "health": int((spaceship.armor + spaceship.hull) / 10),
        "cargo_full": cargo_full,
        "stargate": len(current_system.stargates),
        "planet": len(current_system.planets),
        "asteroid_belt": len(current_system.asteroid_belts),
        "moon": len(current_system.moons),
        "debris": len(current_system.debrises),
        "location": get_current_location_type(current_location),
        "system_player": len(current_system.players),
        "location_player": len(current_location.players),
        "distance_from_home": int(
            calculate_distance_from_home(player, current_system, home_system) / 10
        ),
        "distance": distance,
        "next_stargate": next_stargate,
        "next_planet": next_planet,
        "next_asteroid_belt": next_asteroid_belt,
        "next_moon": next_moon,
        "factory_level": factory_level,
        "mission_difficulty": mission_difficulty,
        "mission_reward": mission_reward,
        "wallet": (
            round(int(math.log(player.wallet) * 100) / 100, 2)
            if player.wallet > 0
            else 0
        ),
        "net_worth": (
            round(int(math.log(player.net_worth) * 100) / 100, 2)
            if player.net_worth > 0
            else 0
        ),
        "ship_cargo_size": (
            round(int(math.log(spaceship.cargo_size) * 100) / 100, 2)
            if spaceship.cargo_size > 0
            else 0
        ),
        "total_investment": (
            round(int(math.log(player.total_investment) * 100) / 100, 2)
            if player.total_investment > 0
            else 0
        ),
        "rich": int(math.log10(player.wallet) if player.wallet > 0 else 0),
        "ship_fat": int(
            math.log10(spaceship.cargo_size) if spaceship.cargo_size > 0 else 0
        ),
        "distance_traveled": player.distance_traveled,
        "mission_completed": player.mission_completed,
        "total_damage": (
            round(int(math.log(player.total_damage) * 100) / 100, 2)
            if player.total_damage > 0
            else 0
        ),
        "kill": player.kill,
        "destroy": player.destroy,
        "death": player.death,
        "score": player.score,
    }
    return state


def get_reduced_state(player):
    state_dict = get_full_state(player)
    state_dict.pop("weapon")
    state_dict.pop("shield")
    state_dict.pop("armor")
    state_dict.pop("hull")
    state_dict.pop("score")
    state_dict.pop("wallet")
    state_dict.pop("net_worth")
    state_dict.pop("ship_cargo_size")
    state_dict.pop("total_investment")
    state_dict.pop("distance_traveled")
    state_dict.pop("mission_completed")
    state_dict.pop("total_damage")
    state_dict.pop("kill")
    state_dict.pop("destroy")
    state_dict.pop("death")
    net_worth_gain = (
        round(
            player.state_memory[-1]["net_worth"] - player.state_memory[0]["net_worth"],
            2,
        )
        if len(player.state_memory) > 1
        else 0
    )
    ship_cargo_size_gain = (
        round(
            player.state_memory[-1]["ship_cargo_size"]
            - player.state_memory[0]["ship_cargo_size"],
            2,
        )
        if len(player.state_memory) > 1
        else 0
    )
    investment_gain = (
        round(
            player.state_memory[-1]["total_investment"]
            - player.state_memory[0]["total_investment"],
            2,
        )
        if len(player.state_memory) > 1
        else 0
    )
    distance_gain = (
        player.state_memory[-1]["distance_traveled"]
        - player.state_memory[0]["distance_traveled"]
        if len(player.state_memory) > 1
        else 0
    )
    mission_gain = (
        player.state_memory[-1]["mission_completed"]
        - player.state_memory[0]["mission_completed"]
        if len(player.state_memory) > 1
        else 0
    )
    damage_gain = (
        round(
            player.state_memory[-1]["total_damage"]
            - player.state_memory[0]["total_damage"],
            2,
        )
        if len(player.state_memory) > 1
        else 0
    )
    kill_gain = (
        player.state_memory[-1]["kill"] - player.state_memory[0]["kill"]
        if len(player.state_memory) > 1
        else 0
    )
    destroy_gain = (
        player.state_memory[-1]["destroy"] - player.state_memory[0]["destroy"]
        if len(player.state_memory) > 1
        else 0
    )
    death_gain = (
        player.state_memory[-1]["death"] - player.state_memory[0]["death"]
        if len(player.state_memory) > 1
        else 0
    )
    health_gain = (
        player.state_memory[-1]["health"] - player.state_memory[0]["health"]
        if len(player.state_memory) > 1
        else 0
    )
    score_gain = (
        player.state_memory[-1]["score"] - player.state_memory[0]["score"]
        if len(player.state_memory) > 1
        else 0
    )
    state_dict["net_worth_gain"] = net_worth_gain
    state_dict["ship_cargo_size_gain"] = ship_cargo_size_gain
    state_dict["investment_gain"] = investment_gain
    state_dict["distance_gain"] = distance_gain
    state_dict["mission_gain"] = mission_gain
    state_dict["damage_gain"] = damage_gain
    state_dict["kill_gain"] = kill_gain
    state_dict["destroy_gain"] = destroy_gain
    state_dict["death_gain"] = death_gain
    state_dict["health_gain"] = health_gain
    state_dict["score_gain"] = score_gain

    state = np.array(list(state_dict.values()))

    return state

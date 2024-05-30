# action.py

from enum import Enum


class Action(Enum):
    IDLE = "idle"  # 0
    MOVE_PLANET = "move_planet"  # 1
    MOVE_ASTEROID_BELT = "move_asteroid_belt"  # 2
    MOVE_MOON = "move_moon"  # 3
    MOVE_STARGATE = "move_stargate"  # 4
    MOVE_DEBRIS = "move_debris"  # 5
    TRAVEL = "travel"  # 6
    EXPLORE = "explore"  # 7
    MINE = "mine"  # 8
    UNLOAD = "unload"  # 9
    BUY = "buy"  # 10
    SELL = "sell"  # 11
    INVEST_FACTORY = "invest_factory"  # 12
    COLLECT = "collect"  # 13
    EASY_MISSION = "easy_mission"  # 14
    REPAIR = "repair"  # 15
    UPGRADE = "upgrade"  # 16
    SALVAGE = "salvage"  # 17
    ATTACK_RANDOM = "attack_random"  # 18
    ATTACK_STRONGEST = "attack_strongest"  # 19
    ATTACK_WEAKEST = "attack_weakest"  # 20
    BOMBARD = "bombard"  # 21
    SET_HOME = "set_home"  # 22
    BUY_WARSHIP = "buy_warship"  # 23
    SELL_WARSHIP = "sell_warship"  # 24
    BUILD_MINER = "build_miner"  # 25
    BUILD_CORVETTE = "build_corvette"  # 26
    BUILD_FRIGATE = "build_frigate"  # 27
    PILOT_MINER = "pilot_miner"  # 28
    PILOT_CORVETTE = "pilot_corvette"  # 29
    PILOT_FRIGATE = "pilot_frigate"  # 30
    PLACE_BOUNTY = "place_bounty"  # 31
    INVEST_DRYDOCK = "invest_drydock"  # 32
    BUILD_DESTROYER = "build_destroyer"  # 33
    PILOT_DESTROYER = "pilot_destroyer"  # 34
    BUILD_EXTRACTOR = "build_extractor"  # 35
    PILOT_EXTRACTOR = "pilot_extractor"  # 36
    BUY_MINING_SPACESHIP = "buy_mining_spaceship"  # 37
    SELL_MINING_SPACESHIP = "sell_mining_spaceship"  # 38
    LOAD = "load"  # 39
    INVEST_MARKETPLACE = "invest_marketplace"  # 40

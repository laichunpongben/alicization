# mission_center.py

import csv
import uuid
import random
import math
from pathlib import Path
from enum import Enum
import logging

import numpy as np

from .building import Building
from ..managers.leaderboard import Leaderboard

logger = logging.getLogger(__name__)


leaderboard = Leaderboard()

MISSION_SUCCESS_BASE_DAMAGE = 50
MISSION_FAIL_BASE_DAMAGE = 100

NUM_BOMBARD_ROUND = 10
P_BOMBARD_HIT = 0.5
DESTROY_SCORE = 10000
BASE_MISSION_SCORE = 10
MAX_DAMAGE = 1e12
NUM_MISSION = 5


class MissionStatus(Enum):
    OPEN = 0
    COMPLETED = 1
    CANCELED = 2


class Mission:
    def __init__(self, description, difficulty, reward):
        self.description = description
        self.difficulty = difficulty
        self.reward = reward
        self.status = MissionStatus.OPEN


class MissionCenter(Building):
    def __init__(self, missions_file=None):
        Building.__init__(self)
        self.name = f"Mission Center {uuid.uuid4().hex}"
        self.missions = []
        if missions_file is None:
            self.missions_file = (
                Path(__file__).resolve().parent.parent / "data" / "missions.csv"
            )
        else:
            self.missions_file = missions_file
        self.load_missions_from_csv(self.missions_file)

    def load_missions_from_csv(self, missions_file, count=NUM_MISSION):
        try:
            with open(missions_file, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                all_missions = [
                    (row["description"], int(row["difficulty"]), int(row["reward"]))
                    for row in reader
                ]
                random.shuffle(all_missions)
                for description, difficulty, reward in all_missions[:count]:
                    self.add_mission(description, difficulty, reward)
        except FileNotFoundError:
            logger.error(f"Mission file '{missions_file}' not found.")
        except Exception as e:
            logger.error(f"Error loading missions: {e}")

    def add_mission(self, description, difficulty, reward):
        mission = Mission(description, difficulty, reward)
        self.missions.append(mission)

    def get_available_missions(self):
        return [
            mission for mission in self.missions if mission.status == MissionStatus.OPEN
        ]

    def has_missions(self):
        return (
            len(
                [
                    mission
                    for mission in self.missions
                    if mission.status == MissionStatus.OPEN
                ]
            )
            > 0
        )

    def get_best_reward_mission(self):
        available_missions = self.get_available_missions()
        if not available_missions:
            return None
        best_mission = max(available_missions, key=lambda mission: mission.reward)
        return best_mission

    def apply_mission_random(self):
        if self.cooldown <= 0:
            available_missions = self.get_available_missions()
            if len(available_missions) > 0:
                return random.choice(available_missions)
        return None

    def apply_mission_easiet(self):
        if self.cooldown <= 0:
            available_missions = self.get_available_missions()
            if len(available_missions) > 0:
                available_missions.sort(key=lambda m: m.difficulty)
                return available_missions[0]
        return None

    def apply_mission_hardest(self):
        if self.cooldown <= 0:
            available_missions = self.get_available_missions()
            if len(available_missions) > 0:
                available_missions.sort(key=lambda m: m.difficulty, reverse=True)
                return available_missions[0]
        return None

    def do_mission(self, player, mission):
        if self.cooldown > 0:
            return 0

        if mission in self.missions and mission.status == MissionStatus.OPEN:
            if mission.difficulty > 0 and player.spaceship.weapon <= 0:
                return 0

            player.turns_until_idle += mission.difficulty
            skill_level = player.skills["missioning"]
            if self.mission_success(mission.difficulty, skill_level):
                damage = min(
                    np.random.poisson(mission.difficulty * MISSION_SUCCESS_BASE_DAMAGE),
                    MAX_DAMAGE,
                )
                player.spaceship.take_damage(damage)
                if player.spaceship.destroyed:
                    player.current_system.make_debris(player.spaceship.cargo_hold)
                    player.die()
                    leaderboard.log_achievement(player.name, "death", 1)
                    result = 0
                else:
                    mission.status = MissionStatus.COMPLETED
                    player.wallet += mission.reward
                    player.mission_completed += 1
                    player.universe.total_mission_completed += 1
                    player.skills["missioning"] = (
                        int(math.log(player.mission_completed) / math.log(math.sqrt(2)))
                        if player.mission_completed > 0
                        else 0
                    )
                    result = mission.reward
                    if mission.difficulty >= 10:
                        leaderboard.log_achievement(
                            player.name,
                            "mission",
                            (mission.difficulty - 9) * BASE_MISSION_SCORE,
                        )
                        logger.warning(
                            f"{player.name} completed MISSION LV {mission.difficulty}"
                        )
            else:
                damage = min(
                    np.random.poisson(mission.difficulty * MISSION_FAIL_BASE_DAMAGE),
                    MAX_DAMAGE,
                )
                player.spaceship.take_damage(damage)
                if player.spaceship.destroyed:
                    player.current_system.make_debris(player.spaceship.cargo_hold)
                    player.die()
                    leaderboard.log_achievement(player.name, "death", 1)
                result = 0

            return result
        else:
            return 0

    def mission_success(self, difficulty, skill_level):
        success_chance = max(
            0, min(0.75 * (1 + skill_level * 0.001), 0.9999) ** difficulty
        )
        return random.random() < success_chance

    def respawn_missions(self):
        mission_count = len(self.get_available_missions())
        if mission_count < NUM_MISSION and random.random() < 0.1:
            self.load_missions_from_csv(
                self.missions_file, count=NUM_MISSION - mission_count
            )
            logger.debug(f"Missions respawned in {self.name}")
        else:
            if mission_count > 0 and random.random() < 0.01:
                missions = self.get_available_missions()
                mission_to_cancel = random.choice(missions)
                mission_to_cancel.status = MissionStatus.CANCELED
                self.load_missions_from_csv(self.missions_file, count=1)
                logger.debug(f"Mission {mission_to_cancel} replaced in {self.name}")

    def clean_up(self):
        self.missions = [mission for mission in self.missions if mission.status == MissionStatus.OPEN]
        logger.debug(f"Cleaned up missions in {self.name}")

    def reset(self):
        self._hull = self._max_hull
        self._cooldown = 10000
        logger.warning(
            f"{self.name} exploded and has a {self._cooldown} turns cooldown!"
        )

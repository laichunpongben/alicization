# leaderboard.py

import heapq
from collections import defaultdict


class Leaderboard:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Leaderboard, cls).__new__(cls)
            cls.__instance.achievements = {}
        return cls.__instance

    def log_achievement(self, player_name, achievement, value, overwrite=False):
        if achievement not in self.achievements:
            self.achievements[achievement] = defaultdict(float)
        if overwrite:
            self.achievements[achievement][player_name] = value
        else:
            self.achievements[achievement][player_name] += value

    def get_achievement_score(self, player_name, achievement):
        if achievement in self.achievements:
            return self.achievements[achievement][player_name]
        else:
            return 0

    def get_top_leaders(self, achievement, top_n=10):
        if achievement not in self.achievements:
            return []

        leaders = heapq.nlargest(
            top_n, self.achievements[achievement].items(), key=lambda item: item[1]
        )
        return leaders
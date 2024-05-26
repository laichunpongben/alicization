# game.py

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from alicization.enums.control import Control
from alicization.enums.goal import Goal
from alicization.player import Player
from alicization.universe import Universe

logger = logging.getLogger(__name__)


NUM_TURN_PER_GAME_STATE_UPDATE = 100
NUM_TURN_PER_SLEEP = 100
SLEEP_SEC = 0.1


class Game:
    def __init__(self):
        self.turn = 1
        self.universe = Universe(initial_systems=5)
        self.players = {
            "randomwalk1": Player(
                "Random Walker", self.universe, control=Control.RANDOM_WALK_AI
            ),
            "symbolic_default1": Player(
                "Slave", self.universe, control=Control.SYMBOLIC_AI
            ),
            "symbolic_maxkill1": Player(
                "Clone Army 1",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill2": Player(
                "Clone Army 2",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill3": Player(
                "Clone Army 3",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill4": Player(
                "Clone Army 4",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill5": Player(
                "Clone Army 5",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill6": Player(
                "Clone Army 6",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill7": Player(
                "Clone Army 7",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill8": Player(
                "Clone Army 8",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill9": Player(
                "Clone Army 9",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxkill10": Player(
                "Clone Army 10",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_KILL,
            ),
            "symbolic_maxbounty1": Player(
                "Bounty Hunter 1",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BOUNTY,
            ),
            "symbolic_maxbounty2": Player(
                "Bounty Hunter 2",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BOUNTY,
            ),
            "symbolic_maxbounty3": Player(
                "Bounty Hunter 3",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BOUNTY,
            ),
            "symbolic_maxmission1": Player(
                "Task Force 1",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission2": Player(
                "Task Force 2",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission3": Player(
                "Task Force 3",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission4": Player(
                "Task Force 4",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission5": Player(
                "Task Force 5",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission6": Player(
                "Task Force 6",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission7": Player(
                "Task Force 7",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission8": Player(
                "Task Force 8",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission9": Player(
                "Task Force 9",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxmission10": Player(
                "Task Force 10",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_MISSION,
            ),
            "symbolic_maxbuild1": Player(
                "Miner 1",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild2": Player(
                "Miner 2",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild3": Player(
                "Miner 3",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild4": Player(
                "Miner 4",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild5": Player(
                "Miner 5",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild6": Player(
                "Miner 6",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild7": Player(
                "Miner 7",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild8": Player(
                "Miner 8",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild9": Player(
                "Miner 9",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild10": Player(
                "Miner 10",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild11": Player(
                "Miner 11",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild12": Player(
                "Miner 12",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild13": Player(
                "Miner 13",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild14": Player(
                "Miner 14",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild15": Player(
                "Miner 15",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild16": Player(
                "Miner 16",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild17": Player(
                "Miner 17",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild18": Player(
                "Miner 18",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild19": Player(
                "Miner 19",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
            "symbolic_maxbuild20": Player(
                "Miner 20",
                self.universe,
                control=Control.SYMBOLIC_AI,
                goal=Goal.MAX_BUILD,
            ),
        }
        self.game_state_queue = asyncio.Queue()

    async def update_game_state(self, websocket: WebSocket):
        try:
            player_data = [player.to_json() for player in self.players.values()]
            await websocket.send_json(
                {
                    "turn": self.turn,
                    "universe": self.universe.to_json(),
                    "players": player_data,
                }
            )
        except WebSocketDisconnect:
            print(f"Connection closed: {websocket}")

    async def simulate_turn(self):
        logger.debug(f"Starting Turn {self.turn}.")

        for player in self.players.values():
            if (
                player.control == Control.RANDOM_WALK_AI
                or player.control == Control.SYMBOLIC_AI
                or player.control == Control.NEURAL_AI
            ):
                player.act()

        self.universe.health_check()

        self.turn += 1

        if self.turn % NUM_TURN_PER_GAME_STATE_UPDATE == 0:
            await self.game_state_queue.put(self)

    async def simulate_game(self):
        logger.info("Simulate Game!")
        try:
            while True:
                await self.simulate_turn()

                if self.turn % NUM_TURN_PER_SLEEP == 0:
                    await asyncio.sleep(SLEEP_SEC)

        except asyncio.CancelledError:
            print("Game simulation stopped.")

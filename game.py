# game.py

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from alicization.enums.control import Control
from alicization.enums.goal import Goal
from alicization.universe import Universe
from alicization.players.player import Player
from alicization.players.policies.ai_action import (
    add_learning_agent,
)

logger = logging.getLogger(__name__)


NUM_TURN_PER_GAME_STATE_UPDATE = 100
NUM_TURN_PER_SLEEP = 100
SLEEP_SEC = 0.1


class Game:
    def __init__(self):
        self._turn = 1
        self._universe = Universe(initial_systems=5)
        self._players = [
            Player("Random Walker", control=Control.RANDOM_WALK_AI),
            Player("Slave", control=Control.SYMBOLIC_AI),
            Player("Clone Army 1", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 2", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 3", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 4", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 5", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 6", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 7", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 8", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 9", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player("Clone Army 10", control=Control.SYMBOLIC_AI, goal=Goal.MAX_KILL),
            Player(
                "Bounty Hunter 1", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BOUNTY
            ),
            Player(
                "Bounty Hunter 2", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BOUNTY
            ),
            Player(
                "Bounty Hunter 3", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BOUNTY
            ),
            Player("Task Force 1", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 2", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 3", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 4", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 5", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 6", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 7", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 8", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 9", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Task Force 10", control=Control.SYMBOLIC_AI, goal=Goal.MAX_MISSION),
            Player("Miner 1", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 2", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 3", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 4", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 5", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 6", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 7", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 8", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 9", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 10", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 11", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 12", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 13", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 14", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 15", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 16", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 17", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 18", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 19", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Miner 20", control=Control.SYMBOLIC_AI, goal=Goal.MAX_BUILD),
            Player("Trader 1", control=Control.SYMBOLIC_AI, goal=Goal.MAX_LOCAL_TRADE),
            Player("Achiever", control=Control.NEURAL_AI, goal=Goal.MAX_SCORE),
        ]
        self.game_state_queue = asyncio.Queue()

        for player in self._players:
            player.born(self._universe)
            if player.control == Control.NEURAL_AI:
                add_learning_agent(player)

    async def update_game_state(self, websocket: WebSocket):
        try:
            player_data = [player.to_json() for player in self._players]
            await websocket.send_json(
                {
                    "turn": self._turn,
                    "universe": self._universe.to_json(),
                    "players": player_data,
                }
            )
        except WebSocketDisconnect:
            print(f"Connection closed: {websocket}")

    async def simulate_turn(self):
        logger.debug(f"Starting Turn {self._turn}.")

        for player in self._players:
            if (
                player.control == Control.RANDOM_WALK_AI
                or player.control == Control.SYMBOLIC_AI
                or player.control == Control.NEURAL_AI
            ):
                player.act()

        self._universe.health_check()
        self._turn += 1

        if self._turn % NUM_TURN_PER_GAME_STATE_UPDATE == 0:
            await self.game_state_queue.put(self)

    async def simulate_game(self):
        logger.info("Simulate Game!")
        try:
            while True:
                await self.simulate_turn()

                if self._turn % NUM_TURN_PER_SLEEP == 0:
                    await asyncio.sleep(SLEEP_SEC)

        except asyncio.CancelledError:
            print("Game simulation stopped.")

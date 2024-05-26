# app.py

import asyncio
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from game import Game

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    game = Game()
    app.state.game = game
    asyncio.create_task(game.simulate_game())
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    game = app.state.game
    await websocket.accept()
    logger.info(f"WebSocket connection established: {websocket}")

    try:
        await game.update_game_state(websocket)
        while True:
            game = await game.game_state_queue.get()
            await game.update_game_state(websocket)
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed: {websocket}")
    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {e}")


if __name__ == "__main__":
    import os
    import uvicorn

    log_conf_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "log_conf.yaml"
    )
    uvicorn.run(app, host="127.0.0.1", port=8000, log_config=log_conf_path)

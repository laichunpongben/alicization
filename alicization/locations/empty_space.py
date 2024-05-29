# empty_space.py

import uuid
import logging

from .location import Location

logger = logging.getLogger(__name__)


class EmptySpace(Location):
    def __init__(self):
        super().__init__()
        self.name = f"Empty Space {uuid.uuid4().hex}"
        
    def debug_print(self):
        logger.info(f"Empty Space: {self.name}")
        logger.info(f"Players: {self.players}")

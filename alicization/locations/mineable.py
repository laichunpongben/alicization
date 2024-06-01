# locations/mineable.py

from abc import ABC, abstractmethod


class Mineable(ABC):
    """Interface for mineable objects. This defines the basic methods
    for objects that can be mined, like planets, asteroids, etc.
    """

    @abstractmethod
    def mine(self):
        pass
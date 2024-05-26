# mineable.py

from abc import ABC, abstractmethod


class Mineable(ABC):
    """Interface for mineable objects. This defines the basic methods
    for objects that can be mined, like planets, asteroids, etc.
    """

    @abstractmethod
    def mine(self):
        """Mines a random resource from the object.

        Returns:
            A list containing a tuple of the mined resource and quantity.
            [(resource_name, amount)]
        """
        pass

    @abstractmethod
    def get_resources(self):
        """Returns a dictionary of resources and their quantities.

        Returns:
            dict: A dictionary representing the object's resources.
        """
        pass

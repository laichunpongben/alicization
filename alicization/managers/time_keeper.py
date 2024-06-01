# time_keeper.py


class TimeKeeper:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TimeKeeper, cls).__new__(cls)
            cls.__instance._turn = 1
        return cls.__instance

    @property
    def turn(self):
        return self._turn

    def tick(self) -> None:
        self._turn += 1

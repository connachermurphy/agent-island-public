import logging
from typing import Callable, List


class Round:
    def __init__(self, logger: logging.Logger, phases: List[Callable[[], None]]):
        self.logger = logger
        self.phases = phases

    def play(self):
        self.logger.info("Starting round from the Round.play() method...")

        for phase in self.phases:
            phase()

        # TODO: manage History

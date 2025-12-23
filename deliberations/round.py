import logging
from dataclasses import dataclass
from typing import Callable, List

from history import History
from player import Player


@dataclass
class RoundContext:
    players: List[Player]
    logger: logging.Logger
    history: History
    round_index: int
    rules_prompt: str


class Round:
    def __init__(
        self, context: RoundContext, phases: List[Callable[[RoundContext], None]]
    ):
        self.context = context
        self.phases = phases

    def play(self):
        self.context.logger.info(f"Starting round {self.context.round_index}")

        player_ids = [player.config.player_id for player in self.context.players]
        self.context.history.start_round(
            round_index=self.context.round_index,
            players=player_ids,
        )

        self.context.history.narrate(
            round_index=self.context.round_index,
            heading="Narrator",
            content=f"Welcome to round {self.context.round_index}!",
            players=self.context.history.players,
        )

        for phase in self.phases:
            self.context.logger.info(f"Starting {phase.__name__}")
            phase(self.context)

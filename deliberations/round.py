import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from history import History
from player import Player


@dataclass
class RoundContext:
    round_index: int
    players: List[Player]
    logger: logging.Logger
    history: History
    rules_prompt: str
    vote_tally: dict[str, int] = field(default_factory=dict)
    eliminated_player: Optional[str] = None

    def player_ids(self) -> List[str]:
        return [player.config.player_id for player in self.players]


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
            player_ids=player_ids,
        )

        self.context.history.narrate(
            round_index=self.context.round_index,
            heading="Narrator",
            content=f"Welcome to round {self.context.round_index}!",
            player_ids=player_ids,
        )

        for phase in self.phases:
            self.context.logger.info(f"Starting {phase.__name__}")
            phase(self.context)

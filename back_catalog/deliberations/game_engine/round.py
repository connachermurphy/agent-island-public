import logging
from dataclasses import dataclass, field
from typing import Any, Callable, List

from .history import History
from .player import Player


@dataclass
class RoundContext:
    """
    Context for a round of the game

    Args:
        round_index: The index of the round
        final_round: Whether this is the final round
        players: List of Player objects
        active_player_ids: List of active player IDs
        eliminated_player_ids: List of eliminated player IDs
        logger: Logger for the round
        history: History for the round
        rules_prompt: Prompt with the rules of the game
        votes: Dictionary of votes for the round
    """

    round_index: int
    final_round: bool
    players: List[Player]
    active_player_ids: List[str]
    eliminated_player_ids: List[str]
    logger: logging.Logger
    history: History
    rules_prompt: str
    votes: dict[str, Any] = field(default_factory=dict)


class Round:
    def __init__(
        self, context: RoundContext, phases: List[Callable[[RoundContext], None]]
    ):
        """
        Initialize the Round class

        Args:
            context: The round context
            phases: List of phase functions
        """
        self.context = context
        self.phases = phases

    def play(self):
        """
        Play a round of the game

        Args:
            None

        Returns:
            None
        """
        self.context.logger.info(f"Starting round {self.context.round_index}")

        all_player_ids = (
            self.context.active_player_ids + self.context.eliminated_player_ids
        )

        self.context.history.start_round(
            round_index=self.context.round_index,
            final_round=self.context.final_round,
            active_player_ids=self.context.active_player_ids,
            eliminated_player_ids=self.context.eliminated_player_ids,
        )

        self.context.history.narrate(
            round_index=self.context.round_index,
            heading="Narrator",
            content=f"Welcome to round {self.context.round_index}!",
            visibility=all_player_ids,
            active_visibility=all_player_ids.copy(),
        )

        for phase in self.phases:
            self.context.logger.info(f"Starting {phase.__name__}")
            phase(self.context)

        self.context.history.narrate(
            round_index=self.context.round_index,
            heading="Narrator",
            content=f"Round {self.context.round_index} complete!",
            visibility=all_player_ids,
            active_visibility=all_player_ids.copy(),
        )

        self.context.logger.info(f"Round {self.context.round_index} complete")

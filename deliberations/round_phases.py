import logging
from typing import Callable, Iterable

from player import Player


def phase_pitches(
    players: Iterable[Player], logger: logging.Logger
) -> Callable[[], None]:
    def _phase() -> None:
        logger.info("Starting pitch phase...")
        for player in players:
            response = player.respond()
            logger.info(
                "Player %s response: %s",
                player.config.player_id,
                response,
            )

    return _phase

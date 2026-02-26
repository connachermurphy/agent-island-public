from typing import Callable

from ..round import RoundContext
from .consolidate_memory import phase_consolidate_memory
from .pitches import phase_pitches
from .votes import phase_votes

PHASE_REGISTRY: dict[str, Callable[[RoundContext], None]] = {
    "pitches": phase_pitches,
    "votes": phase_votes,
    "consolidate_memory": phase_consolidate_memory,
}

__all__ = [
    "PHASE_REGISTRY",
    "phase_pitches",
    "phase_votes",
    "phase_consolidate_memory",
]

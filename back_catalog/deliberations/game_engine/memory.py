from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from .history import History
    from .player import Player


class MemoryStrategy(ABC):
    """
    Abstract base class for context management strategies.

    Each strategy decides:
    1. How to consolidate raw events into memory (consolidate)
    2. How to render stored memory for the LLM (render)
    3. How to serialize its state (to_dict)
    """

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Identifier for this strategy type."""
        ...

    @abstractmethod
    def consolidate(
        self,
        player: Player,
        history: History,
        round_index: int,
        rules_prompt: str,
    ) -> None:
        """
        Process events from the given round and update internal memory state.

        Called at the end of each round (the phase_consolidate_memory step).
        The strategy owns the LLM call — it calls player.respond() directly
        if needed, and clears active_visibility on events it has consumed.
        """
        ...

    @abstractmethod
    def render(self) -> str:
        """
        Render the current memory state as a string for inclusion
        in the player's context.
        """
        ...

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the memory state for logging."""
        ...


@dataclass
class SummarizationStrategy(MemoryStrategy):
    """
    Asks the player to summarize each round's events into a brief narrative.
    Stores one summary per round. On render, concatenates all summaries.
    """

    summaries: Dict[int, str] = field(default_factory=dict)
    consolidation_log: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def strategy_name(self) -> str:
        return "summarization"

    def consolidate(
        self,
        player: Player,
        history: History,
        round_index: int,
        rules_prompt: str,
    ) -> None:
        player_id = player.config.player_id

        round_log = history.rounds.get(round_index)
        if not round_log:
            return

        # Collect events visible to this player in the current round
        visible_parts: List[str] = []
        visible_events = []
        for event in round_log.events:
            if player_id in event.active_visibility:
                visible_parts.append(f"{event.heading}:")
                visible_parts.append(f"{event.content}\n")
                visible_events.append(event)

        if not visible_parts:
            return

        visible_text = "\n".join(visible_parts)

        # Include past summaries so the agent can connect events across rounds
        memory_context = self.render()
        if memory_context:
            visible_text = f"{memory_context}\n\n{visible_text}"

        system_prompt = f"""{rules_prompt}

{player.config.character_prompt}

Please briefly summarize the events of this round.
This summary will be the only context on the events of this round
that you will have in future rounds.
Other players will not be able to see your summary."""

        response = player.respond(
            system_prompt=system_prompt,
            messages=[{"role": "user", "content": visible_text}],
        )

        self.summaries[round_index] = response.text
        self.consolidation_log.append(
            {
                "round_index": round_index,
                "prompt": f"{system_prompt}\n\n{visible_text}",
                "summary": response.text,
                "reasoning": response.reasoning,
                "metadata": response.metadata,
            }
        )

        # Clear active_visibility on consumed events
        for event in visible_events:
            event.active_visibility.remove(player_id)

    def render(self) -> str:
        if not self.summaries:
            return ""
        parts = ["<memory>"]
        for round_idx in sorted(self.summaries.keys()):
            parts.append(f"Round {round_idx} Summary:")
            parts.append(self.summaries[round_idx])
            parts.append("")
        parts.append("</memory>")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "summaries": {str(k): v for k, v in self.summaries.items()},
            "consolidation_log": self.consolidation_log,
        }


@dataclass
class NoOpStrategy(MemoryStrategy):
    """
    Baseline strategy: no consolidation, full history is always shown.
    active_visibility is never cleared, so render_for_player returns everything.
    """

    @property
    def strategy_name(self) -> str:
        return "none"

    def consolidate(
        self,
        player: Player,
        history: History,
        round_index: int,
        rules_prompt: str,
    ) -> None:
        pass

    def render(self) -> str:
        return ""

    def to_dict(self) -> Dict[str, Any]:
        return {"strategy": self.strategy_name}


STRATEGY_REGISTRY: Dict[str, type] = {
    "none": NoOpStrategy,
    "summarization": SummarizationStrategy,
}


def create_strategy(name: str) -> MemoryStrategy:
    """Factory to create a MemoryStrategy from a config string."""
    cls = STRATEGY_REGISTRY.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown memory strategy '{name}'. "
            f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return cls()

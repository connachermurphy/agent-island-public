from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Event:
    heading: str
    role: str
    prompt: str
    content: str
    visibility: List[str]
    reasoning: str | None = None
    response: Any | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "heading": self.heading,
            "role": self.role,
            "prompt": self.prompt,
            "content": self.content,
            "visibility": self.visibility,
            "reasoning": self.reasoning,
            "response": repr(self.response),
        }


@dataclass
class RoundLog:
    round_index: int
    final_round: bool
    active_player_ids: List[str]
    eliminated_player_ids: List[str]
    events: List[Event] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the round log to a dictionary.

        Args:
            None

        Returns:
            A dictionary representing the round log
        """
        return {
            "round_index": self.round_index,
            "final_round": self.final_round,
            "active_player_ids": self.active_player_ids,
            "eliminated_player_ids": self.eliminated_player_ids,
            "events": [event.to_dict() for event in self.events],
        }


class History:
    def __init__(self) -> None:
        self.rounds: Dict[int, RoundLog] = {}

    def start_round(
        self,
        round_index: int,
        final_round: bool,
        active_player_ids: List[str],
        eliminated_player_ids: List[str],
    ) -> None:
        """
        Start a new round in the game history.

        Args:
            round_index: The index of the round
            final_round: Whether this is the final round
            active_player_ids: The IDs of the active players
            eliminated_player_ids: The IDs of the eliminated players
        """

        self.rounds[round_index] = RoundLog(
            round_index=round_index,
            final_round=final_round,
            active_player_ids=active_player_ids,
            eliminated_player_ids=eliminated_player_ids,
            events=[],
        )

    def add_event(
        self,
        round_index: int,
        heading: str,
        role: str,
        prompt: str,
        content: str,
        visibility: List[str],
        reasoning: str | None = None,
        response: Any | None = None,
    ) -> None:
        """
        Add an event to the game history.

        Args:
            round_index: The index of the round
            heading: The heading of the event
            role: The role of the event
            prompt: The prompt provided to the player
            content: The content of the event (player response or narrator message)
            visibility: The visibility of the event content
            reasoning: The reasoning provided by the player
            response: The response provided by the player

        Returns:
            None
        """
        self.rounds[round_index].events.append(
            Event(
                heading=heading,
                role=role,
                prompt=prompt,
                content=content,
                visibility=visibility,
                reasoning=reasoning,
                response=response,
            )
        )

    def narrate(
        self,
        round_index: int,
        heading: str,
        content: str,
        visibility: List[str],
    ) -> None:
        """
        Add a narrator message to the game history.

        Args:
            round_index: The index of the round
            heading: The heading of the event
            content: The content of the event
            visibility: The visibility of the event

        Returns:
            None
        """
        self.add_event(
            round_index=round_index,
            heading=heading,
            role="narrator",
            prompt="N/A",
            content=content,
            visibility=visibility,
        )

    def render_for_player(self, player_id: str) -> str:
        """
        Render the game history for a player.

        Args:
            player_id: The ID of the player to render the history for

        Returns:
            A string representing the game history for the player

        Notes:
            - Only events that are visible to the player will be rendered
            - Reasoning is _not_ rendered for any events
        """
        parts: List[str] = ["<game_history>"]
        for round_log in self.rounds.values():
            parts.append(f"Round {round_log.round_index}:")
            for event in round_log.events:
                if player_id in event.visibility:
                    parts.append(f"{event.heading}:")
                    parts.append(f"{event.content}\n")
        parts.append("</game_history>")
        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the history to a dictionary.

        Args:
            None

        Returns:
            A dictionary representing the game history
        """
        return {str(k): v.to_dict() for k, v in self.rounds.items()}

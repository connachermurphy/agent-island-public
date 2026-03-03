import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from openrouter import OpenRouter

from .llm_response import LLMResponse, parse_openrouter_response
from .memory import MemoryStrategy, create_strategy

logger = logging.getLogger(__name__)


@dataclass
class PlayerConfig:
    """
    Configuration for a player

    Args:
        player_id: The ID of the player
        character_prompt: The prompt for the player's character
        provider: The provider of the player's client
        model: The model of the player's client
        api_key: The API key for the player's client
        client_kwargs: The kwargs for the player's client
            (use Responses API param names)
    """

    player_id: str
    character_prompt: str
    model: str
    api_key: str
    client_kwargs: dict
    memory_strategy: str = "none"


@dataclass
class FreeResponse:
    text: str
    reasoning: str | None = None
    metadata: dict | None = None


@dataclass
class ChoiceResponse:
    selected: str | None
    text: str
    reasoning: str | None = None
    metadata: dict | None = None


class Player(ABC):
    config: PlayerConfig
    memory: MemoryStrategy

    @abstractmethod
    def free_response(self, system_prompt: str, context: str) -> FreeResponse: ...

    @abstractmethod
    def choice_response(
        self, system_prompt: str, context: str, options: list[str]
    ) -> ChoiceResponse: ...


class AIPlayer(Player):
    def __init__(self, config: PlayerConfig, max_retries: int = 3):
        """
        Initialize the AIPlayer class

        Args:
            config: PlayerConfig object
            max_retries: Number of retry attempts on API failure
        """
        self.config = config
        self.max_retries = max_retries
        self.client = OpenRouter(api_key=config.api_key)
        self.memory: MemoryStrategy = create_strategy(config.memory_strategy)

    def free_response(self, system_prompt: str, context: str) -> FreeResponse:
        result = self._respond(system_prompt, context)
        return FreeResponse(
            text=result.text,
            reasoning=result.reasoning,
            metadata=result.metadata,
        )

    def choice_response(
        self, system_prompt: str, context: str, options: list[str]
    ) -> ChoiceResponse:
        result = self._respond(system_prompt, context)
        selected = self._extract_vote(result.text, options)
        metadata = dict(result.metadata) if result.metadata else {}
        if selected is None:
            metadata["vote_parse_failed"] = True
        return ChoiceResponse(
            selected=selected,
            text=result.text,
            reasoning=result.reasoning,
            metadata=metadata or None,
        )

    def _respond(
        self,
        system_prompt: str,
        context: str,
    ) -> LLMResponse:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.beta.responses.send(
                    model=self.config.model,
                    instructions=system_prompt,
                    input=context,
                    **self.config.client_kwargs,
                )
                result = parse_openrouter_response(response)
                if attempt > 0:
                    meta = dict(result.metadata) if result.metadata else {}
                    meta["retries"] = attempt
                    result.metadata = meta
                return result
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    wait = 2**attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Request failed for player %s (attempt %d/%d): %s. "
                        "Retrying in %ds.",
                        self.config.player_id,
                        attempt + 1,
                        self.max_retries + 1,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "Request failed for player %s after %d attempt(s): %s",
                        self.config.player_id,
                        self.max_retries + 1,
                        exc,
                    )
        raise last_exc  # type: ignore[misc]

    def _extract_vote(self, content: str, valid_player_ids: list[str]) -> Optional[str]:
        match = re.search(r"<vote>(.*?)</vote>", content, re.IGNORECASE | re.DOTALL)
        if match:
            vote = match.group(1).strip()
            if vote in valid_player_ids and vote != self.config.player_id:
                return vote
        return None

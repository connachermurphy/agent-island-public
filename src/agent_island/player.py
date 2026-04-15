import logging
import queue
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol

from openrouter import OpenRouter

from .llm_response import LLMResponse, parse_openrouter_response
from .memory import MemoryStrategy, create_strategy

logger = logging.getLogger(__name__)


@dataclass
class PlayerConfig:
    """
    Configuration for a player.

    AI players require model and api_key. Human players can omit them.
    """

    player_id: str
    character_prompt: str
    model: str = ""
    api_key: str = ""
    client_kwargs: dict = field(default_factory=dict)
    memory_strategy: str = "none"
    player_type: str = "ai"


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


class FreeCollector(Protocol):
    def collect(self, system_prompt: str, context: str, action: str) -> str: ...


class ChoiceCollector(Protocol):
    def collect(
        self, system_prompt: str, context: str, options: list[str], action: str
    ) -> tuple[str, str]:
        # returns (selected, text)
        ...


class Player(ABC):
    config: PlayerConfig
    memory: MemoryStrategy

    @abstractmethod
    def free_response(
        self, system_prompt: str, context: str, action: str, llm_instructions: str = ""
    ) -> FreeResponse: ...

    @abstractmethod
    def choice_response(
        self,
        system_prompt: str,
        context: str,
        options: list[str],
        action: str,
        llm_instructions: str = "",
    ) -> ChoiceResponse: ...


class AIPlayer(Player):
    def __init__(
        self,
        config: PlayerConfig,
        max_retries: int = 3,
        timeout_ms: int = 600_000,
    ):
        self.config = config
        self.max_retries = max_retries
        self.client = OpenRouter(api_key=config.api_key, timeout_ms=timeout_ms)
        self.memory: MemoryStrategy = create_strategy(config.memory_strategy)

    def free_response(
        self, system_prompt: str, context: str, action: str, llm_instructions: str = ""
    ) -> FreeResponse:
        result = self._respond(system_prompt, context, action, llm_instructions)
        return FreeResponse(
            text=result.text,
            reasoning=result.reasoning,
            metadata=result.metadata,
        )

    def choice_response(
        self,
        system_prompt: str,
        context: str,
        options: list[str],
        action: str,
        llm_instructions: str = "",
    ) -> ChoiceResponse:
        result = self._respond(system_prompt, context, action, llm_instructions)
        selected = self._extract_choice(result.text, options)
        metadata = dict(result.metadata) if result.metadata else {}
        if selected is None:
            metadata["choice_parse_failed"] = True
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
        action: str,
        llm_instructions: str = "",
    ) -> LLMResponse:
        input_parts = [context, action]
        if llm_instructions:
            input_parts.append(llm_instructions)

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.beta.responses.send(
                    model=self.config.model,
                    instructions=system_prompt,
                    input="\n\n".join(input_parts),
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
                        "Request failed for player %s (model %s) "
                        "(attempt %d/%d): %s. Retrying in %ds.",
                        self.config.player_id,
                        self.config.model,
                        attempt + 1,
                        self.max_retries + 1,
                        exc,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "Request failed for player %s (model %s) "
                        "after %d attempt(s): %s",
                        self.config.player_id,
                        self.config.model,
                        self.max_retries + 1,
                        exc,
                    )
        raise RuntimeError(
            f"Request failed for player {self.config.player_id} "
            f"(model {self.config.model}) after {self.max_retries + 1} "
            f"attempt(s): {last_exc}"
        ) from last_exc

    def _extract_choice(
        self, content: str, valid_player_ids: list[str]
    ) -> Optional[str]:
        match = re.search(r"<choice>(.*?)</choice>", content, re.IGNORECASE | re.DOTALL)
        if match:
            choice = match.group(1).strip()
            if choice in valid_player_ids and choice != self.config.player_id:
                return choice
        return None


class HumanPlayer(Player):
    def __init__(
        self, config: PlayerConfig, free: FreeCollector, choice: ChoiceCollector
    ):
        if config.memory_strategy != "none":
            raise ValueError(
                f"Human player '{config.player_id}' has memory_strategy="
                f"'{config.memory_strategy}', but human players do not support "
                f"memory consolidation. Remove the field or set it to 'none'."
            )
        self.config = config
        # Human players always use NoOpStrategy
        self.memory: MemoryStrategy = create_strategy("none")
        self._free = free
        self._choice = choice

    def free_response(
        self, system_prompt: str, context: str, action: str, llm_instructions: str = ""
    ) -> FreeResponse:
        # llm_instructions (e.g. XML vote format) is for AI parsing; ignored for humans.
        text = self._free.collect(system_prompt, context, action)
        return FreeResponse(text=text)

    def choice_response(
        self,
        system_prompt: str,
        context: str,
        options: list[str],
        action: str,
        llm_instructions: str = "",
    ) -> ChoiceResponse:
        # llm_instructions (e.g. XML vote format) is for AI parsing; ignored for humans.
        selected, text = self._choice.collect(system_prompt, context, options, action)
        return ChoiceResponse(selected=selected, text=text)


# ---------------------------------------------------------------------------
# Remote collectors — for use with the FastAPI web backend.
#
# Both collectors block on a queue.Queue until the web layer pushes a payload.
# The on_waiting callback is fired first so the backend can tell the frontend
# that human input is needed and what prompt to show.
#
# on_waiting signature:
#   on_waiting(kind, system_prompt, context, action, options)
#   kind: "free" | "choice"
#   options: list[str] for "choice", None for "free"
# ---------------------------------------------------------------------------


class RemoteFreeCollector:
    """Blocks on input_queue until the web layer posts {"text": ...}."""

    def __init__(
        self,
        input_queue: "queue.Queue[dict]",
        on_waiting: Callable[[str, str, str, str, "list[str] | None"], None],
    ):
        self._input_queue = input_queue
        self._on_waiting = on_waiting

    def collect(self, system_prompt: str, context: str, action: str) -> str:
        self._on_waiting("free", system_prompt, context, action, None)
        payload = self._input_queue.get(block=True)
        if payload.get("_cancelled"):
            raise RuntimeError("Game session cancelled.")
        return payload["text"]


class RemoteChoiceCollector:
    """Blocks on input_queue until the web layer posts
    {"selected": ..., "text": ...}."""

    def __init__(
        self,
        input_queue: "queue.Queue[dict]",
        on_waiting: Callable[[str, str, str, str, "list[str] | None"], None],
    ):
        self._input_queue = input_queue
        self._on_waiting = on_waiting

    def collect(
        self, system_prompt: str, context: str, options: list[str], action: str
    ) -> tuple[str, str]:
        self._on_waiting("choice", system_prompt, context, action, options)
        payload = self._input_queue.get(block=True)
        if payload.get("_cancelled"):
            raise RuntimeError("Game session cancelled.")
        return payload["selected"], payload["text"]

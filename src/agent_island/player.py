import re
from dataclasses import dataclass
from typing import Optional

from openrouter import OpenRouter

from .llm_response import LLMResponse, parse_openrouter_response
from .memory import MemoryStrategy, create_strategy


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


class Player:
    def __init__(self, config: PlayerConfig):
        """
        Initialize the Player class

        Args:
            config: PlayerConfig object
            client: Client object
        """
        self.config = config
        self.client = OpenRouter(api_key=config.api_key)
        self.memory: MemoryStrategy = create_strategy(config.memory_strategy)

    def respond(
        self,
        system_prompt: str,
        context: str,
    ) -> LLMResponse:
        """
        Get an LLM response from the player

        Args:
            system_prompt: Instructions for the player (rules, character, task)
            context: The game context the player is responding to

        Returns:
            The response from the client
        """
        response = self.client.beta.responses.send(
            model=self.config.model,
            instructions=system_prompt,
            input=context,
            **self.config.client_kwargs,
        )
        return parse_openrouter_response(response)

    def extract_vote(self, content: str, valid_player_ids: list[str]) -> Optional[str]:
        """
        Extract vote from player response using structured format

        Args:
            response (str): The response from the player

        Returns:
            Optional[str]: The vote from the player (None if no vote is found)
        """

        # Grab the vote from the within the <vote> tags
        match = re.search(r"<vote>(.*?)</vote>", content, re.IGNORECASE | re.DOTALL)
        if match:
            vote = match.group(1).strip()
            if vote in valid_player_ids and vote != self.config.player_id:
                return vote

        return None

import re
from dataclasses import dataclass
from typing import Optional

from llm_wrapper import Client


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
    """

    player_id: str
    character_prompt: str
    provider: str
    model: str
    api_key: str
    client_kwargs: dict

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "character_prompt": self.player_prompt,
            "provider": self.provider,
            "model": self.model,
            "client_kwargs": repr(self.client_kwargs)
        }


class Player:
    def __init__(self, config: PlayerConfig, client: Client):
        """
        Initialize the Player class

        Args:
            config: PlayerConfig object
            client: Client object
        """
        self.config = config
        self.client = client

    def respond(
        self,
        system_prompt: str,
        messages: list[dict],
    ):
        """
        Get an LLM response from the player

        Args:
            system_prompt: The system prompt for the client
            messages: The message history for the client

        Returns:
            The response from the client
        """
        response = self.client.generate(
            system=system_prompt,
            messages=messages,
            **self.config.client_kwargs,
        )
        return response

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

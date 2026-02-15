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
        # TODO: Measure number of tokens in and out to determine if we are compressing context
        if hasattr(response, 'raw') and hasattr(response.raw, 'usage_metadata'):
            usage_metadata = response.raw.usage_metadata
            usage_in = getattr(usage_metadata, 'prompt_token_count', None)
            usage_out = getattr(usage_metadata, 'candidates_token_count', None)
            thoughts_tokens = getattr(usage_metadata, 'thoughts_token_count', None)
            total_tokens = getattr(usage_metadata, 'total_token_count', None)
           
        print(f"[tokens] player={self.config.player_id} in={usage_in} out={usage_out} thoughts={thoughts_tokens} total={total_tokens}")

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

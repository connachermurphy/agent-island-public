import re
from dataclasses import dataclass
from typing import Optional

from llm_wrapper import Client


@dataclass
class PlayerConfig:
    player_id: str
    character_prompt: str
    provider: str
    model: str
    api_key: str
    client_kwargs: dict


class Player:
    def __init__(self, config: PlayerConfig, client: Client):
        self.config = config
        self.client = client

    def respond(
        self,
        system_prompt: str,
        messages: list[dict],
    ) -> str:
        response = self.client.generate(
            system=system_prompt,
            messages=messages,
            **self.config.client_kwargs,
        )
        return response

    def extract_vote(
        self, content: str, valid_player_ids: list[str]
    ) -> Optional[str]:
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

        # TODO: add warnings
        return None

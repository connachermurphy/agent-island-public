from dataclasses import dataclass

from llm_wrapper import Client

# TODO: add character prompt
# TODO: add temperature
# TODO: add max_tokens
# TODO: add reasoning


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

    # TODO: add an extract_vote method

from dataclasses import dataclass

from llm_wrapper import Client

# TODO: add character prompt
# TODO: add temperature
# TODO: add max_tokens
# TODO: add reasoning


@dataclass
class PlayerConfig:
    player_id: str
    provider: str
    model: str
    api_key: str


class Player:
    def __init__(self, config: PlayerConfig, client: Client):
        self.config = config
        self.client = client

    def respond(self) -> str:
        # TODO: add other arguments to the generate method
        response = self.client.generate(
            messages=[{"role": "user", "content": "Hello, there!"}]
        )
        return response.text

    # TODO: add an extract_vote method

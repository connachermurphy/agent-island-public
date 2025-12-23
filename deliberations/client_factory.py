from dataclasses import dataclass
from typing import Dict

from llm_wrapper import create_client


@dataclass(frozen=True)
class ClientConfig:
    provider: str
    model: str
    api_key: str


class ClientFactory:
    def __init__(self) -> None:
        self._clients: Dict[ClientConfig, object] = {}

    def get(self, provider: str, model: str, api_key: str):
        key = ClientConfig(provider=provider, model=model, api_key=api_key)
        if key not in self._clients:
            self._clients[key] = create_client(
                provider=provider,
                api_key=api_key,
                model=model,
            )
        return self._clients[key]

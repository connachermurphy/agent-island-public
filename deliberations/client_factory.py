from dataclasses import dataclass
from typing import Dict

from llm_wrapper import create_client


@dataclass(frozen=True)
class ClientConfig:
    """
    Configuration for a client

    Args:
        provider: The provider of the client
        model: The model of the client
        api_key: The API key for the client
    """

    provider: str
    model: str
    api_key: str


class ClientFactory:
    def __init__(self) -> None:
        """
        Initialize the ClientFactory class

        Args:
            None
        """
        self._clients: Dict[ClientConfig, object] = {}

    def get(self, provider: str, model: str, api_key: str):
        """
        Get a client, creating it if it doesn't exist

        Args:
            provider: The provider of the client
            model: The model of the client
            api_key: The API key for the client

        Returns:
            The client
        """
        key = ClientConfig(provider=provider, model=model, api_key=api_key)
        if key not in self._clients:
            self._clients[key] = create_client(
                provider=provider,
                api_key=api_key,
                model=model,
            )
        return self._clients[key]

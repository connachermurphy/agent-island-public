# Agent Island: Deliberations

Introducing season 3 of Agent Island, Deliberations.

## Gameplay

We 

`description`

## Engine structure
- `engine.py` ([⬇️](#enginepy))
- `player.py` ([⬇️](#playerpy))
- `client_factory.py` ([⬇️](#client_factorypy))
- `round.py` ([⬇️](#roundpy))
- `round_phases.py`
- `client_factory.py`
- `history.py`

### `engine.py`
Creates the `GameEngine` class, with an associated `GameEngineConfig`. `GameEngine` orchestrates the gameplay.

The `GameEngineConfig` class accepts the following parameters:
- `logger` (`logging.Logger`): Logger for the GameEngine
- `player_configs` (`list[PlayerConfig]`): List of PlayerConfig objects
- `logs_dir` (`str`): Directory to save logs
- `rules_prompt` (`str`): Prompt with the rules of the game

### `player.py`
Creates the `Player` class, with an associated `PlayerConfig` class.

The `PlayerConfig` class accepts the following parameters:
- `player_id` (`str`): The ID of the player
- `character_prompt` (`str`): The prompt for the player's character
- `provider` (`str`): The provider of the player's client
- `model` (`str`): The model of the player's client
- `api_key` (`str`): The API key for the player's client
- `client_kwargs` (`dict`): Additional keyword arguments for the client

### `client_factory.py`
Creates the `ClientFactory` class, with an associated `ClientConfig` class. The `ClientFactory` class maintains LLM clients and avoids duplication of the clients.

The `ClientConfig` class accepts the following parameters:
- `provider` (`str`): The provider of the client.
- `model` (`str`): The model of the client.
- `api_key` (`str`): The API key for the client.

## Usage

To set up your virtual environment and install dependencies, run:

```bash
uv sync
```

To run a sample game, execute:

```bash
uv run example.py
```

## Logs

`Describe logs usage`
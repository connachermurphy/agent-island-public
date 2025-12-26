# Agent Island: Deliberations

Introducing season 3 of Agent Island, Deliberations.

## Gameplay

We 

`description`

## Engine structure
- `engine.py` ([⬇️](#enginepy))
- `player.py` ([⬇️](#playerpy))
- `round.py` ([⬇️](#roundpy))
- `round_phases.py`
- `client_factory.py`
- `history.py`

### `engine.py`
Creates the `GameEngine` class, with an associated `GameEngineConfig`. `GameEngine` orchestrates the gameplay.

### `player.py`
Creates the `Player` class, with an associated `PlayerConfig` class.

The `Player` class requires the following parameters:
- `player_id` (`str`): The ID of the player
- `character_prompt` (`str`): The prompt for the player's character
- `provider` (`str`): The provider of the player's client
- `model` (`str`): The model of the player's client
- `api_key` (`str`): The API key for the player's client
- `client_kwargs` (`dict`): Additional keyword arguments for the client

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
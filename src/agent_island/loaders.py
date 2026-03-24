import pathlib
import tomllib

from .player import (
    AIPlayer,
    ChoiceCollector,
    FreeCollector,
    HumanPlayer,
    Player,
    PlayerConfig,
)

VALID_PLAYER_TYPES = {"ai", "human"}


def load_game_config_from_toml(config_path: pathlib.Path) -> dict:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    game = data.get("game", {})

    # Parse round_overrides array-of-tables into dict[int, list[str]]
    round_overrides = game.pop("round_overrides", [])
    for i, entry in enumerate(round_overrides):
        if "round" not in entry or "phases" not in entry:
            raise ValueError(
                f"round_overrides[{i}] must have both 'round' and 'phases' keys, "
                f"got: {list(entry.keys())}"
            )
    game["round_phase_overrides"] = {
        entry["round"]: entry["phases"] for entry in round_overrides
    }

    return game


def load_player_configs_from_toml(
    config_path: pathlib.Path, api_key: str
) -> list[PlayerConfig]:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    players = data.get("players", [])
    for i, p in enumerate(players):
        player_type = p.get("player_type", "ai")
        if player_type not in VALID_PLAYER_TYPES:
            raise ValueError(
                f"players[{i}] has invalid player_type '{player_type}', "
                f"must be one of {sorted(VALID_PLAYER_TYPES)}"
            )
    return [
        PlayerConfig(
            player_id=p["player_id"],
            character_prompt=p["character_prompt"],
            model=p.get("model", ""),
            api_key=api_key if p.get("player_type", "ai") == "ai" else "",
            client_kwargs=p.get("client_kwargs", {}),
            memory_strategy=p.get("memory_strategy", "none"),
            player_type=p.get("player_type", "ai"),
        )
        for p in players
    ]


def create_players(
    player_configs: list[PlayerConfig],
    free_collector: FreeCollector,
    choice_collector: ChoiceCollector,
) -> list[Player]:
    players: list[Player] = []
    for config in player_configs:
        if config.player_type == "human":
            players.append(HumanPlayer(config, free_collector, choice_collector))
        else:
            players.append(AIPlayer(config))
    return players

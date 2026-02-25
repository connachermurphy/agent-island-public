import pathlib
import tomllib

from .player import PlayerConfig


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
    return [
        PlayerConfig(
            player_id=p["player_id"],
            character_prompt=p["character_prompt"],
            model=p["model"],
            api_key=api_key,
            client_kwargs=p.get("client_kwargs", {}),
            memory_strategy=p.get("memory_strategy", "none"),
        )
        for p in players
    ]

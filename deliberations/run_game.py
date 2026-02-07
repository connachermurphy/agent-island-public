import argparse
import logging
import os
import pathlib
import tomllib

import dotenv
from game_engine import GameEngine, GameEngineConfig, PlayerConfig

LOGS_DIR = "logs"

dotenv.load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def load_player_specs_from_toml(config_path: str) -> list[dict]:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is required but not set.")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    players = data.get("players", [])
    specs: list[dict] = []
    for p in players:
        spec = {
            "player_id": p["player_id"],
            "character_prompt": p["character_prompt"],
            "model": p["model"],
            "api_key": OPENROUTER_API_KEY,
            "client_kwargs": p.get("client_kwargs", {}),
        }
        specs.append(spec)
    return specs


if __name__ == "__main__":
    # Prepare logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Parse optional config path argument
    parser = argparse.ArgumentParser(description="Run an Agent Island game")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to a player config TOML file",
    )
    args = parser.parse_args()

    # Load player specifications from TOML config
    here = pathlib.Path(__file__).parent
    config_path = here / (args.config if args.config else "player_config.toml")
    player_specs = load_player_specs_from_toml(str(config_path))
    num_players = len(player_specs)

    rules_prompt = f"""
        You are a player in a game with {num_players} players.
        In round 1 through {num_players - 2}, you and the
        other players will first make a pitch for why you
        should advance to the next round. After all players
        make their pitches, you will then vote to eliminate
        one other player. The player with the most votes is
        eliminated. You will be notified explicitly when it
        is your turn to vote.

        In round {num_players - 1}, you will make a pitch
        for why you should win the game. The previously
        eliminated players will choose the winner. The
        player with the most votes wins the game.

        You will speak in a random order. You can reference
        anything in your pitches and votes, including
        previous players' speeches and actions.
    """

    player_configs = [PlayerConfig(**config) for config in player_specs]
    game_config = GameEngineConfig(
        logger=logger,
        player_configs=player_configs,
        logs_dir=LOGS_DIR,
        rules_prompt=rules_prompt,
    )
    game = GameEngine(game_config)
    game.play()

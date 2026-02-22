import argparse
import logging
import os
import pathlib

import dotenv

from .engine import GameConfig, GameEngine
from .loaders import load_game_config_from_toml, load_player_configs_from_toml

LOGS_DIR = "logs"

dotenv.load_dotenv()


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Run an Agent Island game")
    parser.add_argument(
        "--game-config",
        type=pathlib.Path,
        default=pathlib.Path("game_config.toml"),
        help="Path to a game config TOML file",
    )
    parser.add_argument(
        "--player-config",
        type=pathlib.Path,
        default=pathlib.Path("player_config.toml"),
        help="Path to a player config TOML file",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required but not set.")

    game_data = load_game_config_from_toml(args.game_config)
    player_configs = load_player_configs_from_toml(args.player_config, api_key=api_key)
    num_players = len(player_configs)

    rules_prompt = game_data["rules_prompt"].format(
        num_players=num_players,
        elimination_rounds=num_players - 2,
        final_round_number=num_players - 1,
    )

    game_config = GameConfig(
        phases=game_data["phases"],
        logs_dir=game_data.get("logs_dir", LOGS_DIR),
        rules_prompt=rules_prompt,
        log_prefix=game_data.get("log_prefix", "gameplay"),
        game_id=game_data.get("game_id"),
    )

    game = GameEngine(game_config=game_config, player_configs=player_configs)
    game.play()

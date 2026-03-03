import argparse
import logging
import os
import pathlib

import dotenv

from .engine import GameConfig, GameEngine
from .history import Event
from .loaders import (
    create_players,
    load_game_config_from_toml,
    load_player_configs_from_toml,
)

LOGS_DIR = "logs"

dotenv.load_dotenv()


class CLIFreeCollector:
    def collect(self, system_prompt: str, context: str) -> str:
        return input("\nYour response: ")


class CLIChoiceCollector:
    def collect(
        self, system_prompt: str, context: str, options: list[str]
    ) -> tuple[str, str]:
        print()
        for i, opt in enumerate(options):
            print(f"  {i + 1}. {opt}")
        while True:
            raw = input("Your choice (number): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                selected = options[int(raw) - 1]
                break
            print(f"Please enter a number between 1 and {len(options)}.")
        text = input("Explanation: ")
        return selected, text


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

    api_key = os.getenv("OPENROUTER_API_KEY", "")

    game_data = load_game_config_from_toml(args.game_config)
    player_configs = load_player_configs_from_toml(args.player_config, api_key=api_key)

    if any(c.player_type == "ai" for c in player_configs) and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for AI players but not set.")

    players = create_players(player_configs, CLIFreeCollector(), CLIChoiceCollector())

    game_config = GameConfig(
        num_players=game_data["num_players"],
        num_rounds=game_data["num_rounds"],
        phases=game_data["phases"],
        logs_dir=game_data.get("logs_dir", LOGS_DIR),
        rules_prompt=game_data["rules_prompt"],
        round_phase_overrides=game_data.get("round_phase_overrides", {}),
        log_prefix=game_data.get("log_prefix", "gameplay"),
        game_id=game_data.get("game_id"),
    )

    human_ids = {p.config.player_id for p in players if p.config.player_type == "human"}

    on_event = None
    if human_ids:
        # Suppress INFO noise; game events stream to stdout via on_event instead
        logging.getLogger().setLevel(logging.WARNING)

        def on_event(event: Event) -> None:
            if any(pid in event.visibility for pid in human_ids):
                content = event.content
                if event.metadata and event.metadata.get("vote"):
                    content = f"Vote: {event.metadata['vote']}\n{content}"
                print(f"\n{event.heading}:\n{content}")

    game = GameEngine(game_config=game_config, players=players, on_event=on_event)
    game.play()

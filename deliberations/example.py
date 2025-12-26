import logging
import os

import dotenv
from engine import GameEngine, GameEngineConfig
from player import PlayerConfig

dotenv.load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MAX_OUTPUT_TOKENS = 1024
LOGS_DIR = "logs"

if __name__ == "__main__":
    # Prepare logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Prepare player specifications
    player_specs = [
        {
            "player_id": "A",
            "character_prompt": "You are player A.",
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "api_key": ANTHROPIC_API_KEY,
            "client_kwargs": {
                "max_tokens": 2048,
                "reasoning": {
                    "type": "enabled",
                    "budget_tokens": 1024,
                },
            },
        },
        {
            "player_id": "B",
            "character_prompt": "You are player B.",
            "provider": "openai",
            "model": "gpt-5-nano-2025-08-07",
            "api_key": OPENAI_API_KEY,
            "client_kwargs": {
                "max_tokens": 2048,
                "reasoning": {
                    "effort": "low",
                    "summary": "auto",
                },
            },
        },
        {
            "player_id": "C",
            "character_prompt": "You are player C.",
            "provider": "openai",
            "model": "gpt-5-nano-2025-08-07",
            "api_key": OPENAI_API_KEY,
            "client_kwargs": {
                "max_tokens": 2048,
                "reasoning": {
                    "effort": "low",
                    "summary": "auto",
                },
            },
        },
    ]

    rules_prompt = """
You are a player in a game.
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

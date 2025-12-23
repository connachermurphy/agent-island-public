import logging
import os

import dotenv
from engine import GameEngine
from player import PlayerConfig

dotenv.load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MAX_OUTPUT_TOKENS = 1024


if __name__ == "__main__":
    # Prepare logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Prepare player specifications
    player_specs = [
        {
            "player_id": "A",
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "api_key": ANTHROPIC_API_KEY,
        },
        {
            "player_id": "B",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": OPENAI_API_KEY,
        },
        {
            "player_id": "C",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": OPENAI_API_KEY,
        },
    ]

    player_configs = [PlayerConfig(**config) for config in player_specs]
    game = GameEngine(logger, player_configs)
    game.play()

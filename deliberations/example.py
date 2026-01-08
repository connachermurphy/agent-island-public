import logging
import os

import dotenv
from engine import GameEngine, GameEngineConfig
from player import PlayerConfig

dotenv.load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
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
                },
            },
        },
        {
            "player_id": "C",
            "character_prompt": "You are player C.",
            "provider": "google",
            "model": "gemini-3-flash-preview",
            "api_key": GOOGLE_API_KEY,
            "client_kwargs": {
                "max_tokens": 2048,
                "reasoning": {
                    "include_thoughts": True,
                    "thinking_level": "low",
                },
            },
        },
    ]

    num_players = len(player_specs)

    rules_prompt = f"""
You are a player in a game with {num_players} players. In round 1 through {num_players - 2}, you and the other players will first make a pitch for why you should advance to the next round. After all players make their pitches, you will then vote to eliminate one other player. The player with the most votes is eliminated. You will be notified explicitly when it is your turn to vote.

In round {num_players - 1}, you will make a pitch for why you should win the game. The previously eliminated players will choose the winner. The player with the most votes wins the game.

You will speak in a random order. You can reference anything in your pitches and votes, including previous players' speeches and actions.
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

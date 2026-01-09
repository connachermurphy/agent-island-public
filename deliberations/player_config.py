"""
Player configuration for the game.
Edit this file to customize the players, models, and reasoning parameters.
"""

import os
import dotenv

dotenv.load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure your players here
PLAYER_SPECS = [
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

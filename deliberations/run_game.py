import logging
import os
import pathlib
import tomllib
import dotenv

from game_engine import GameEngine, GameEngineConfig, PlayerConfig

LOGS_DIR = "logs"

dotenv.load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def _default_api_key_env(provider: str) -> str | None:
    mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    return mapping.get(provider.lower())


def load_player_specs_from_toml(config_path: str) -> list[dict]:
    with open(config_path, "rb") as f:
        data = tomllib.load(f)
    players = data.get("players", [])
    specs: list[dict] = []
    for p in players:
        provider = p["provider"]
        api_key_env = p.get("api_key_env") or _default_api_key_env(provider)
        api_key = os.getenv(api_key_env) if api_key_env else None
        spec = {
            "player_id": p["player_id"],
            "character_prompt": p["character_prompt"],
            "provider": provider,
            "model": p["model"],
            "api_key": api_key,
            "client_kwargs": p.get("client_kwargs", {}),
        }
        specs.append(spec)
    return specs


if __name__ == "__main__":
    # Prepare logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load player specifications from TOML config
    here = pathlib.Path(__file__).parent
    config_path = here / "player_config.toml"
    player_specs = load_player_specs_from_toml(str(config_path))
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

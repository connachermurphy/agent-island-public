import logging

from game_engine import GameEngine, GameEngineConfig, PlayerConfig
from player_config import PLAYER_SPECS

LOGS_DIR = "logs"

if __name__ == "__main__":
    # Prepare logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load player specifications from config
    player_specs = PLAYER_SPECS
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

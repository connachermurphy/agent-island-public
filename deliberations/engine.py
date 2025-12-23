import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List

from client_factory import ClientFactory
from history import History
from player import Player, PlayerConfig
from round import Round, RoundContext
from round_phases import phase_pitches, phase_votes


# TODO: use the GameEngineConfig to structure the .play() method
@dataclass
class GameEngineConfig:
    logger: logging.Logger
    player_configs: list[PlayerConfig]
    logs_dir: str
    rules_prompt: str


class GameEngine:
    def __init__(
        self,
        game_config: GameEngineConfig,
    ):
        self.game_config = game_config
        self.players = self._initialize_players()
        self.history = History()

    def _initialize_players(self) -> List[Player]:
        players: List[Player] = []

        client_factory = ClientFactory()

        for player_config in self.game_config.player_configs:
            client = client_factory.get(
                provider=player_config.provider,
                model=player_config.model,
                api_key=player_config.api_key,
            )
            player = Player(player_config, client)
            players.append(player)

        return players

    def _create_round_context(
        self, round_index: int, players: List[Player]
    ) -> RoundContext:
        return RoundContext(
            round_index=round_index,
            players=players,
            logger=self.game_config.logger,
            history=self.history,
            rules_prompt=self.game_config.rules_prompt,
        )

    def play(self):
        """
        Play the game
        """
        # Set timestamp (output filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Initialize game
        self.game_config.logger.info(f"Starting Deliberations game ({timestamp})")

        # Count number of players
        num_players = len(self.players)

        self.game_config.logger.info(f"{num_players} players")

        # Store original set of player IDs in history
        # TODO: do not conflate player IDs with player objects
        player_ids = [player.config.player_id for player in self.players]
        self.history.player_ids = player_ids

        #########################################################
        # Start placeholder for game logic
        #########################################################
        # Run a generic round with just pitches
        round_index = 1

        round_context = self._create_round_context(round_index, self.players)
        round = Round(context=round_context, phases=[phase_pitches, phase_votes])
        round.play()

        self.game_config.logger.info(
            f"Vote tally: {round_context.vote_tally} (from engine.py)"
        )

        self.game_config.logger.info(
            f"Eliminated player: {round_context.eliminated_player} (from engine.py)"
        )

        next_round_players = [
            player
            for player in self.players
            if player.config.player_id != round_context.eliminated_player
        ]

        self.game_config.logger.info(
            f"Next round players: {[player.config.player_id for player in next_round_players]} (from engine.py)"
        )

        # TODO: update active players and launch next round

        #########################################################
        # End placeholder for game logic
        #########################################################

        # Log game history
        output_path = os.path.join(
            self.game_config.logs_dir, f"gameplay_{timestamp}.json"
        )
        with open(output_path, "w") as f:
            json.dump(self.history.to_dict(), f, indent=2)
        self.game_config.logger.info("Wrote game history to %s", output_path)

import logging
from typing import List

# TODO: add a GameConfig class that structures the .play() method
from client_factory import ClientFactory
from player import Player, PlayerConfig
from round import Round
from round_phases import phase_pitches


class GameEngine:
    def __init__(self, logger: logging.Logger, player_configs: list[PlayerConfig]):
        self.logger = logger
        self.player_configs = player_configs
        self.players = self._initialize_players()

    def _initialize_players(self) -> List[Player]:
        players: List[Player] = []

        client_factory = ClientFactory()

        for player_config in self.player_configs:
            client = client_factory.get(
                provider=player_config.provider,
                model=player_config.model,
                api_key=player_config.api_key,
            )
            player = Player(player_config, client)
            players.append(player)

        return players

    def play(self):
        """
        Play the game
        """

        self.logger.info(
            "Starting Deliberations game from the GameEngine.play() method..."
        )

        num_players = len(self.players)

        # TODO: build out Round class
        # TODO: built out History class
        # TODO: use Round and History classes to play the game
        print(f"Number of players: {num_players}")

        # Run a generic round with just pitches
        round = Round(
            logger=self.logger,
            phases=[phase_pitches(self.players, self.logger)],
        )

        round.play()

        pass

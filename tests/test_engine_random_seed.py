"""Tests for game identity and random-seed separation."""

import random
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from agent_island import GameConfig, GameEngine, PlayerConfig
from agent_island.phases import PHASE_REGISTRY


def _player(player_id: str):
    return SimpleNamespace(
        config=PlayerConfig(
            player_id=player_id,
            character_prompt=f"You are {player_id}.",
        )
    )


def _config(*, game_id: str, random_seed: int | None = None) -> GameConfig:
    return GameConfig(
        num_players=2,
        num_rounds=1,
        phases=["capture_randomness"],
        rules_prompt="Rules",
        game_id=game_id,
        random_seed=random_seed,
    )


class GameRandomSeedTest(unittest.TestCase):
    def test_explicit_seed_is_independent_from_game_id(self) -> None:
        players = [_player("AAAA"), _player("BBBB")]
        draws: list[tuple[float, list[str]]] = []

        def capture_randomness(context):
            draws.append(
                (
                    context.rng.random(),
                    context.rng.sample(context.active_player_ids, k=2),
                )
            )

        global_state = random.getstate()
        with patch.dict(PHASE_REGISTRY, {"capture_randomness": capture_randomness}):
            GameEngine(
                _config(game_id="unique-game-a", random_seed=123), players
            ).play()
            GameEngine(
                _config(game_id="unique-game-b", random_seed=123), players
            ).play()

        self.assertEqual(draws[0], draws[1])
        self.assertEqual(random.getstate(), global_state)

    def test_game_id_remains_the_default_seed(self) -> None:
        players = [_player("AAAA"), _player("BBBB")]
        draws: list[float] = []

        def capture_randomness(context):
            draws.append(context.rng.random())

        with patch.dict(PHASE_REGISTRY, {"capture_randomness": capture_randomness}):
            GameEngine(_config(game_id="legacy-game"), players).play()

        expected = random.Random("legacy-game").random()
        self.assertEqual(draws, [expected])


if __name__ == "__main__":
    unittest.main()

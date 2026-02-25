import json
import logging
import os
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List

from .history import History
from .player import Player, PlayerConfig
from .round import Round, RoundContext
from .round_phases import PHASE_REGISTRY


@dataclass
class GameConfig:
    """
    Configuration for the game

    Args:
        num_players: Expected number of players (validated against player configs)
        num_rounds: Number of rounds to play (final round determined by index)
        phases: Default ordered list of phase names (must be keys in PHASE_REGISTRY)
        logs_dir: Directory to save logs
        rules_prompt: Prompt with the rules of the game
        round_phase_overrides: Per-round phase overrides keyed by round number
        log_prefix: Optional prefix for log filenames (default: "gameplay")
        game_id: Optional game ID for reproducibility
    """

    num_players: int
    num_rounds: int
    phases: list[str]
    logs_dir: str
    rules_prompt: str
    round_phase_overrides: dict[int, list[str]] = field(default_factory=dict)
    log_prefix: str = field(default="gameplay")
    game_id: str | None = field(default=None)


class GameEngine:
    def __init__(
        self,
        game_config: GameConfig,
        player_configs: list[PlayerConfig],
    ):
        """
        Initialize the GameEngine

        Args:
            game_config: GameConfig object
            player_configs: List of PlayerConfig objects
        """
        self.game_config = game_config
        self.player_configs = player_configs
        self.logger = logging.getLogger(__name__)
        self._validate_config()
        self.players = self._initialize_players()
        self.history = History()

    def _validate_config(self) -> None:
        """Validate game config against player configs and phase registry."""
        cfg = self.game_config

        if cfg.num_players != len(self.player_configs):
            raise ValueError(
                f"num_players ({cfg.num_players}) does not match "
                f"player config count ({len(self.player_configs)})"
            )

        if cfg.num_rounds < 1:
            raise ValueError(f"num_rounds must be >= 1, got {cfg.num_rounds}")

        # TODO: Relax this constraint when non-elimination rounds are added
        if cfg.num_rounds > cfg.num_players - 1:
            raise ValueError(
                f"num_rounds ({cfg.num_rounds}) must be <= num_players - 1 "
                f"({cfg.num_players - 1})"
            )

        # Validate default phase names
        for name in cfg.phases:
            if name not in PHASE_REGISTRY:
                raise ValueError(
                    f"Unknown phase '{name}' in default phases. "
                    f"Valid phases: {list(PHASE_REGISTRY.keys())}"
                )

        # Validate round overrides
        for round_idx, phase_names in cfg.round_phase_overrides.items():
            if round_idx < 1 or round_idx > cfg.num_rounds:
                raise ValueError(
                    f"Round override index {round_idx} is out of range "
                    f"[1, {cfg.num_rounds}]"
                )
            for name in phase_names:
                if name not in PHASE_REGISTRY:
                    raise ValueError(
                        f"Unknown phase '{name}' in override for round {round_idx}. "
                        f"Valid phases: {list(PHASE_REGISTRY.keys())}"
                    )

    def _get_phases_for_round(self, round_index: int) -> List[callable]:
        """
        Get the phase callables for a given round.

        Uses round-specific overrides if configured, otherwise the default phases.

        Args:
            round_index: 1-indexed round number

        Returns:
            List of phase callables
        """
        phase_names = self.game_config.round_phase_overrides.get(
            round_index, self.game_config.phases
        )
        return [PHASE_REGISTRY[name] for name in phase_names]

    def _initialize_players(self) -> List[Player]:
        """
        Initialize the players (Player class) from the player configurations

        Args:
            None

        Returns:
            List[Player]: List of Player objects
        """
        # Initialize an empty list of players
        players: List[Player] = []

        # Initialize the players from the player configurations
        for player_config in self.player_configs:
            player = Player(player_config)
            players.append(player)

        return players

    def _create_round_context(
        self,
        round_index: int,
        final_round: bool,
        players: List[Player],
        active_player_ids: List[str],
    ) -> RoundContext:
        """
        Create the round context

        Args:
            round_index: The index of the round
            final_round: Whether this is the final round
            players: List of Player objects
            active_player_ids: List of active player IDs

        Returns:
            RoundContext: The round context
        """

        # Construct list of all player IDs
        all_player_ids = [p.config.player_id for p in players]

        # Construct list of eliminated players
        eliminated_player_ids = [
            pid for pid in all_player_ids if pid not in active_player_ids
        ]

        # Create the round context
        return RoundContext(
            round_index=round_index,
            final_round=final_round,
            players=players,
            active_player_ids=active_player_ids,
            eliminated_player_ids=eliminated_player_ids,
            logger=self.logger,
            history=self.history,
            rules_prompt=self.game_config.rules_prompt,
        )

    def play(self):
        """
        Play the game

        Args:
            None

        Returns:
            None
        """
        # Resolve game ID (use provided value for reproduction, else generate fresh)
        game_id = self.game_config.game_id or str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Seed random draws from the game ID for partial reproducibility
        random.seed(game_id)

        # Log start of game
        self.logger.info(f"Starting game {game_id} ({timestamp})")

        self.logger.info(f"{self.game_config.num_players} players")

        # Store original set of player IDs in game history
        active_player_ids = [player.config.player_id for player in self.players]
        self.history.player_ids = active_player_ids

        num_rounds = self.game_config.num_rounds

        try:
            for round_index in range(1, num_rounds + 1):
                final_round = round_index == num_rounds
                outcome = "Winning" if final_round else "Eliminated"

                self.logger.info(f"Round {round_index}")

                # Resolve phases for this round (override or default)
                phases = self._get_phases_for_round(round_index)

                # Create round context and play
                round_context = self._create_round_context(
                    round_index=round_index,
                    final_round=final_round,
                    players=self.players,
                    active_player_ids=active_player_ids,
                )
                round = Round(
                    context=round_context,
                    phases=phases,
                )
                round.play()

                self.logger.info(f"Vote tally: {round_context.votes['vote_tally']}")

                self.logger.info(
                    f"{outcome} player: {round_context.votes['selected_player']}"
                )

                # Remove eliminated player from active player IDs
                if not final_round:
                    active_player_ids = [
                        pid
                        for pid in active_player_ids
                        if pid != round_context.votes["selected_player"]
                    ]
                    self.logger.info(f"Next round players: {active_player_ids}")

        except Exception as exc:
            self.logger.error("Game %s failed: %s", game_id, exc)
            self._write_log(game_id, timestamp, status="failed", error=str(exc))
            raise

        self._write_log(game_id, timestamp, status="completed", error=None)

    def _compute_stats(self) -> dict:
        """
        Compute game statistics from the event history.

        All metrics are derived post-hoc from event data:
          - vote_parse_failures: events flagged with metadata["vote_parse_failed"]
          - reasoning_extraction_failures: non-narrator events with reasoning=None
          - cost: sum of metadata["cost"] per player
          - usage: token counts and cost_retrieval_failures per player

        Returns:
            dict with vote_parse_failures, reasoning_extraction_failures, cost, usage
        """
        vpf_by_player: dict[str, int] = {}
        ref_by_player: dict[str, int] = {}
        cost_by_player: dict[str, float] = {}
        usage_by_player: dict[str, dict[str, int]] = {}

        for round_log in self.history.rounds.values():
            for event in round_log.events:
                if event.role == "narrator":
                    continue
                player_id = event.role.removeprefix("player ")
                meta = event.metadata or {}

                if meta.get("vote_parse_failed"):
                    vpf_by_player[player_id] = vpf_by_player.get(player_id, 0) + 1

                if event.reasoning is None:
                    ref_by_player[player_id] = ref_by_player.get(player_id, 0) + 1

                if "cost" in meta:
                    cost_by_player[player_id] = (
                        cost_by_player.get(player_id, 0.0) + meta["cost"]
                    )

                pu = usage_by_player.setdefault(
                    player_id,
                    {
                        "input_tokens": 0,
                        "completion_tokens": 0,
                        "reasoning_tokens": 0,
                        "total_tokens": 0,
                        "cost_retrieval_failures": 0,
                    },
                )
                pu["input_tokens"] += meta.get("input_tokens", 0)
                pu["completion_tokens"] += meta.get("completion_tokens", 0)
                pu["reasoning_tokens"] += meta.get("reasoning_tokens", 0)
                pu["total_tokens"] += meta.get("total_tokens", 0)
                if meta.get("cost_retrieval_failed"):
                    pu["cost_retrieval_failures"] += 1

        def _sum(key: str) -> int:
            return sum(p.get(key, 0) for p in usage_by_player.values())

        return {
            "vote_parse_failures": {
                "total": sum(vpf_by_player.values()),
                "by_player": vpf_by_player,
            },
            "reasoning_extraction_failures": {
                "total": sum(ref_by_player.values()),
                "by_player": ref_by_player,
            },
            "cost": {
                "total": sum(cost_by_player.values()),
                "by_player": cost_by_player,
            },
            "usage": {
                "by_player": usage_by_player,
                "input_tokens": _sum("input_tokens"),
                "completion_tokens": _sum("completion_tokens"),
                "reasoning_tokens": _sum("reasoning_tokens"),
                "total_tokens": _sum("total_tokens"),
                "cost_retrieval_failures": _sum("cost_retrieval_failures"),
            },
        }

    def _write_log(
        self,
        game_id: str,
        timestamp: str,
        status: str,
        error: str | None,
    ) -> None:
        os.makedirs(self.game_config.logs_dir, exist_ok=True)

        output_path = os.path.join(
            self.game_config.logs_dir,
            f"{self.game_config.log_prefix}_{game_id}.json",
        )
        with open(output_path, "w") as f:
            output = {
                "game": {
                    "id": game_id,
                    "timestamp": timestamp,
                    "num_players": self.game_config.num_players,
                    "num_rounds": self.game_config.num_rounds,
                    "log_prefix": self.game_config.log_prefix,
                    "phases": self.game_config.phases,
                    "round_phase_overrides": {
                        str(k): v
                        for k, v in self.game_config.round_phase_overrides.items()
                    },
                    "rules_prompt": self.game_config.rules_prompt,
                    "status": status,
                    "error": error,
                },
                "players": {
                    p.config.player_id: {
                        k: v for k, v in asdict(p.config).items() if k != "api_key"
                    }
                    for p in self.players
                },
                "stats": self._compute_stats(),
                "history": self.history.to_dict(),
            }
            json.dump(output, f, indent=2)
        self.logger.info("Wrote game history to %s", output_path)

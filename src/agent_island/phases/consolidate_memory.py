from ..round import RoundContext
from .common import permute_player_ids


def phase_consolidate_memory(context: RoundContext) -> None:
    """
    Each player consolidates events into memory according to their
    configured strategy.

    Runs for all players (active and eliminated) to ensure uniform
    context management.

    Args:
        context: The round context

    Returns:
        None
    """
    all_player_ids = context.active_player_ids + context.eliminated_player_ids

    for player_id in permute_player_ids(all_player_ids):
        player = next(
            player for player in context.players if player.config.player_id == player_id
        )

        context.logger.info(f"Player {player_id} is consolidating memory")
        player.memory.consolidate(
            player=player,
            history=context.history,
            round_index=context.round_index,
            rules_prompt=context.rules_prompt,
        )



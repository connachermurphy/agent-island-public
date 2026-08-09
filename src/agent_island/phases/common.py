import random


def permute_player_ids(
    player_ids: list[str], rng: random.Random | None = None
) -> list[str]:
    """
    Permute the player IDs in a random order.

    Args:
        players_ids: The list of player IDs to permute

    Returns:
        list[str]: The permuted player IDs
    """
    generator = rng if rng is not None else random
    return generator.sample(player_ids, k=len(player_ids))

from ..round import RoundContext


def phase_elimination(context: RoundContext) -> None:
    """
    Eliminate the player selected by the vote phase.

    Reads ``context.votes["selected_player"]`` (set by :func:`phase_votes`)
    and removes that player from ``context.active_player_ids``.

    Args:
        context: The round context

    Returns:
        None
    """
    if context.round_type == "final":
        raise RuntimeError("phase_elimination must not run in a 'final' round")

    selected = context.votes.get("selected_player")
    if selected is None:
        context.logger.warning(
            "No selected player found in votes; skipping elimination"
        )
        return

    if selected not in context.active_player_ids:
        context.logger.warning(
            "Selected player %s is not in active players; skipping elimination",
            selected,
        )
        return

    context.active_player_ids.remove(selected)
    context.eliminated_player_ids.append(selected)

    context.logger.info("Player %s has been eliminated", selected)

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Round {context.round_index} Elimination",
        content=f"Player {selected} has been eliminated.",
        visibility=context.history.player_ids,
        active_visibility=context.history.player_ids.copy(),
    )

from ..round import RoundContext
from .common import permute_player_ids


def phase_pitches(context: RoundContext) -> None:
    """
    Conduct a round phase of pitches

    Args:
        context: The round context

    Returns:
        None
    """

    # The objective for the pitch depends on the round
    if context.final_round:
        outcome = "win the game"
        pitch_announcement = (
            "It is time for final pitches. "
            "Each player will make their case for why they should win the game."
        )
    else:
        outcome = "advance to the next round"
        pitch_announcement = (
            "It is time for pitches. "
            "Each player will make their case for why they should "
            "advance to the next round."
        )

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Round {context.round_index} Pitches",
        content=pitch_announcement,
        visibility=context.history.player_ids,
        active_visibility=context.history.player_ids.copy(),
    )

    # Permute the player IDs to avoid order effects
    for player_id in permute_player_ids(context.active_player_ids):
        # Get the player object from the player ID
        player = next(
            player for player in context.players if player.config.player_id == player_id
        )

        # Elicit the pitch from the player
        context.logger.info(f"Player {player.config.player_id} is making their pitch")
        memory_context = player.memory.render()
        visible_events = context.history.render_for_player(player.config.player_id)
        if memory_context:
            visible_events = f"{memory_context}\n\n{visible_events}"
        action = (
            f"Please make your pitch for why you should {outcome}. "
            f"The remaining players are: {context.active_player_ids}. "
            f"Other players will be able to see your pitch."
        )

        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}
        """

        response = player.free_response(
            system_prompt=system_prompt,
            context=visible_events,
            action=action,
        )

        context.history.add_event(
            round_index=context.round_index,
            heading=f"Player {player.config.player_id}'s Pitch",
            role=f"player {player.config.player_id}",
            prompt=f"{system_prompt}\n\n{visible_events}\n\n{action}",
            content=response.text,
            reasoning=response.reasoning,
            metadata=response.metadata,
            visibility=context.history.player_ids,
            active_visibility=context.history.player_ids.copy(),
        )

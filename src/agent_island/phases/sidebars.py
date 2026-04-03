from ..round import RoundContext
from .common import permute_player_ids


def phase_sidebars(
    context: RoundContext,
    *,
    num_rounds: int = 1,
    messages_per_exchange: int = 2,
) -> None:
    """
    Conduct a round of private 1-on-1 sidebar conversations.

    Each active player selects one other active player to have a
    private conversation with. For every (initiator, target) pair
    the two players exchange messages visible only to them.

    Args:
        context: The round context
        num_rounds: Number of back-and-forth rounds per sidebar
        messages_per_exchange: Total messages exchanged per round
            (alternating between the two players)

    Returns:
        None
    """
    active = context.active_player_ids
    if len(active) < 2:
        context.logger.info("Not enough active players for sidebars")
        return

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Round {context.round_index} Sidebars",
        content=(
            "It is time for sidebar conversations. "
            "Each player will choose one other player for a "
            "private 1-on-1 conversation."
        ),
        visibility=context.history.player_ids,
        active_visibility=context.history.player_ids.copy(),
    )

    # --- Selection step ---
    selections: dict[str, str] = {}  # initiator -> target

    for player_id in permute_player_ids(active):
        player = next(
            p for p in context.players
            if p.config.player_id == player_id
        )

        candidates = permute_player_ids(
            [pid for pid in active if pid != player_id]
        )

        memory_context = player.memory.render()
        visible_events = context.history.render_for_player(player_id)
        if memory_context:
            visible_events = f"{memory_context}\n\n{visible_events}"

        action = (
            "Choose one player for a private sidebar conversation. "
            f"Choose from: {candidates}."
        )

        llm_instructions = (
            "Your choice must be of the following format: "
            "'<choice>PLAYER ID</choice>'.\n\n"
            "Example: '<choice>X</choice>' is valid, but "
            "'<choice>[X]</choice>' and '<choice>XY</choice>' are "
            "not. Here, we assume X and Y are player IDs."
        )

        system_prompt = f"""
{context.rules_prompt}

<character>
{player.config.character_prompt}
</character>
"""

        context.logger.info(
            "Player %s is choosing a sidebar partner", player_id
        )

        response = player.choice_response(
            system_prompt=system_prompt,
            context=visible_events,
            options=candidates,
            action=action,
            llm_instructions=llm_instructions,
        )

        if response.selected:
            selections[player_id] = response.selected
        else:
            context.logger.warning(
                "Sidebar selection failed for player %s", player_id
            )

        metadata = dict(response.metadata) if response.metadata else {}
        metadata["sidebar_selection"] = response.selected

        context.history.add_event(
            round_index=context.round_index,
            heading=f"Player {player_id}'s Sidebar Selection",
            role=f"player {player_id}",
            prompt=(
                f"{system_prompt}\n\n{visible_events}"
                f"\n\n{action}\n\n{llm_instructions}"
            ),
            content=response.text,
            reasoning=response.reasoning,
            metadata=metadata or None,
            visibility=[player_id],
            active_visibility=[player_id],
        )

    # --- Conversation step ---
    for initiator_id, target_id in selections.items():
        _run_sidebar(
            context=context,
            initiator_id=initiator_id,
            target_id=target_id,
            num_rounds=num_rounds,
            messages_per_exchange=messages_per_exchange,
        )


def _run_sidebar(
    context: RoundContext,
    initiator_id: str,
    target_id: str,
    num_rounds: int,
    messages_per_exchange: int,
) -> None:
    """Run a private sidebar conversation between two players."""
    pair_visibility = [initiator_id, target_id]

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Sidebar: {initiator_id} & {target_id}",
        content=(
            f"Player {initiator_id} has initiated a private "
            f"sidebar conversation with Player {target_id}."
        ),
        visibility=pair_visibility,
        active_visibility=pair_visibility.copy(),
    )

    # Alternate speakers, starting with the initiator
    speakers = [initiator_id, target_id]

    for rnd in range(num_rounds):
        for msg_idx in range(messages_per_exchange):
            speaker_id = speakers[msg_idx % 2]
            listener_id = speakers[(msg_idx + 1) % 2]

            player = next(
                p for p in context.players
                if p.config.player_id == speaker_id
            )

            memory_context = player.memory.render()
            visible_events = context.history.render_for_player(
                speaker_id
            )
            if memory_context:
                visible_events = (
                    f"{memory_context}\n\n{visible_events}"
                )

            action = (
                f"You are in a private sidebar conversation "
                f"with Player {listener_id} "
                f"(message {msg_idx + 1}/{messages_per_exchange}"
                f", round {rnd + 1}/{num_rounds}). "
                f"Only you and Player {listener_id} can see "
                f"this conversation. Say what you'd like."
            )

            system_prompt = f"""
{context.rules_prompt}

<character>
{player.config.character_prompt}
</character>
"""

            context.logger.info(
                "Sidebar %s & %s: round %d, message %d (%s)",
                initiator_id,
                target_id,
                rnd + 1,
                msg_idx + 1,
                speaker_id,
            )

            response = player.free_response(
                system_prompt=system_prompt,
                context=visible_events,
                action=action,
            )

            context.history.add_event(
                round_index=context.round_index,
                heading=(
                    f"Sidebar {initiator_id} & {target_id}: "
                    f"{speaker_id}"
                ),
                role=f"player {speaker_id}",
                prompt=(
                    f"{system_prompt}\n\n{visible_events}"
                    f"\n\n{action}"
                ),
                content=response.text,
                reasoning=response.reasoning,
                metadata=response.metadata,
                visibility=pair_visibility,
                active_visibility=pair_visibility.copy(),
            )

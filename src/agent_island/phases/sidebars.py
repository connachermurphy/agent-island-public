from ..round import RoundContext
from .common import permute_player_ids


def phase_sidebars(
    context: RoundContext,
    *,
    num_exchanges: int = 1,
    messages_per_exchange: int = 2,
) -> None:
    """
    Conduct private 1-on-1 sidebar conversations.

    For each exchange, every active player selects a partner and
    immediately has a private conversation with them before the
    next player selects.

    Args:
        context: The round context
        num_exchanges: Number of select-and-converse cycles
        messages_per_exchange: Total messages exchanged per
            conversation (alternating between the two players)

    Returns:
        None
    """
    active = context.active_player_ids
    if len(active) < 2:
        context.logger.info("Not enough active players for sidebars")
        return

    if num_exchanges == 1:
        exchange_text = (
            "Each player will initiate one private conversation, "
            f"consisting of {messages_per_exchange} "
            f"{'message' if messages_per_exchange == 1 else 'messages'}."
        )
    else:
        exchange_text = (
            f"There will be {num_exchanges} exchanges. "
            "Each exchange, every player will initiate a private conversation, "
            f"consisting of {messages_per_exchange} "
            f"{'message' if messages_per_exchange == 1 else 'messages'}."
        )

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Round {context.round_index} Sidebars",
        content=(
            "It is time for sidebar conversations. "
            "Each player will choose one other player for a "
            f"private 1-on-1 conversation. {exchange_text}"
        ),
        visibility=context.history.player_ids,
        active_visibility=context.history.player_ids.copy(),
    )

    for exchange in range(num_exchanges):
        for player_id in permute_player_ids(active):
            player = next(p for p in context.players if p.config.player_id == player_id)

            candidates = permute_player_ids([pid for pid in active if pid != player_id])

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
                "Player %s is choosing a sidebar partner (exchange %d/%d)",
                player_id,
                exchange + 1,
                num_exchanges,
            )

            response = player.choice_response(
                system_prompt=system_prompt,
                context=visible_events,
                options=candidates,
                action=action,
                llm_instructions=llm_instructions,
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

            if response.selected:
                _run_sidebar(
                    context=context,
                    initiator_id=player_id,
                    target_id=response.selected,
                    messages_per_exchange=messages_per_exchange,
                )
            else:
                context.logger.warning(
                    "Sidebar selection failed for player %s", player_id
                )


def _run_sidebar(
    context: RoundContext,
    initiator_id: str,
    target_id: str,
    messages_per_exchange: int,
) -> None:
    """Run a private sidebar conversation between two players."""
    pair_visibility = [initiator_id, target_id]

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Sidebar between {initiator_id} & {target_id}",
        content=(
            f"Player {initiator_id} has initiated a private "
            f"sidebar conversation with Player {target_id}."
        ),
        visibility=pair_visibility,
        active_visibility=pair_visibility.copy(),
    )

    # Alternate speakers, starting with the initiator
    speakers = [initiator_id, target_id]

    for msg_idx in range(messages_per_exchange):
        speaker_id = speakers[msg_idx % 2]
        listener_id = speakers[(msg_idx + 1) % 2]

        player = next(p for p in context.players if p.config.player_id == speaker_id)

        memory_context = player.memory.render()
        visible_events = context.history.render_for_player(speaker_id)
        if memory_context:
            visible_events = f"{memory_context}\n\n{visible_events}"

        is_last = msg_idx == messages_per_exchange - 1
        if is_last:
            message_note = (
                f"This is the final message "
                f"({msg_idx + 1}/{messages_per_exchange}). "
                f"No more messages will be sent after this."
            )
        else:
            message_note = f"This is message {msg_idx + 1}/{messages_per_exchange}."

        action = (
            f"You are in a private sidebar conversation "
            f"with Player {listener_id}. "
            f"Only you and Player {listener_id} can see "
            f"this conversation. "
            f"{message_note} "
            f"Please send a message."
        )

        system_prompt = f"""
{context.rules_prompt}

<character>
{player.config.character_prompt}
</character>
"""

        context.logger.info(
            "Sidebar between %s & %s: Player %s's message (%d/%d)",
            initiator_id,
            target_id,
            speaker_id,
            msg_idx + 1,
            messages_per_exchange,
        )

        response = player.free_response(
            system_prompt=system_prompt,
            context=visible_events,
            action=action,
        )

        context.history.add_event(
            round_index=context.round_index,
            heading=(
                f"Sidebar between {initiator_id} & {target_id}. "
                f"Player {speaker_id}'s message"
            ),
            role=f"player {speaker_id}",
            prompt=(f"{system_prompt}\n\n{visible_events}\n\n{action}"),
            content=response.text,
            reasoning=response.reasoning,
            metadata=response.metadata,
            visibility=pair_visibility,
            active_visibility=pair_visibility.copy(),
        )

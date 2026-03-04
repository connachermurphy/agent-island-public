import random

from ..round import RoundContext
from .common import permute_player_ids


def phase_votes(context: RoundContext) -> None:
    """
    Conduct a round phase of votes

    Args:
        context: The round context

    Returns:
        None
    """
    # Initialize the vote tally
    vote_tally: dict[str, int] = {}

    # The outcome for the vote depends on the round
    if context.final_round:
        outcome_verb = "wins"
        vote_instruction = "Vote for one player to win."
        voters = context.eliminated_player_ids
        vote_announcement = (
            "It is time for the final vote. "
            "Eliminated players will vote for one of the remaining "
            "players to win the game. "
            "Votes are private."
        )
    else:
        outcome_verb = "is eliminated"
        vote_instruction = "Vote to eliminate one player."
        voters = context.active_player_ids
        vote_announcement = (
            "It is time to vote. "
            "Players will vote to eliminate one player from the game. "
            "Votes are private."
        )

    context.history.narrate(
        round_index=context.round_index,
        heading=f"Round {context.round_index} Vote",
        content=vote_announcement,
        visibility=context.history.player_ids,
        active_visibility=context.history.player_ids.copy(),
    )

    # Construct list of candidates for the vote
    candidates = context.active_player_ids

    # Permute the player IDs to avoid order effects
    for voter in permute_player_ids(voters):
        # Get the player object from the voter ID
        player = next(
            player for player in context.players if player.config.player_id == voter
        )

        # Elicit the vote from the player
        context.logger.info(f"Player {voter} is voting")
        memory_context = player.memory.render()
        visible_events = context.history.render_for_player(voter)
        if memory_context:
            visible_events = f"{memory_context}\n\n{visible_events}"

        # Permute candidates at the voter level to avoid order effects
        # Exclude the active voter from the candidates
        candidates_for_voter = permute_player_ids([c for c in candidates if c != voter])

        action = (
            f"{vote_instruction} You cannot vote for yourself. "
            f"Vote for one of: {candidates_for_voter}. "
            f"After you have voted, please provide an explanation for your vote. "
            f"Other players will not be able to see your vote or explanation."
        )

        llm_instructions = """Your vote must be of the following format:
'<vote>PLAYER ID</vote>', or it will be ignored.

Example: '<vote>X</vote>' is a valid vote, but
'<vote>[X]</vote>' and '<vote>XY</vote>' are not.
Here, we assume X and Y are player IDs."""

        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}
"""

        response = player.choice_response(
            system_prompt=system_prompt,
            context=visible_events,
            options=candidates_for_voter,
            action=action,
            llm_instructions=llm_instructions,
        )

        if response.selected:
            vote_tally[response.selected] = vote_tally.get(response.selected, 0) + 1
        else:
            context.logger.warning(
                "Vote parsing failed for player %s", player.config.player_id
            )

        metadata = dict(response.metadata) if response.metadata else {}
        metadata["vote"] = response.selected

        context.history.add_event(
            round_index=context.round_index,
            heading=f"Player {player.config.player_id}'s Vote",
            role=f"player {player.config.player_id}",
            prompt=f"{system_prompt}\n\n{action}\n\n{llm_instructions}\n\n{visible_events}",
            content=response.text,
            reasoning=response.reasoning,
            metadata=metadata or None,
            visibility=[player.config.player_id],
            active_visibility=[player.config.player_id],
        )

        context.logger.debug(
            "Player %s voted for %s", player.config.player_id, response.selected
        )

    context.votes["vote_tally"] = vote_tally
    context.logger.info(f"Final vote tally: {vote_tally}")

    # Build tally string sorted by descending vote count, including 0-vote candidates
    tally_str = ", ".join(
        f"{p}: {vote_tally.get(p, 0)}"
        for p in sorted(candidates, key=lambda p: -vote_tally.get(p, 0))
    )

    # Find selected player
    if not vote_tally:
        # If no valid votes, randomly select a player
        selected_player_id = random.choice(candidates)
        context.logger.info(
            f"No valid votes found. Randomly selecting Player {selected_player_id}"
        )
        context.history.narrate(
            round_index=context.round_index,
            heading=f"Round {context.round_index} Vote Results",
            content=(
                f"No valid votes found, so we are randomly "
                f"selecting a player. Player "
                f"{selected_player_id} {outcome_verb}."
                f" Vote tally: {tally_str}."
            ),
            visibility=context.history.player_ids,
            active_visibility=context.history.player_ids.copy(),
        )
    else:
        # If there are valid votes, find the player with the most votes
        max_votes = max(vote_tally.values())
        tied_players = [p for p, v in vote_tally.items() if v == max_votes]

        # If there is only one player with the most votes, select that player
        if len(tied_players) == 1:
            selected_player_id = tied_players[0]
            context.logger.info(
                f"Player {selected_player_id} {outcome_verb} with {max_votes} vote(s)"
            )
            context.history.narrate(
                round_index=context.round_index,
                heading=f"Round {context.round_index} Vote Results",
                content=(
                    f"Player {selected_player_id} "
                    f"{outcome_verb} with "
                    f"{max_votes} vote(s)."
                    f" Vote tally: {tally_str}."
                ),
                visibility=context.history.player_ids,
                active_visibility=context.history.player_ids.copy(),
            )

        # If there is a tie, randomly select a player from the tied players
        else:
            selected_player_id = random.choice(tied_players)
            context.logger.info(
                f"Tie between {tied_players} with "
                f"{max_votes} vote(s). Randomly selecting "
                f"Player {selected_player_id} "
                f"{outcome_verb}."
            )
            context.history.narrate(
                round_index=context.round_index,
                heading=f"Round {context.round_index} Vote Results",
                content=(
                    f"There is a tie between "
                    f"{tied_players} with "
                    f"{max_votes} vote(s), so we are "
                    f"randomly selecting one player. "
                    f"Player {selected_player_id} "
                    f"{outcome_verb}."
                    f" Vote tally: {tally_str}."
                ),
                visibility=context.history.player_ids,
                active_visibility=context.history.player_ids.copy(),
            )

    # Persist vote results to the round log
    context.history.rounds[context.round_index].vote_tally = vote_tally
    context.history.rounds[context.round_index].selected_player = selected_player_id

    context.votes["selected_player"] = selected_player_id

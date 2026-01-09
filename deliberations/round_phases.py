import random

from round import RoundContext


def permute_player_ids(player_ids: list[str]) -> list[str]:
    """
    Permute the player IDs in a random order.

    Args:
        players_ids: The list of player IDs to permute

    Returns:
        list[str]: The permuted player IDs
    """
    return random.sample(player_ids, k=len(player_ids))


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
    else:
        outcome = "advance to the next round"

    # Permute the player IDs to avoid order effects
    for player_id in permute_player_ids(context.active_player_ids):
        # Get the player object from the player ID
        player = next(
            player for player in context.players if player.config.player_id == player_id
        )

        # Elicit the pitch from the player
        context.logger.info(f"Player {player.config.player_id} is making their pitch")
        visible_events = context.history.render_for_player(player.config.player_id)
        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}

Please make your pitch for why you should {outcome}.

The remaining players are: {context.active_player_ids}.

Other players will be able to see your pitch.
        """

        response = player.respond(
            system_prompt=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": visible_events,
                },
            ],
        )

        context.history.add_event(
            round_index=context.round_index,
            heading=f"Player {player.config.player_id}'s Pitch",
            role=f"player {player.config.player_id}",
            prompt=f"{system_prompt}\n\n{visible_events}",
            content=response.text,
            reasoning=response.reasoning,
            response=response,
            visibility=context.history.player_ids,
        )


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
        outcome = "win"
        outcome_verb = "wins"
        voters = context.eliminated_player_ids
    else:
        outcome = "eliminate"
        outcome_verb = "is eliminated"
        voters = context.active_player_ids

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
        visible_events = context.history.render_for_player(voter)

        # Permute candidates at the voter level to avoid order effects
        # Exclude the active voter from the candidates
        candidates_for_voter = permute_player_ids([c for c in candidates if c != voter])

        system_prompt = f"""
            {context.rules_prompt}

            {player.config.character_prompt}

            Please vote for one player to {outcome}. You cannot vote for yourself.

            You must vote for one of the following players: {candidates_for_voter}.

            Your vote must be of the following format: '<vote>[PLAYER ID]</vote>', or it will be ignored.

            Example: '<vote>X</vote>' is a valid vote, but '<vote>[X]</vote>' and '<vote>XY</vote>' are not.

            After you have voted, please provide an explanation for your vote.

            Other players will not be able to see your vote or explanation.
        """

        response = player.respond(
            system_prompt=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": visible_events,
                },
            ],
        )

        context.history.add_event(
            round_index=context.round_index,
            heading=f"Player {player.config.player_id}'s Vote",
            role=f"player {player.config.player_id}",
            prompt=f"{system_prompt}\n\n{visible_events}",
            content=response.text,
            reasoning=response.reasoning,
            response=response,
            visibility=[player.config.player_id],
        )

        # Extract the vote from the player response
        vote = player.extract_vote(response.text, candidates_for_voter)
        if vote:
            vote_tally[vote] = vote_tally.get(vote, 0) + 1

        context.logger.info(f"Player {player.config.player_id} voted for {vote}")

    context.votes["vote_tally"] = vote_tally
    context.logger.info(f"Final vote tally: {vote_tally}")

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
            content=f"No valid votes found, so we are randomly selecting a player. Player {selected_player_id} {outcome_verb}.",
            visibility=context.history.player_ids,
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
                content=f"Player {selected_player_id} {outcome_verb} with {max_votes} vote(s).",
                visibility=context.history.player_ids,
            )

        # If there is a tie, randomly select a player from the tied players
        else:
            selected_player_id = random.choice(tied_players)
            context.logger.info(
                f"Tie between {tied_players} with {max_votes} vote(s). Randomly selecting Player {selected_player_id} {outcome_verb}."
            )
            context.history.narrate(
                round_index=context.round_index,
                heading=f"Round {context.round_index} Vote Results",
                content=f"There is a tie between {tied_players} with {max_votes} vote(s), so we are randomly selecting one player. Player {selected_player_id} {outcome_verb}.",
                visibility=context.history.player_ids,
            )

    context.votes["selected_player"] = selected_player_id

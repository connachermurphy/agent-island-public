import random

from round import RoundContext


def phase_pitches(context: RoundContext) -> None:
    if context.final_round:
        outcome = "win the game"
    else:
        outcome = "advance to the next round"

    for player_id in context.active_player_ids:
        player = next(
            player for player in context.players if player.config.player_id == player_id
        )

        context.logger.info(f"Player {player.config.player_id} is making their pitch")
        visible_events = context.history.render_for_player(player.config.player_id)
        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}

Please make your pitch for why you should {outcome}. Please limit your response to 25 words at most.

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
            response=response,
            visibility=context.history.player_ids,
        )


def phase_votes(context: RoundContext) -> None:
    vote_tally: dict[str, int] = {}

    if context.final_round:
        outcome = "win"
        outcome_verb = "wins"
        voters = context.eliminated_player_ids
    else:
        outcome = "eliminate"
        outcome_verb = "is eliminated"
        voters = context.active_player_ids

    candidates = context.active_player_ids

    for voter in voters:
        player = next(
            player for player in context.players if player.config.player_id == voter
        )
        context.logger.info(f"Player {voter} is voting")
        visible_events = context.history.render_for_player(voter)

        candidates_for_voter = [c for c in candidates if c != voter]

        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}

Please vote for one player to {outcome}. You cannot vote for yourself.

You must vote for one of the following players: {candidates_for_voter}.

Your vote must be of the following format: '<vote>[PLAYER ID]</vote>', or it will be ignored.

Example: '<vote>X</vote>' is a valid vote, but '<vote>[X]</vote>' and '<vote>XY</vote>' are not.

After you have voted, please provide your reasoning for your vote. Please limit your reasoning to 25 words at most.

Other players will not be able to see your vote or reasoning.
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
            response=response,
            visibility=[player.config.player_id],
        )

        vote = player.extract_vote(response.text, candidates_for_voter)
        if vote:
            vote_tally[vote] = vote_tally.get(vote, 0) + 1

        context.logger.info(f"Player {player.config.player_id} voted for {vote}")
        context.logger.info(f"Running vote tally: {vote_tally}")

    context.votes["vote_tally"] = vote_tally
    context.logger.info(f"Final vote tally: {vote_tally}")

    # Find selected player
    if not vote_tally:
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
        max_votes = max(vote_tally.values())
        tied_players = [p for p, v in vote_tally.items() if v == max_votes]
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

import random

from round import RoundContext


def phase_pitches(context: RoundContext) -> None:
    for player in context.players:
        context.logger.info(f"Player {player.config.player_id} is making their pitch")
        visible_events = context.history.render_for_player(player.config.player_id)
        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}

Please make your pitch for why you should advance to the next round. Please limit your response to 25 words at most.

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


# TODO: add phase_confessionals


def phase_votes(context: RoundContext) -> None:
    vote_tally: dict[str, int] = {}

    player_ids = context.player_ids()

    for player in context.players:
        players_ids_excluding_self = [
            pid for pid in player_ids if pid != player.config.player_id
        ]

        context.logger.info(f"Player {player.config.player_id} is voting")
        visible_events = context.history.render_for_player(player.config.player_id)
        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}

Please vote for one player to eliminate. You cannot vote for yourself. Please limit your response to 25 words at most.

You must vote for one of the following players: {players_ids_excluding_self}.

Your vote must be of the following format: '<vote>[PLAYER ID]</vote>', or it will be ignored.

Example: '<vote>X</vote>' is a valid vote, but '<vote>[X]</vote>' is not.

Other players will not be able to see your vote.
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

        vote = player.extract_vote(response.text, player_ids)
        if vote:
            vote_tally[vote] = vote_tally.get(vote, 0) + 1

        context.logger.info(f"Player {player.config.player_id} voted for {vote}")
        context.logger.info(f"Running vote tally: {vote_tally}")

    context.vote_tally = vote_tally
    context.logger.info(f"Final vote tally: {vote_tally}")

    # Find eliminated player
    if not vote_tally:
        selected_player_id = random.choice(player_ids)
        context.logger.info(
            f"No valid votes found. Randomly eliminating Player {selected_player_id}"
        )
    else:
        max_votes = max(vote_tally.values())
        tied_players = [p for p, v in vote_tally.items() if v == max_votes]
        if len(tied_players) == 1:
            selected_player_id = tied_players[0]
            context.logger.info(
                f"Player {selected_player_id} is eliminated with {max_votes} vote(s)"
            )
        else:
            selected_player_id = random.choice(tied_players)
            context.logger.info(
                f"Tie between {tied_players} with {max_votes}. Randomly eliminating Player {selected_player_id}"
            )

    context.eliminated_player = selected_player_id

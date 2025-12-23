from round import RoundContext


def phase_pitches(context: RoundContext) -> None:
    for player in context.players:
        context.logger.info(f"Player {player.config.player_id} is making their pitch")
        visible_events = context.history.render_for_player(player.config.player_id)
        system_prompt = f"""
{context.rules_prompt}

{player.config.character_prompt}
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

        full_prompt = f"""
{system_prompt}
{visible_events}
        """

        context.history.add_event(
            round_index=context.round_index,
            heading=f"Player {player.config.player_id}'s Pitch",
            role=f"player {player.config.player_id}",
            prompt=full_prompt,
            content=response.text,
            response=response,
            visibility=context.history.players,
        )


# TODO: add phase_votes
# TODO: add phase_confessionals

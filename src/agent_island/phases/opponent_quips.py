import re

from ..round import RoundContext
from .common import permute_player_ids

QUIP_RE = re.compile(
    r'<quip\s+player="([^"]+)">(.*?)</quip>', re.IGNORECASE | re.DOTALL
)


def phase_opponent_quips(context: RoundContext) -> None:
    """
    Each AI player writes a short, playful quip about every other player's
    play style. One event is emitted per quip for easy downstream filtering.
    """

    for player_id in permute_player_ids(context.history.player_ids):
        player = next(
            player for player in context.players if player.config.player_id == player_id
        )

        if player.config.player_type != "ai":
            continue

        context.logger.info(f"Player {player.config.player_id} is writing quips")

        system_prompt = f"""
{context.rules_prompt}

<character>
{player.config.character_prompt}
</character>
        """

        memory_context = player.memory.render()
        visible_events = context.history.render_for_player(player.config.player_id)
        if memory_context:
            visible_events = f"{memory_context}\n\n{visible_events}"

        opponent_ids = [
            pid for pid in context.history.player_ids if pid != player.config.player_id
        ]

        action = (
            "The game is over. Write a short, playful quip (1-2 sentences max) about "
            "each of your opponents' play styles. Be witty and specific — reference "
            "actual moves or moments from the game. Keep it lighthearted.\n\n"
            f"Your opponents are: {opponent_ids}.\n\n"
            "Format your response as:\n"
            "```\n"
            '<quip player="PLAYER_ID">Your quip here</quip>\n'
            "```\n"
            "Write one `<quip>` tag per opponent."
        )

        response = player.free_response(
            system_prompt=system_prompt,
            context=visible_events,
            action=action,
        )

        quips = QUIP_RE.findall(response.text)

        if not quips:
            context.logger.warning(
                f"Player {player.config.player_id}: no quips parsed from response"
            )
            continue

        if player.config.player_type == "human":
            prompt = action
        else:
            prompt = f"{system_prompt}\n\n{visible_events}\n\n{action}"

        for i, (target_id, quip_text) in enumerate(quips):
            context.history.add_event(
                round_index=context.round_index,
                heading=f"Player {player.config.player_id}'s quip about {target_id}",
                role=f"player {player.config.player_id}",
                prompt=prompt,
                content=quip_text.strip(),
                reasoning=response.reasoning if i == 0 else None,
                metadata={
                    **(response.metadata or {}),
                    "quip_target": target_id,
                    "quip_author": player.config.player_id,
                }
                if i == 0
                else {
                    "quip_target": target_id,
                    "quip_author": player.config.player_id,
                },
                visibility=context.history.player_ids,
                active_visibility=context.history.player_ids.copy(),
            )

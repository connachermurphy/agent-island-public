import unittest
from contextlib import contextmanager

from agent_island import GameConfig, GameEngine, Player, PlayerConfig
from agent_island.memory import create_strategy
from agent_island.player import (
    ChoiceResponse,
    FreeResponse,
    PlayerActionContext,
    PlayerActionKind,
    PlayerActionPhase,
)


class RecordingPlayer(Player):
    def __init__(self, player_id: str) -> None:
        self.config = PlayerConfig(
            player_id=player_id,
            character_prompt=f"You are {player_id}.",
        )
        self.memory = create_strategy("none")
        self.action_contexts: list[PlayerActionContext] = []

    @contextmanager
    def action_scope(self, action_context):
        self.action_contexts.append(action_context)
        yield

    def free_response(
        self, system_prompt, context, action, llm_instructions=""
    ) -> FreeResponse:
        del system_prompt, context, action, llm_instructions
        return FreeResponse(text="A concise response.")

    def choice_response(
        self, system_prompt, context, options, action, llm_instructions=""
    ) -> ChoiceResponse:
        del system_prompt, context, action, llm_instructions
        return ChoiceResponse(
            selected=options[0],
            text=f"<choice>{options[0]}</choice>",
        )


class PlayerActionContextTest(unittest.TestCase):
    def test_base_player_scope_is_backward_compatible(self) -> None:
        player = RecordingPlayer("ABCD")
        context = PlayerActionContext(
            round_index=1,
            round_type="elimination",
            phase=PlayerActionPhase.PITCH,
            action=PlayerActionKind.PITCH,
            scope_id="round-1:pitch:ABCD",
        )
        with Player.action_scope(player, context):
            pass

    def test_engine_emits_typed_scopes_for_model_facing_actions(self) -> None:
        players = [RecordingPlayer(player_id) for player_id in ("A", "B", "C")]
        engine = GameEngine(
            GameConfig(
                num_players=3,
                num_rounds=2,
                phases=["sidebars", "pitches", "votes", "elimination"],
                rules_prompt="Rules",
                round_phase_overrides={2: ["pitches", "votes"]},
                round_type_overrides={2: "final"},
                phase_config={
                    "sidebars": {"num_exchanges": 1, "messages_per_exchange": 2}
                },
                game_id="typed-action-context-test",
            ),
            players,
        )
        engine.play()

        contexts = [context for player in players for context in player.action_contexts]
        phases = {context.phase for context in contexts}
        self.assertEqual(
            phases,
            {
                PlayerActionPhase.SIDEBAR,
                PlayerActionPhase.PITCH,
                PlayerActionPhase.VOTE,
            },
        )
        sidebar_contexts = [
            context
            for context in contexts
            if context.phase == PlayerActionPhase.SIDEBAR
        ]
        self.assertTrue(sidebar_contexts)
        self.assertTrue(
            all(
                context.conversation_id == context.scope_id
                for context in sidebar_contexts
            )
        )
        selection = next(
            context
            for context in sidebar_contexts
            if context.action == PlayerActionKind.SIDEBAR_PARTNER_CHOICE
        )
        self.assertTrue(
            any(
                context.action == PlayerActionKind.SIDEBAR_MESSAGE
                and context.scope_id == selection.scope_id
                for context in sidebar_contexts
            )
        )
        self.assertTrue(
            all(
                context.conversation_id is None
                for context in contexts
                if context.phase in {PlayerActionPhase.PITCH, PlayerActionPhase.VOTE}
            )
        )


if __name__ == "__main__":
    unittest.main()

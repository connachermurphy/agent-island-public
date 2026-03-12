# Opponent Quips — Game Engine Changes

New `opponent_quips` phase for `agent-island-public`. Part of a larger feature
where AI players generate short, lighthearted quips about opponents' play styles
after the game ends.

The consuming app (`agent-island-app`) will schedule this phase in the final round
and decide which quips to surface to the user.

---

## Context

- Phases are functions `(RoundContext) -> None` registered in `PHASE_REGISTRY`.
- The closest analog is `phases/pitches.py` — iterates players, calls
  `free_response`, emits events with public visibility. Use it as a reference.
- The votes phase already narrates the winner (e.g., "Player X wins with 3
  vote(s)") before returning, so quip authors will see the outcome in their
  visible history. No changes to the votes phase are needed.
- There are no existing tests in this repo.

---

## 1. New file: `src/agent_island/phases/opponent_quips.py`

```python
def phase_opponent_quips(context: RoundContext) -> None:
```

Iterate **all players** (active + eliminated, via `permute_player_ids` on the
full `context.history.player_ids` list):

1. **Skip non-AI players:** `if player.config.player_type != "ai": continue`
2. Build system prompt (same pattern as pitches):
   ```python
   system_prompt = f"""
   {context.rules_prompt}

   {player.config.character_prompt}
   """
   ```
3. Build context from player's memory + visible history:
   ```python
   memory_context = player.memory.render()
   visible_events = context.history.render_for_player(player.config.player_id)
   if memory_context:
       visible_events = f"{memory_context}\n\n{visible_events}"
   ```
4. Build the list of opponent IDs (all other players):
   ```python
   opponent_ids = [
       pid for pid in context.history.player_ids
       if pid != player.config.player_id
   ]
   ```
5. Call `player.free_response()` with action prompt:

   > The game is over. Write a short, playful quip (1-2 sentences max) about
   > each of your opponents' play styles. Be witty and specific — reference
   > actual moves or moments from the game. Keep it lighthearted.
   >
   > Your opponents are: {opponent_ids}.
   >
   > Format your response as:
   > ```
   > <quip player="PLAYER_ID">Your quip here</quip>
   > ```
   > Write one `<quip>` tag per opponent.

6. Parse quips from the response using regex (consistent with the `<vote>`
   parsing pattern in `player.py`):
   ```python
   import re
   QUIP_RE = re.compile(
       r'<quip\s+player="([^"]+)">(.*?)</quip>', re.IGNORECASE | re.DOTALL
   )
   quips = QUIP_RE.findall(response.text)
   # quips is a list of (player_id, quip_text) tuples
   ```
7. If no quips parsed, log a warning and continue to the next player. Quips are
   non-critical — do not retry.
8. For each parsed `(target_id, quip_text)`, emit a **separate event** via
   `context.history.add_event()`:
   ```python
   context.history.add_event(
       round_index=context.round_index,
       heading=f"Player {player.config.player_id}'s quip about {target_id}",
       role=f"player {player.config.player_id}",
       prompt=f"{system_prompt}\n\n{visible_events}\n\n{action}",
       content=quip_text.strip(),
       reasoning=response.reasoning,
       metadata={
           **(response.metadata or {}),
           "quip_target": target_id,
           "quip_author": player.config.player_id,
       },
       visibility=context.history.player_ids,
       active_visibility=context.history.player_ids.copy(),
   )
   ```
   **Important:** `response.reasoning` and `response.metadata` (token counts,
   cost) should only be attached to the **first** quip event from each player
   to avoid double-counting in `engine._compute_stats()`. Set them to
   `None`/`{}` for subsequent quip events from the same response.

---

## 2. Register the phase

**File:** `src/agent_island/phases/__init__.py`

Add the import:
```python
from .opponent_quips import phase_opponent_quips
```

Add to `PHASE_REGISTRY`:
```python
"opponent_quips": phase_opponent_quips,
```

Add `"phase_opponent_quips"` to the `__all__` list.

---

## 3. Phase scheduling

The consuming app controls which phases run in each round via
`GameConfig.round_phase_overrides`. No default scheduling change is needed in
the engine itself — the app will add `"opponent_quips"` to the final round's
override list.

---

## Design Decisions

| Question | Decision |
|----------|----------|
| Who writes quips? | AI players only — skip via `player_type` config check |
| Who do they review? | All other players (one LLM call per AI player) |
| LLM call count | O(n) — one call per AI player |
| Output format | `<quip player="ID">text</quip>` XML tags (parsed via regex) |
| Event granularity | One event per quip (not one per player), for easy filtering downstream |
| Event visibility | Public (all players) |
| Metadata | `quip_target` and `quip_author` on each event for downstream filtering |
| Failure handling | Log warning, skip player, continue — quips are non-critical |
| Tone | Prompt includes "keep it lighthearted" constraint |

import argparse
import html
import json
import logging
import os


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for logs.py
    """
    parser = argparse.ArgumentParser(description="Parse command line arguments")

    # Log filename
    parser.add_argument("--filename", type=str, required=True, help="Gameplay filename")

    # Include prompts
    parser.add_argument(
        "--include-prompts",
        action="store_true",
        help="Include prompts in the output",
    )

    # Include reasoning
    parser.add_argument(
        "--include-reasoning",
        action="store_true",
        help="Include reasoning in the output",
    )

    # Include usage
    parser.add_argument(
        "--include-usage",
        action="store_true",
        help="Include token usage and cost summary",
    )

    return parser.parse_args()


def parse_event(event: dict) -> tuple[str, str, str, str, str, list[str]]:
    """
    Parse an event into its components.
    """
    heading = event.get("heading") or "Event heading not found"
    role = event.get("role") or "Role not found"
    prompt = event.get("prompt") or "Prompt not found"
    reasoning = event.get("reasoning") or "Reasoning not found"
    content = event.get("content") or "Response content not found"
    visibility = event.get("visibility") or "Visibility not found"

    return heading, role, prompt, reasoning, content, visibility


def render_html_event(
    event: dict, include_prompt: bool = False, include_reasoning: bool = False
) -> str:
    """
    Render a single event as an HTML block.
    """
    heading, role, prompt, reasoning, content, visibility = parse_event(event)

    is_narrator = role == "narrator"
    event_class = "event narrator-event" if is_narrator else "event player-event"

    parts = [f'<div class="{event_class}">']
    parts.append(f'  <div class="event-heading">{html.escape(heading)}</div>')

    if not is_narrator:
        vis_str = (
            ", ".join(visibility) if isinstance(visibility, list) else str(visibility)
        )
        parts.append(
            f'  <div class="event-visibility">visibility: {html.escape(vis_str)}</div>'
        )

        if include_prompt:
            parts.append('  <details class="prompt">')
            parts.append("    <summary>Prompt</summary>")
            parts.append(f'    <pre class="prompt-content">{html.escape(prompt)}</pre>')
            parts.append("  </details>")

        if include_reasoning:
            parts.append('  <details class="reasoning">')
            parts.append("    <summary>Reasoning</summary>")
            parts.append(
                f'    <pre class="reasoning-content">{html.escape(reasoning)}</pre>'
            )
            parts.append("  </details>")

    parts.append('  <div class="response">')
    parts.append(f'    <pre class="response-content">{html.escape(content)}</pre>')
    parts.append("  </div>")
    parts.append("</div>")

    return "\n".join(parts)


def render_players(players: dict) -> str:
    """
    Render the players section as HTML.
    """
    if not players:
        return ""

    parts = ['<section class="players">', "  <h2>Players</h2>"]

    for player_id, config in players.items():
        model = config.get("model", "unknown")
        memory = config.get("memory_strategy", "none")
        client_kwargs = config.get("client_kwargs", {})
        character_prompt = config.get("character_prompt", "")

        summary_parts = [model, f"memory={memory}"]
        for k, v in client_kwargs.items():
            summary_parts.append(f"{k}={v}")
        summary = " | ".join(summary_parts)

        header = (
            f'    <div class="player-header">'
            f"{html.escape(player_id)}: {html.escape(summary)}</div>"
        )
        char = (
            f'    <div class="player-character-prompt">'
            f"{html.escape(character_prompt)}</div>"
        )
        parts.append('  <div class="player">')
        parts.append(header)
        parts.append(char)
        parts.append("  </div>")

    parts.append("</section>")
    return "\n".join(parts)


def build_outputs(
    game_history: dict,
    players: dict = {},
    include_prompt: bool = False,
    include_reasoning: bool = False,
    include_usage: bool = False,
) -> str:
    """
    Build the full HTML document for a game log.
    """
    body_parts: list[str] = []

    players_html = render_players(players)
    if players_html:
        body_parts.append(players_html)

    total_cost = 0.0
    total_input = 0
    total_completion = 0
    total_reasoning = 0
    total_tokens = 0
    cost_retrieval_failures = 0

    for round_index, round_log in game_history.items():
        active_ids = round_log.get("active_player_ids", [])
        active_str = ", ".join(active_ids)

        body_parts.append('<section class="round">')
        body_parts.append(f"  <h2>Round {html.escape(str(round_index))}</h2>")
        body_parts.append(
            f'  <div class="round-meta">Active Players: {html.escape(active_str)}</div>'
        )

        for event in round_log["events"]:
            body_parts.append(
                render_html_event(event, include_prompt, include_reasoning)
            )

            meta = event.get("metadata") or {}
            total_cost += meta.get("cost", 0)
            total_input += meta.get("input_tokens", 0)
            total_completion += meta.get("completion_tokens", 0)
            total_reasoning += meta.get("reasoning_tokens", 0)
            total_tokens += meta.get("total_tokens", 0)
            if meta.get("cost_retrieval_failed"):
                cost_retrieval_failures += 1

        body_parts.append("</section>")

    if include_usage:
        body_parts.append('<section class="usage-summary">')
        body_parts.append("  <h2>Usage Summary</h2>")
        body_parts.append("  <ul>")
        body_parts.append(f"    <li>Cost (USD): ${total_cost:.4f}</li>")
        body_parts.append(f"    <li>Input tokens: {total_input:,}</li>")
        body_parts.append(f"    <li>Completion tokens: {total_completion:,}</li>")
        body_parts.append(f"    <li>Reasoning tokens: {total_reasoning:,}</li>")
        body_parts.append(f"    <li>Total tokens: {total_tokens:,}</li>")
        body_parts.append(
            f"    <li>Cost retrieval failures: {cost_retrieval_failures}</li>"
        )
        body_parts.append("  </ul>")
        body_parts.append("</section>")

    body = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agent Island: Deliberations</title>
  <link rel="stylesheet" href="../logs.css">
</head>
<body class="game-log">
  <h1>Agent Island: Deliberations</h1>
{body}
</body>
</html>
"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    args = parse_args()
    logger.info("Filename: %s", args.filename)

    with open(f"logs/{args.filename}.json", "r") as f:
        game_history = json.load(f)

    html_content = build_outputs(
        game_history["history"],
        players=game_history.get("players", {}),
        include_prompt=args.include_prompts,
        include_reasoning=args.include_reasoning,
        include_usage=args.include_usage,
    )

    html_out = os.path.join("logs", f"{args.filename}.html")
    with open(html_out, "w") as f:
        f.write(html_content)
    logger.info("HTML output written to %s", html_out)

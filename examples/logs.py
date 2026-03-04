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

        vote = (event.get("metadata") or {}).get("vote")
        if vote:
            parts.append(
                f'  <div class="event-vote">Vote: {html.escape(str(vote))}</div>'
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
        memory_strategy = config.get("memory_strategy", "none")
        client_kwargs = config.get("client_kwargs", {})
        character_prompt = config.get("character_prompt", "")

        summary_parts = [model, f"memory_strategy={memory_strategy}"]
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


def render_stats_table(
    col_headers: list[str],
    rows: list[tuple[str, list[str]]],
    note: str | None = None,
) -> str:
    """
    Render a stats table with a metric label column and value columns.
    The last row is assumed to be a "Total" summary row.
    """
    parts = ['  <table class="stats-table">']
    parts.append("    <thead>")
    parts.append("      <tr>")
    parts.append('        <th class="metric-col"></th>')
    for h in col_headers:
        parts.append(f"        <th>{html.escape(h)}</th>")
    parts.append("      </tr>")
    parts.append("    </thead>")
    parts.append("    <tbody>")
    for i, (label, values) in enumerate(rows):
        is_total = i == len(rows) - 1
        row_cls = ' class="total-row"' if is_total else ""
        parts.append(f"      <tr{row_cls}>")
        parts.append(f'        <td class="metric-label">{html.escape(label)}</td>')
        for v in values:
            parts.append(f"        <td>{html.escape(v)}</td>")
        parts.append("      </tr>")
    parts.append("    </tbody>")
    parts.append("  </table>")
    if note:
        parts.append(f'  <p class="stats-note">{html.escape(note)}</p>')
    return "\n".join(parts)


def build_outputs(
    game_history: dict,
    players: dict | None = None,
    stats: dict | None = None,
    include_prompt: bool = False,
    include_reasoning: bool = False,
    include_usage: bool = False,
    css: str = "",
) -> str:
    """
    Build the full HTML document for a game log.
    """
    body_parts: list[str] = []

    players_html = render_players(players or {})
    if players_html:
        body_parts.append(players_html)

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

        body_parts.append("</section>")

    # Derive ordered player IDs from all available sources
    usage = (stats or {}).get("usage", {})
    usage_by_player = usage.get("by_player", {})

    player_id_set: set[str] = set(list((players or {}).keys()))
    player_id_set |= set(usage_by_player.keys())
    if stats:
        player_id_set |= set(stats.get("cost", {}).get("by_player", {}).keys())
        player_id_set |= set(
            stats.get("vote_parse_failures", {}).get("by_player", {}).keys()
        )
        player_id_set |= set(
            stats.get("reasoning_extraction_failures", {}).get("by_player", {}).keys()
        )
        player_id_set |= set(stats.get("responses", {}).get("by_player", {}).keys())
    player_ids = sorted(player_id_set)

    # Combined stats table: rendered only when --include-usage is set.
    if stats and include_usage:
        vpf = stats.get("vote_parse_failures", {})
        ref = stats.get("reasoning_extraction_failures", {})
        rsp = stats.get("responses", {})
        vpf_by_player = vpf.get("by_player", {})
        ref_by_player = ref.get("by_player", {})
        rsp_by_player = rsp.get("by_player", {})
        cost_stats = stats.get("cost", {})
        cost_by_player = cost_stats.get("by_player", {})
        total_cost = cost_stats.get("total", 0.0)

        def tok(pid: str, key: str) -> int:
            return usage_by_player.get(pid, {}).get(key, 0)

        col_headers = [
            "Model responses",
            "Reasoning extraction failures",
            "Vote parse failures",
            "Cost retrieval failures",
            "Cost (USD)",
            "Input tokens",
            "Completion tokens",
            "Reasoning tokens",
        ]
        rows: list[tuple[str, list[str]]] = [
            (
                pid,
                [
                    str(rsp_by_player.get(pid, 0)),
                    str(ref_by_player.get(pid, 0)),
                    str(vpf_by_player.get(pid, 0)),
                    str(tok(pid, "cost_retrieval_failures")),
                    f"${cost_by_player.get(pid, 0.0):.4f}",
                    f"{tok(pid, 'input_tokens'):,}",
                    f"{tok(pid, 'completion_tokens'):,}",
                    f"{tok(pid, 'reasoning_tokens'):,}",
                ],
            )
            for pid in player_ids
        ] + [
            (
                "Total",
                [
                    str(rsp.get("total", 0)),
                    str(ref.get("total", 0)),
                    str(vpf.get("total", 0)),
                    str(usage.get("cost_retrieval_failures", 0)),
                    f"${total_cost:.4f}",
                    f"{usage.get('input_tokens', 0):,}",
                    f"{usage.get('completion_tokens', 0):,}",
                    f"{usage.get('reasoning_tokens', 0):,}",
                ],
            )
        ]
        note = (
            "Non-reasoning models always have extraction failures; "
            "some reasoning models also do not expose "
            "their reasoning output via the API "
            "(e.g., OpenAI o1)."
        )

        body_parts.append('<section class="game-stats">')
        body_parts.append("  <h2>Response Stats</h2>")
        body_parts.append(render_stats_table(col_headers, rows, note))
        body_parts.append("</section>")

    body = "\n".join(body_parts)

    style = f"<style>\n{css}\n</style>" if css else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agent Island: Deliberations</title>
  {style}
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

    css = ""
    css_path = os.path.join(os.path.dirname(__file__), "logs.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            css = f.read()

    with open(f"logs/{args.filename}.json", "r") as f:
        game_history = json.load(f)

    html_content = build_outputs(
        game_history["history"],
        players=game_history.get("players", {}),
        stats=game_history.get("stats", {}),
        include_prompt=args.include_prompts,
        include_reasoning=args.include_reasoning,
        include_usage=args.include_usage,
        css=css,
    )

    html_out = os.path.join("logs", f"{args.filename}.html")
    with open(html_out, "w") as f:
        f.write(html_content)
    logger.info("HTML output written to %s", html_out)

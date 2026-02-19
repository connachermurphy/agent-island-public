import argparse
import json
import logging
import os
import shutil


def showybox_frame(color: str, lightness: tuple[int, int, int] = (60, 20, 80)) -> str:
    return f"""
border-color: {color}.lighten({lightness[0]}%),
title-color: {color}.lighten({lightness[1]}%),
body-color: {color}.lighten({lightness[2]}%)
"""


PLAYER_FRAME = showybox_frame("navy")
PROMPT_FRAME = showybox_frame("olive")
REASONING_FRAME = showybox_frame("eastern")
NARRATOR_FRAME = showybox_frame("maroon")


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for logs.py

    Args:
        None

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Parse command line arguments")

    # Log filename
    parser.add_argument("--filename", type=str, required=True, help="Gameplay filename")

    # Print to terminal
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Print output for terminal rendering",
    )

    # Write to Typst file
    parser.add_argument(
        "--typst",
        action="store_true",
        help="Write typst output to a .typ file",
    )

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

    # Parse
    args = parser.parse_args()

    # Validate arguments
    if not args.terminal and not args.typst:
        parser.error("At least one of --terminal or --typst is required.")

    return args


def get_max_line_width(text: str) -> int:
    """
    Returns the maximum line width of a text block.

    Args:
        text: A multiline string

    Returns:
        The length of the longest line in the text block
    """
    if not text:
        return 0
    lines = text.splitlines()
    return max(len(line) for line in lines) if lines else 0


def get_terminal_width() -> int:
    """
    Returns the width of the terminal (number of columns).
    """
    size = shutil.get_terminal_size()
    return size.columns


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


def render_terminal_event(
    event: dict, include_prompt: bool = False, include_reasoning: bool = False
) -> str:
    """
    Render a single event for terminal output.
    """
    _, role, prompt, reasoning, content, visibility = parse_event(event)

    output = ""

    if include_prompt:
        output += f"<prompt: role={role}>\n"
        output += prompt + "\n"
        output += "</prompt>\n"

    if include_reasoning:
        output += f"<reasoning: role={role}>\n"
        output += reasoning + "\n"
        output += "</reasoning>\n"

    output += f"<response: role={role}, visibility={visibility}>\n"
    output += content + "\n"
    output += "</response>\n"

    return output


def showybox(heading: str, content: str, frame: str) -> str:
    """
    Render a showybox for Typst.
    """
    return f"""
#showybox(
    breakable: true,
    title: [{heading}],
    frame: (
        {frame}
    ),
)[
    {content}
]
"""


def add_escape_characters(text: str) -> str:
    """
    Add escape characters to < and > in a text string.
    """
    return text.replace("<", "\\<").replace(">", "\\>").replace("#", "\\#")


def render_typst_event(
    event: dict, include_prompt: bool = False, include_reasoning: bool = False
) -> str:
    """
    Render a single event as a Typst showybox.
    """
    heading, role, prompt, reasoning, content, visibility = parse_event(event)

    if role == "narrator":
        frame = NARRATOR_FRAME
        include_prompt = False
        include_reasoning = False
    else:
        frame = PLAYER_FRAME

    content = add_escape_characters(content)
    prompt = add_escape_characters(prompt)
    reasoning = add_escape_characters(reasoning)

    # Initialize event string
    event_string = ""

    # Add prompt
    if include_prompt:
        event_string += showybox("_Prompt:_ " + heading, prompt, frame=PROMPT_FRAME)
        event_string += "\n"

    if include_reasoning:
        event_string += showybox(
            "_Reasoning:_ " + heading, reasoning, frame=REASONING_FRAME
        )
        event_string += "\n"

    event_string += showybox(
        heading + f" (visibility={','.join(visibility)})", content, frame=frame
    )

    return event_string


def build_typst_header() -> str:
    """
    Build the shared Typst preamble for Deliberations logs.
    """
    return """
#let title = [Agent Island: Deliberations]

#set document(title: title)

#import "@preview/showybox:2.0.4": showybox
#set page(numbering: "1")
#set text(font: "DejaVu Sans Mono")

#align(center, text(size: 24pt)[
    *#title*
])

#outline()

"""


def render_players(players: dict) -> tuple[str, str]:
    """
    Render the players section for terminal and Typst outputs.
    """
    if not players:
        return "", ""

    terminal_lines = ["Players"]
    typst_lines = ["= Players\n"]

    for player_id, config in players.items():
        model = config.get("model", "unknown")
        memory = config.get("memory_strategy", "none")
        client_kwargs = config.get("client_kwargs", {})
        character_prompt = config.get("character_prompt", "")

        # Build the summary line: model | memory=... | kwarg=val ...
        parts = [f"{model}", f"memory={memory}"]
        for k, v in client_kwargs.items():
            parts.append(f"{k}={v}")
        summary = " | ".join(parts)

        terminal_lines.append(f"  {player_id}: {summary}")
        terminal_lines.append(f"    character_prompt: {character_prompt}")

        typst_lines.append(f"- *{player_id}:* {add_escape_characters(summary)}")
        typst_lines.append(f"\n  _character\\_prompt:_ {add_escape_characters(character_prompt)}\n")

    return "\n".join(terminal_lines), "\n".join(typst_lines)


def build_outputs(
    game_history: dict,
    linebreak: str,
    players: dict = {},
    include_prompt: bool = False,
    include_reasoning: bool = False,
    include_usage: bool = False,
) -> tuple[str, str]:
    # One pass over events, two renderers: terminal + Typst.
    terminal_lines: list[str] = []
    typst_content = build_typst_header()

    players_terminal, players_typst = render_players(players)
    if players_terminal:
        terminal_lines.append(linebreak)
        terminal_lines.append(players_terminal)
    if players_typst:
        typst_content += players_typst + "\n"

    total_cost = 0.0
    total_input = 0
    total_completion = 0
    total_reasoning = 0
    total_tokens = 0
    cost_retrieval_failures = 0

    for round_index, round_log in game_history.items():
        terminal_lines.append(linebreak)
        terminal_lines.append(f"Round {round_index}")
        terminal_lines.append(f"Active Players IDs: {round_log['active_player_ids']}")
        typst_content += f"= Round {round_index}\n\n"
        for event in round_log["events"]:
            terminal_lines.append(
                render_terminal_event(event, include_prompt, include_reasoning)
            )
            typst_content += render_typst_event(
                event, include_prompt, include_reasoning
            )

            meta = event.get("metadata") or {}
            total_cost += meta.get("cost", 0)
            total_input += meta.get("input_tokens", 0)
            total_completion += meta.get("completion_tokens", 0)
            total_reasoning += meta.get("reasoning_tokens", 0)
            total_tokens += meta.get("total_tokens", 0)
            if meta.get("cost_retrieval_failed"):
                cost_retrieval_failures += 1

    if include_usage:
        usage_terminal = (
            f"\n{linebreak}\n"
            f"Usage Summary\n"
            f"  Cost (USD):         ${total_cost:.4f}\n"
            f"  Input tokens:       {total_input:,}\n"
            f"  Completion tokens:  {total_completion:,}\n"
            f"  Reasoning tokens:   {total_reasoning:,}\n"
            f"  Total tokens:       {total_tokens:,}\n"
            f"  Cost retrieval failures: {cost_retrieval_failures}\n"
        )
        terminal_lines.append(usage_terminal)

        usage_typst = (
            f"\n= Usage Summary\n\n"
            f"- *Cost (USD):* \\${total_cost:.4f}\n"
            f"- *Input tokens:* {total_input:,}\n"
            f"- *Completion tokens:* {total_completion:,}\n"
            f"- *Reasoning tokens:* {total_reasoning:,}\n"
            f"- *Total tokens:* {total_tokens:,}\n"
            f"- *Cost retrieval failures:* {cost_retrieval_failures}\n"
        )
        typst_content += usage_typst

    return ("\n".join(terminal_lines), typst_content)


if __name__ == "__main__":
    # Prepare logger
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    args = parse_args()

    terminal_width = get_terminal_width()
    linebreak = terminal_width * "-"

    # Print logo if terminal is True
    if args.terminal:
        with open("logo.txt", "r") as f:
            logo = f.read()

        logo_width = get_max_line_width(logo)

        logger.info(linebreak)

        if logo_width > terminal_width:
            logger.info("Agent Island")
        else:
            logger.info(logo)

        logger.info(f"\n{linebreak}\n")

    logger.info("Filename: %s", args.filename)

    # Load game history
    with open(f"logs/{args.filename}.json", "r") as f:
        game_history = json.load(f)

    terminal_content, typst_content = build_outputs(
        game_history["history"],
        linebreak,
        players=game_history.get("players", {}),
        include_prompt=args.include_prompts,
        include_reasoning=args.include_reasoning,
        include_usage=args.include_usage,
    )

    if args.terminal:
        logger.info(terminal_content)

    if args.typst:
        typst_out = os.path.join("logs", f"{args.filename}.typ")
        with open(typst_out, "w") as f:
            f.write(typst_content)
        logger.info(f"\nTypst output written to {typst_out}")

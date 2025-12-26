import argparse
import json
import os
import shutil

PLAYER_FRAME = """
border-color: blue.lighten(60%),
title-color: blue.lighten(20%),
body-color: blue.lighten(80%)
"""


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for logs.py

    Args:
        None

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(description="Parse command line arguments")
    parser.add_argument("--filename", type=str, required=True, help="Gameplay filename")
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Print output for terminal rendering",
    )
    parser.add_argument(
        "--typst",
        action="store_true",
        help="Write typst output to a .typ file",
    )
    args = parser.parse_args()
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


def render_terminal_event(event: dict, include_prompt: bool = False) -> str:
    """
    Render a single event for terminal output.
    """
    output = ""

    if include_prompt:
        output += f"<prompt: role={event['role']}>"
        output += event["prompt"]
        output += "</prompt>"

    output += f"<response: role={event['role']}, visibility={event['visibility']}>\n"
    output += event["content"] + "\n"
    output += "</response>\n"

    return output


# TODO: create showybox function
# TODO: prompt render


def render_typst_event(event: dict, include_prompt: bool = False) -> str:
    """
    Render a single event as a Typst showybox.
    """
    heading = event.get("heading", "Event")
    content = event.get("content", "")

    # Add escape characters on < and >
    content = content.replace("<", "\<").replace(">", "\>")

    return f"""
#showybox(
    breakable: true,
    title: [{heading}],
    frame: (
        {PLAYER_FRAME}
    ),
)[
    {content}
]
"""


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


def build_outputs(
    game_history: dict,
    linebreak: str,
    include_prompt: bool = False,
    frame: str = PLAYER_FRAME,
) -> tuple[str, str]:
    # One pass over events, two renderers: terminal + Typst.
    terminal_lines: list[str] = []
    typst_content = build_typst_header()

    for round_index, round_log in game_history.items():
        terminal_lines.append(linebreak)
        terminal_lines.append(f"Round {round_index}")
        terminal_lines.append(f"Active Players IDs: {round_log['active_player_ids']}")
        typst_content += f"= Round {round_index}\n\n"
        for event in round_log["events"]:
            terminal_lines.append(render_terminal_event(event, include_prompt))
            typst_content += render_typst_event(event)

    return ("\n".join(terminal_lines), typst_content)


if __name__ == "__main__":
    # Entry point: load history, render terminal output, and optionally write Typst.
    args = parse_args()

    terminal_width = get_terminal_width()
    linebreak = terminal_width * "-"

    # Print logo if terminal is True
    if args.terminal:
        with open("logo.txt", "r") as f:
            logo = f.read()

        logo_width = get_max_line_width(logo)

        print(linebreak)

        if logo_width > terminal_width:
            print("Agent Island")
        else:
            print(logo)

        print(f"\n{linebreak}\n")

    print("Filename:", args.filename, "\n")
    # TODO: other metadata?

    # Load game history
    with open(f"logs/{args.filename}.json", "r") as f:
        game_history = json.load(f)

    # TODO: include prompts
    # TODO: include thinking

    terminal_content, typst_content = build_outputs(game_history, linebreak)

    if args.terminal:
        print(terminal_content)

    if args.typst:
        typst_out = os.path.join("logs", f"{args.filename}.typ")
        with open(typst_out, "w") as f:
            f.write(typst_content)
        print(f"\nTypst output written to {typst_out}")

# uv run logs.py --filename gameplay_20251223_154729 --terminal
# Process event: include prompt selectively --> add as command line argument
# Similar logic for including thinking
# Add colors

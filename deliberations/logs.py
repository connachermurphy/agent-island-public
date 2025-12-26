import argparse
import json
import os
import shutil

# TODO: build with function
PLAYER_FRAME = """
border-color: blue.lighten(60%),
title-color: blue.lighten(20%),
body-color: blue.lighten(80%)
"""

PROMPT_FRAME = """
border-color: olive.lighten(60%),
title-color: olive.lighten(20%),
body-color: olive.lighten(80%)
"""

REASONING_FRAME = """
border-color: purple.lighten(60%),
title-color: purple.lighten(20%),
body-color: purple.lighten(80%)
"""

NARRATOR_FRAME = """
border-color: teal.lighten(60%),
title-color: teal.lighten(20%),
body-color: teal.lighten(80%)
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

    # TODO: add reasoning rendering

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


def parse_event(event: dict) -> tuple[str, str, str, str, list[str]]:
    """
    Parse an event into its components.
    """
    heading = event.get("heading", "Event heading not found")
    content = event.get("content", "Response content not found")
    prompt = event.get("prompt", "Prompt not found")
    role = event.get("role", "Role not found")
    visibility = event.get("visibility", "Visibility not found")

    return heading, content, prompt, role, visibility


# TODO: add a higher level function to get pieces of an event (e.g., prompt, heading, content)
def render_terminal_event(event: dict, include_prompt: bool = False) -> str:
    """
    Render a single event for terminal output.
    """
    _, content, prompt, role, visibility = parse_event(event)

    output = ""

    if include_prompt:
        output += f"<prompt: role={role}>\n"
        output += prompt + "\n"
        output += "</prompt>\n"

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
    return text.replace("<", "\<").replace(">", "\>")


def render_typst_event(event: dict, include_prompt: bool = False) -> str:
    """
    Render a single event as a Typst showybox.
    """
    heading, content, prompt, role, visibility = parse_event(event)

    if role == "narrator":
        frame = NARRATOR_FRAME
        include_prompt = False
    else:
        frame = PLAYER_FRAME

    content = add_escape_characters(content)
    prompt = add_escape_characters(prompt)

    # Initialize event string
    event_string = ""

    # Add prompt
    if include_prompt:
        event_string += showybox("_Prompt:_ " + heading, prompt, frame=PROMPT_FRAME)
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


def build_outputs(
    game_history: dict,
    linebreak: str,
    include_prompt: bool = False,
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
            typst_content += render_typst_event(event, include_prompt)

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

    terminal_content, typst_content = build_outputs(
        game_history, linebreak, args.include_prompts
    )

    if args.terminal:
        print(terminal_content)

    if args.typst:
        typst_out = os.path.join("logs", f"{args.filename}.typ")
        with open(typst_out, "w") as f:
            f.write(typst_content)
        print(f"\nTypst output written to {typst_out}")

# uv run logs.py --filename gameplay_20251223_154729 --terminal
# uv run logs.py --filename gameplay_20251223_154729 --terminal --typst
# uv run logs.py --filename gameplay_20251223_154729 --terminal --typst --include-prompts
# Process event: include prompt selectively --> add as command line argument
# Similar logic for including thinking
# Add colors

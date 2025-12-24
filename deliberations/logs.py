import argparse
import json
import shutil


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
    return parser.parse_args()


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


def process_event(event: dict, include_prompt: bool = False) -> str:
    """
    Process an event and return a string representation.

    Args:
        event: The event to process
        include_prompt: Whether to include the prompt

    Returns:
        A string representation of the event
    """
    str = ""

    if include_prompt:
        str += f"<prompt: role={event['role']}>"
        str += event["prompt"]
        str += "</prompt>"

    str += f"<response: role={event['role']}, visibility={event['visibility']}>"
    str += event["content"]
    str += "</response>"

    return str


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()

    # Print logo if terminal is True
    if args.terminal:
        with open("logo.txt", "r") as f:
            logo = f.read()

        logo_width = get_max_line_width(logo)

        terminal_width = get_terminal_width()
        linebreak = terminal_width * "-"
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

    # Loop through rounds
    for round_index, round_log in game_history.items():
        print(linebreak)

        # Report round index
        print(f"Round {round_index}")

        # Report active players
        print("Active Players IDs:", round_log["active_player_ids"])

        # Loop through events
        for event in round_log["events"]:
            # print(event.keys())
            content = process_event(event)
            print(content)

# uv run logs.py --filename gameplay_20251223_154729 --terminal
# Process event: include prompt selectively --> add as command line argument
# Similar logic for including thinking

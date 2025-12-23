import argparse
import json
import shutil

# TODO: include prompts
# TODO: include thinking


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


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()

    # Print logo if terminal is True
    if args.terminal:
        with open("logo.txt", "r") as f:
            logo = f.read()

        logo_width = get_max_line_width(logo)

        terminal_width = get_terminal_width()

        if logo_width > terminal_width:
            print("Agent Island")
        else:
            print(logo)

    # Load game history
    with open(f"logs/{args.filename}.json", "r") as f:
        game_history = json.load(f)

    for round_index, round_log in game_history.items():
        print(terminal_width * "=")
        print(f"Round {round_index}")
        print("Player IDs:", round_log["player_ids"])
        print("Round index (stored)", round_log["round_index"])
        print(terminal_width * "=")
        print(round_log["events"])
        print(terminal_width * "=")
        print("\n\n")

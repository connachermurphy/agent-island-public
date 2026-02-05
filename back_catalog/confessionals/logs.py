import argparse
import json
import subprocess
import tempfile


def showybox(
    heading: str,
    content: str,
    frame: str = None,
) -> str:
    frame = (
        f"""
frame: (
    {frame}
),
"""
        if frame
        else ""
    )

    return f"""
#showybox(
    {frame}
    breakable: true,
    title: [{heading}],
    
)[
    {content}
]
    """


PLAYER_FRAME = """
border-color: blue.lighten(60%),
title-color: blue.lighten(20%),
body-color: blue.lighten(80%)
"""

NARRATOR_FRAME = """
border-color: olive.lighten(60%),
title-color: olive.lighten(20%),
body-color: olive.lighten(80%)
"""

DEBUG_FRAME = """
border-color: red.lighten(60%),
title-color: red.lighten(20%),
body-color: red.lighten(80%)
"""


def generate_typst_content(
    game_history: dict, timestamp: str, debug: bool = False
) -> str:
    """
    Generate a typst content string from the game history

    Args:
        game_history (dict): The game history
        debug (bool): Whether to include debug information in output

    Returns:
        str: The typst content string
    """

    typst_content = f"""
#let title = [Agent Island: Confessionals]

#set document(title: title)

#import "@preview/showybox:2.0.4": showybox
#set page(numbering: "1")
#set text(font: "DejaVu Sans Mono")

#align(center, text(size: 24pt)[
    *#title*
])

And so begins the adventure...

`Timestamp: {timestamp}`\n\n
"""

    typst_content += "#outline()"

    typst_content += showybox(
        "Host messages", "Host messages will be displayed here.", frame=NARRATOR_FRAME
    )
    typst_content += showybox(
        "Player messages", "Player messages will be displayed here.", frame=PLAYER_FRAME
    )

    for round_index, round_data in game_history.items():
        typst_content += f"= Round {round_data['round']}\n\n"
        for event in round_data["events"]:
            if debug:
                typst_content += showybox(
                    f"{event['heading']} (Debug)",
                    f"""
                    `Role: {event["role"]}`\n\n
                    `Visibility: {event["visibility"]}`\n\n
                    `Prompt: {event["prompt"]}`\n\n
                    """,
                    frame=DEBUG_FRAME,
                )
            if event["role"] == "narrator":
                typst_content += showybox(
                    event["heading"], event["content"], frame=NARRATOR_FRAME
                )
            else:
                typst_content += showybox(
                    event["heading"], event["content"], frame=PLAYER_FRAME
                )

    return typst_content


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate typst content from game logs"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Include debug information in output"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        required=True,
        help="Timestamp for the game log file (e.g., 20250831_163349)",
    )
    args = parser.parse_args()

    # Read game history file
    with open(f"logs/gameplay_{args.timestamp}.json", "r") as f:
        game_history = json.load(f)

    # Generate typst content
    typst_content = generate_typst_content(game_history, args.timestamp, args.debug)

    # Write typst content to file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".typ", delete=False, encoding="utf-8"
    ) as f:
        typst_file = f.name
        f.write(typst_content)

    filename = f"logs/gameplay{'_debug' if args.debug else ''}_{args.timestamp}.pdf"

    try:
        result = subprocess.run(
            [
                "typst",
                "compile",
                typst_file,
                filename,
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("Error: typst not found. Please install typst from https://typst.app/")

    if result.returncode == 0:
        print(f"PDF generated at {filename}")
    else:
        print(f"Error generating PDF: {result.stderr}")

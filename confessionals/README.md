# Agent Island: Confessionals



## Setup

1. Initialize the project:
```bash
uv sync
```

2. Set up your environment variables:
```bash
# Create a .env file with your Anthropic API key
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

## Usage

### Run a game:
```bash
uv run main.py
```

This script will:
- load player configurations from `prompts/players.json` and `prompts/player_*.md`;
- run elimination rounds with confessionals, pitches, and voting;
- run final round with confessionals, pitches, and voting;
- and save game history to `logs/gameplay_TIMESTAMP.json`.

### Generate formatted logs:
```bash
uv run logs.py --timestamp=TIMESTAMP [--debug]
```

Args:
- `--timestamp`: Required. The timestamp from the gameplay JSON file (e.g., `20250905_182337`)
- `--debug`: Optional. Include debug information (prompts, visibility, roles) in the output

Example:
```bash
uv run logs.py --timestamp=20250905_182337 --debug
```

This generates a PDF at `logs/gameplay_debug_TIMESTAMP.pdf` using Typst. Requires [Typst](https://typst.app/) to be installed.

## File Structure

- `main.py` - Main game engine and logic
- `logs.py` - Log formatting and PDF generation
- `prompts/` - Game rules and player character definitions
- `logs/` - Generated game logs and PDFs

## Game mechanics
The game is structured as follows:
- The game begins with 5 players
- From rounds 1 to 3, the players
    - have a (private) confessional for reflection and strategizing,
    - make their public pitch for advancing to the next round,
    - and, after observing all pitches, submit their (private) vote for a player to eliminate.
    - The player with the most votes is eliminated. In the case of a tie, one of the players with the most votes is randomly eliminated.
- In round 4, the remaining 2 players
    - have a (private) confessional for reflection and strategizing
    - and then make a (public) pitch for why they should win the game.
    - Next, the eliminated players select a winner.

Note, the script in `main.py` is written to accomodate modifications to the game structure (e.g., removing confessionals or making votes public).

## Todo:
- Create players flexibly (character prompt, toggle for self-generated prompt, model)
- There is some redundancy/confusion in the `elimination` and `final_round` logic that I need to clean up
- There is an explosion in context that I really need to manage.
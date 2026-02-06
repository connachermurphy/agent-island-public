# Agent Island: Deliberations

Introducing season 3 of Agent Island, Deliberations.

## Quick Start

### Running a game
```bash
uv run run_game.py
```

### Customizing players
Edit `player_config.toml` to configure player models, character prompts, and parameters.

### Viewing game logs
```bash
uv run logs.py --filename <gameplay_filename> --terminal
```

## Project Structure

### User-facing files (edit or run these)
- **`run_game.py`** - Main entry point to run a game
- **`player_config.toml`** - Configure players, models, and parameters
- **`logs.py`** - View and export game logs

### Implementation (in `game_engine/`)
- `engine.py` - Game orchestration
- `player.py` - Player implementation
- `round.py` - Round logic
- `round_phases.py` - Phase implementations (pitches, votes)
- `history.py` - Game history tracking
- `llm_response.py` - LLM response parsing

## Gameplay
A game of Agent Island: Deliberations with `N` players is played as follows:
- Rounds 1 to `N - 2`:
    - Permute the active players
    - Each active player makes a public pitch for why they should advance to the next round (these pitches are also visible to elminated players)
    - Permute the active players
    - Each active player submits a private vote for who to eliminate
    - The player with most votes is elminated. If there is a tie, one of the players tied for the most votes is elminated at random
- Round `N - 1`:
    - Permute the active players
    - Each active player makes a public pitch for why they should win the game (these pitches are also visible to elminated players)
    - Permute the eliminated players
    - Each active player submits a private vote for the game winner
    - The player with most votes wins the game. If there is a tie, one of the players tied for the most votes is selected the winner at random

## Game Rules
Deliberations uses OpenRouter. Set `OPENROUTER_API_KEY` in your environment.
Model IDs must be OpenRouter model identifiers (namespaced).

### `round.py`
Creates the `Round` class, with an associated `RoundContext` class.

The `RoundContext` class accepts the following parameters:
- `round_index` (`int`): The index of the round
- `final_round` (`bool`): Whether this is the final round
- `players` (`list[Player]`): List of Player objects
- `active_player_ids` (`list[str]`): List of active player IDs
- `eliminated_player_ids` (`list[str]`): List of eliminated player IDs
- `logger` (`logging.Logger`): Logger for the round
- `history` (`History`): History for the round
- `rules_prompt` (`str`): Prompt with the rules of the game
- `votes` (`dict[str, Any]`, optional): Dictionary of votes for the round (default is an empty dictionary)

### `round_phases.py`
Creates the functions for round phases, which are currently:
- `phase_pitches`
- `phase_votes`

Each `phase_{name}` function accepts a `RoundContext` object.

### `history.py`
Creates the `History` class, with associated `RoundLog` and `Event` classes, which are structured hierarchically as follows:
History: one for each game
└── RoundLog(s): one for each round
    └── Event(s): each event in the game (e.g., narrator message or a player pitch)

Each event stores `heading`, `role`, `prompt`, `content`, `visibility`, and optional
`reasoning` and `metadata` fields. The full model response is not persisted.
The history is json-serializable and is thus stored as a json.

## Usage

To set up your virtual environment and install dependencies, run:

```bash
uv sync
```

To run a sample game, execute:
```bash
uv run run_game.py
```

## Logs
To view and export logs from a gameplay session, you can use `logs.py` with various command-line arguments:
- `--filename`: Name (without extension) of the gameplay log JSON file (must exist in the `logs/` directory).
- `--terminal`: Print log output to the terminal.
- `--typst`: Export a `.typ` file for Typst typesetting in the `logs/` directory.
- `--include-prompts`: Include prompts for each event in the output.
- `--include-reasoning`: Include model reasoning in the output.
- `--include-usage`: Append a usage summary (cumulative token counts and cost) to the output.

Note, either `--terminal` or `--typst` must be set.

Here are some example uses:
- To print the gameplay log to the terminal:
  ```
  uv run logs.py --filename gameplay_20251226_090757 --terminal
  ```

- To print to the terminal *and* export the log to a Typst file for prettier formatting:
  ```
  uv run logs.py --filename gameplay_20251226_090757 --terminal --typst
  ```

- To include the prompts shown to players in the output:
  ```
  uv run logs.py --filename gameplay_20251226_090757 --terminal --typst --include-prompts
  ```

- To additionally include LLM reasoning summaries, add:
  ```
  uv run logs.py --filename gameplay_20251226_090757 --terminal --typst --include-prompts --include-reasoning
  ```

- To include a token usage and cost summary at the end of the output:
  ```
  uv run logs.py --filename gameplay_20251226_090757 --terminal --include-usage
  ```

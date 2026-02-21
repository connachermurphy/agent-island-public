# agent-island-public
Agent Island (for public release)

## Usage

Run a game with the `agent-island` CLI using `uv run`:

```bash
uv run agent-island [--game-config PATH] [--player-config PATH]
```

**Options:**
- `--game-config` — Path to a game config TOML file (default: `game_config.toml`)
- `--player-config` — Path to a player config TOML file (default: `player_config.toml`)

**Example:**
```bash
uv run agent-island --game-config game_config.toml --player-config player_config.toml
```

Alternatively, install the CLI globally with `uv tool install .` and run `agent-island` directly.

**Prerequisite:** `OPENROUTER_API_KEY` must be set in your environment or a `.env` file.

## Development

### Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Linting checks run automatically on pull requests and must pass before merging.

**Check for issues:**
```bash
uvx ruff check .
uvx ruff format --check .
```

**Auto-fix issues:**
```bash
uvx ruff check --fix .  # Fix linting issues (including import sorting)
uvx ruff format .       # Auto-format code
```

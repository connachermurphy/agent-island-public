# agent-island-public
Agent Island (for public release)

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

# Examples

## Viewing game logs

After running a game, view the logs with `logs.py`. This writes an HTML file to the `logs/` directory.

```bash
uv run logs.py --filename <gameplay_filename>
```

Arguments:
- `--filename`: Name (without extension) of the gameplay log JSON file (must exist in the `logs/` directory).
- `--include-prompts`: Include the full prompt sent to each player (shown in a collapsible expander).
- `--include-reasoning`: Include model reasoning (shown in a collapsible expander).
- `--include-usage`: Append a usage summary (cumulative token counts and cost) at the end.

Example uses:

- Basic log view:
  ```bash
  uv run logs.py --filename gameplay_20251226_090757
  ```

- Include prompts and reasoning:
  ```bash
  uv run logs.py --filename gameplay_20251226_090757 --include-prompts --include-reasoning
  ```

- Include token usage and cost summary:
  ```bash
  uv run logs.py --filename gameplay_20251226_090757 --include-usage
  ```

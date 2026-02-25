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

- Include prompts, reasoning, and usage summary:
  ```bash
  uv run logs.py --include-prompts --include-reasoning --include-usage --filename gameplay_202521226_090757
  ```

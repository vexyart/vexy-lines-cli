# Installation

## Requirements

- Python 3.11 or newer
- The [Vexy Lines](https://vexy.art) desktop app for MCP and export commands
- macOS for the dialog-less export pipeline (uses AppleScript and `defaults write`)

## Install from PyPI

```bash
pip install vexy-lines-cli
```

This pulls in `vexy-lines-apy` (MCP client, style engine) and `vexy-lines-py` (parser) automatically.

Or with `uv`:

```bash
uv add vexy-lines-cli
```

## Additional extras

For video processing:

```bash
pip install "vexy-lines-run[video]"
```

For the GUI:

```bash
pip install vexy-lines-run
```

## Installed commands

| Command | What it runs |
|---------|-------------|
| `vexy-lines` | CLI (with args) or GUI (without args) |
| `vexy-lines-mcp` | MCP stdio-to-TCP bridge server |

## Runtime dependencies

| Package | Why |
|---------|-----|
| `vexy-lines-apy` | MCP client and style engine |
| `fire` | CLI framework (subcommand dispatch) |
| `loguru` | Structured debug logging |

## Verify the install

```bash
vexy-lines --help
```

## Development install

```bash
git clone https://github.com/vexyart/vexy-lines.git
cd vexy-lines/vexy-lines-cli
uv venv --python 3.12
uv pip install -e ".[dev]"
```

Run tests:

```bash
uvx hatch test
```

# vexy-lines-cli

Command-line interface and MCP passthrough server for [Vexy Lines](https://vexy.art) — the macOS vector art app.

Parse `.lines` files, batch export to PDF/SVG, apply styles to images and video, and connect Claude Desktop or Cursor directly to the Vexy Lines MCP API.

## Install

```bash
pip install vexy-lines-cli
```

Requires Python 3.11+. Pulls in `vexy-lines-apy` (MCP client, style engine) and `vexy-lines-py` (parser) automatically.

For video processing: `pip install vexy-lines-run[video]`. For the GUI: `pip install vexy-lines-run`.

## Quick start

```bash
# Inspect a file without opening the app
vexy-lines info artwork.lines

# Show the layer/group/fill tree
vexy-lines file-tree artwork.lines

# Export a folder of .lines files to PDF (auto-launches the app)
vexy-lines export ./my-art/ --format pdf

# Apply a style template to a folder of photos
vexy-lines style-transfer --style template.lines --input-dir ./photos/ --output-dir ./out/

# Check MCP connectivity
vexy-lines mcp-status
```

Running `vexy-lines` with no arguments launches the GUI (requires `vexy-lines-run`).

## Subcommand reference

### Parser — no app required

| Command | What it does |
|---|---|
| `info <file>` | Show caption, DPI, dimensions, layer/fill counts |
| `file-tree <file>` | Print the layer/group/fill hierarchy |
| `extract-source <file>` | Save the embedded source image to disk |
| `extract-preview <file>` | Save the embedded preview image to disk |
| `batch-convert` | Extract preview or source images from a directory of `.lines` files |

All parser commands accept `--json-output` for machine-readable output.

```bash
vexy-lines info artwork.lines --json-output
vexy-lines batch-convert --input-dir ./art/ --output-dir ./thumbs/ --what preview --format jpg
```

### Export — auto-launches app

Uses dialog-less export: injects settings into macOS preferences, triggers `File > Export`, then restores original prefs. Input can be a single file or a directory.

```bash
vexy-lines export ./art/ --format svg --output ./svg-out/
vexy-lines export artwork.lines --format pdf --dry-run   # preview without exporting
vexy-lines export ./art/ --force --timeout-multiplier 2
```

Options: `--format` (`pdf`/`svg`), `--force`, `--dry-run`, `--timeout-multiplier` (0.1–10.0), `--max-retries` (0–10), `--say-summary`.

### Style — app must be running

```bash
# Single style across all images
vexy-lines style-transfer --style look.lines --input-dir ./frames/ --format svg

# Interpolate between two styles across the sequence
vexy-lines style-transfer --style start.lines --end-style end.lines \
    --input-dir ./frames/ --output-dir ./out/

# Apply style to video
vexy-lines style-video --style look.lines --input clip.mp4 --output result.mp4
```

### MCP — app must be running

Direct JSON-RPC calls to the Vexy Lines embedded server (`localhost:47384`).

| Command | What it does |
|---|---|
| `mcp-status` | Check if the MCP server is reachable |
| `tree` | Print the live document layer tree |
| `new-document` | Create a new document |
| `open <file>` | Open a `.lines` file |
| `add-fill <layer-id> <fill-type>` | Add a fill to a layer |
| `render` | Trigger a full render |

```bash
vexy-lines mcp-status
vexy-lines tree --json-output
vexy-lines new-document --width 210 --height 297 --dpi 300
vexy-lines add-fill 42 linear --color "#ff0000"
```

All MCP commands accept `--host` and `--port` (defaults: `127.0.0.1:47384`).

### Bridge and GUI

| Command | What it does |
|---|---|
| `mcp-serve` | Start the stdio-to-TCP bridge (same as running `vexy-lines-mcp`) |
| `gui` | Launch the Vexy Lines Run (requires `vexy-lines-run`) |

## MCP server setup

`vexy-lines-mcp` bridges Claude Desktop and Cursor to the Vexy Lines TCP server. It reads newline-delimited JSON-RPC from stdin, forwards over TCP, and writes responses to stdout.

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "vexy-lines": {
      "command": "vexy-lines-mcp"
    }
  }
}
```

For Cursor, add the same block under `mcp.servers` in `.cursor/mcp.json`.

The bridge auto-launches the Vexy Lines app on first connection. Pass `--no-launch` to disable:

```bash
vexy-lines mcp-serve --no-launch
vexy-lines mcp-serve --host 127.0.0.1 --port 47384
```

## Full documentation

[Read the docs](https://vexyart.github.io/vexy-lines/vexy-lines-cli/) for the complete CLI reference, export pipeline internals, and more examples.

## License

MIT

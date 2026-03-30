# vexy-lines-cli

CLI tool and MCP passthrough server for [Vexy Lines](https://vexy.art) vector art.

Parse `.lines` files, apply styles via MCP, batch export to PDF/SVG, and automate the Vexy Lines application -- all from the command line.

## Installation

```bash
pip install vexy-lines-cli
```

This pulls in `vexy-lines-apy` (MCP client, style engine) and `vexy-lines-py` (parser) automatically.

## Quick start

```bash
# Show file metadata
vexy-lines info artwork.lines

# Print the layer tree
vexy-lines file_tree artwork.lines

# Extract the embedded source image
vexy-lines extract_source artwork.lines

# Extract the preview image
vexy-lines extract_preview artwork.lines --format .png

# Batch export a directory to PDF
vexy-lines export ./my-art/ --format pdf

# Apply a style to images
vexy-lines style_transfer --style template.lines --input-dir ./photos/ --output-dir ./output/

# Check MCP server status
vexy-lines mcp_status
```

## Subcommands

### Parser (no app needed)

| Command | Description |
|---------|-------------|
| `info INPUT` | Show `.lines` file metadata (caption, DPI, layer counts) |
| `file_tree INPUT` | Print the layer/group/fill tree |
| `extract_source INPUT` | Extract the embedded source image |
| `extract_preview INPUT` | Extract the embedded preview image |

### Style (requires MCP server)

| Command | Description |
|---------|-------------|
| `style_transfer` | Apply a `.lines` style to images, with optional interpolation |
| `style_video` | Apply a style to video frames |

### Batch operations

| Command | Description |
|---------|-------------|
| `batch_convert` | Extract previews/sources from `.lines` files in bulk |
| `export INPUT` | Batch export `.lines` to PDF/SVG via plist injection |

### MCP (requires running Vexy Lines app)

| Command | Description |
|---------|-------------|
| `mcp_status` | Check if the MCP server is reachable |
| `tree` | Print the layer tree of the current document |
| `new_document` | Create a new document |
| `open INPUT` | Open a `.lines` file |
| `add_fill LAYER_ID FILL_TYPE` | Add a fill to a layer |
| `render` | Trigger a full render |

### GUI

| Command | Description |
|---------|-------------|
| `gui` | Launch the GUI (requires `vexy-lines-run`) |

Running `vexy-lines` with no arguments also attempts to launch the GUI.

## Common options

Most subcommands support:

- `--json-output` -- output as JSON
- `--verbose` -- show detailed progress
- `--host` / `--port` -- MCP server address (default `127.0.0.1:47384`)

Export-specific:

- `--format` -- `pdf` or `svg`
- `--force` -- re-export even if output exists
- `--dry-run` -- preview without exporting
- `--timeout-multiplier` -- scale all timeouts (0.1--10.0)
- `--max-retries` -- retry attempts per file (0--10)

## License

MIT

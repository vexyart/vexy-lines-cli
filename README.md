# vexy-lines-cli

Command-line interface and MCP passthrough server for [Vexy Lines](https://vexy.art) — the macOS vector art app.

Parse `.lines` files, batch export to PDF/SVG/PNG, apply styles to images and video, and connect Claude Desktop or Cursor directly to the Vexy Lines MCP API.

## Install

```bash
pip install vexy-lines-cli
```

Requires Python 3.11+. Pulls in `vexy-lines-apy` (MCP client, style engine) and `vexy-lines-py` (parser) automatically.

For video processing and the GUI: `pip install vexy-lines-run` (all dependencies are included).

## Quick start

```bash
# Inspect a file without opening the app
vexy-lines-cli info artwork.lines

# Show the layer/group/fill tree
vexy-lines-cli file-tree artwork.lines

# Export a folder of .lines files to PDF (auto-launches the app)
vexy-lines-cli export ./my-art/ --format pdf

# Apply a style template to a folder of photos
vexy-lines-cli style-transfer --style template.lines --input-dir ./photos/ --output-dir ./out/

# Check MCP connectivity
vexy-lines-cli mcp-status
```

## Subcommand reference

### Parser — no app required

| Command | What it does |
|---|---|
| `info <file>` | Show caption, DPI, dimensions, layer/fill/filter counts |
| `file-tree <file>` | Print the layer/group/fill hierarchy, including image filters |
| `extract-source <file>` | Save the embedded source image to disk |
| `extract-sources <file>` | Save the document source plus all group source images |
| `extract-preview <file>` | Save the embedded preview image to disk |
| `batch-convert` | Extract preview or source images from a directory of `.lines` files |

All parser commands accept `--json-output` for machine-readable output.

```bash
vexy-lines-cli info artwork.lines --json-output
vexy-lines-cli extract-sources artwork.lines --output-dir ./sources/
vexy-lines-cli batch-convert --input-dir ./art/ --output-dir ./thumbs/ --what preview --format jpg
```

### Export — auto-launches app

Uses dialog-less export: injects settings into macOS preferences, triggers `File > Export`, then restores original prefs. Input can be a single file or a directory.

```bash
vexy-lines-cli export ./art/ --format svg --output ./svg-out/
vexy-lines-cli export artwork.lines --format pdf --dry-run   # preview without exporting
vexy-lines-cli export ./art/ --force --timeout-multiplier 2
```

Options: `--format` (`pdf`/`svg`/`png`), `--force`, `--dry-run`, `--timeout-multiplier` (0.1–10.0), `--max-retries` (0–10), `--say-summary`.

### Export bundle - auto-launches app

Export one file or a directory to several formats in one pass and optionally extract the embedded source image.

```bash
vexy-lines-cli export-bundle artwork.lines
vexy-lines-cli export-bundle ./art/ --output ./bundle-out/
vexy-lines-cli export-bundle artwork.lines --formats pdf,svg --source=False
```

Options: `--formats` (`pdf,svg,png` by default), `--source`, `--dpi`, `--render-timeout`.

### Style — app must be running

```bash
# Single style across all images
vexy-lines-cli style-transfer --style look.lines --input-dir ./frames/ --format svg

# Interpolate between two styles across the sequence
vexy-lines-cli style-transfer --style start.lines --end-style end.lines \
    --input-dir ./frames/ --output-dir ./out/

# Apply style to video
vexy-lines-cli style-video --style look.lines --input clip.mp4 --output result.mp4

# Resume an interrupted video job (automatic — just re-run the same command)
vexy-lines-cli style-video --style look.lines --input clip.mp4 --output result.mp4

# Force restart (discard cached frames)
vexy-lines-cli style-video --style look.lines --input clip.mp4 --output result.mp4 --force

# Auto-clean job folder after completion
vexy-lines-cli style-transfer --style look.lines --input-dir ./frames/ --cleanup
```

All style commands create a **job folder** (`{output}-vljob/`) that stores intermediate `.lines`, `.svg`, and raster files. If the process is interrupted, re-running the same command skips already-completed items. Use `--force` to start fresh or `--cleanup` to remove the job folder after completion.

### Interpolation

```bash
# One explicit intermediate .lines file, no app required
vexy-lines-cli interpolate start.lines end.lines --t 0.5 --output mid.lines

# Render the full interpolation timeline through the app
vexy-lines-cli interpolate-video start.lines end.lines \
    --output blend.mp4 --frames 120 --fps 30

# Capture the Vexy Lines GUI while stepping through the interpolation
vexy-lines-cli record-interpolation-screen start.lines end.lines \
    --output ./screen-frames --frames 120 --fps 30 --zoom-steps 2 \
    --video screen-recording.mp4
```

`interpolate` writes a real `.lines` document between two files with the same group/layer/fill structure, blending matching numeric XML attributes and native `.lines` colours while preserving IDs, captions, flags, and enum-like modes. `interpolate-video` renders generated intermediate `.lines` documents via MCP, rasterizes app-exported SVG frames locally, and assembles MP4. `record-interpolation-screen` opens the start document in the GUI, applies optional macOS zoom keystrokes, captures the Vexy Lines window once per interpolation frame, and can assemble those screenshots into a video. The JSON result reports requested `frames` separately from retained temporary artifacts; use `--keep-work` or `--work-dir` when you need intermediate paths.

### MCP — app must be running

Direct JSON-RPC calls to the Vexy Lines embedded server (`localhost:47384`).

| Command | What it does |
|---|---|
| `mcp-status` | Check if the MCP server is reachable |
| `tree` | Print the live document layer tree |
| `new-document` | Create a new document |
| `open <file>` | Open a `.lines` file |
| `add-fill <layer-id> <fill-type>` | Add a fill to a layer |
| `get-image-filters <fill-id>` | Read a fill's image-filter chain |
| `set-image-filters <fill-id> <filters-json>` | Replace a fill's image-filter chain |
| `add-image-filter <fill-id> <filter-type>` | Add one image filter to a fill |
| `remove-image-filter <fill-id> <index>` | Remove one image filter from a fill |
| `render` | Trigger a full render |

```bash
vexy-lines-cli mcp-status
vexy-lines-cli tree --json-output
vexy-lines-cli new-document --width 210 --height 297 --dpi 300
vexy-lines-cli add-fill 42 linear --color "#ff0000"
vexy-lines-cli get-image-filters 99
vexy-lines-cli set-image-filters 99 '[{"type":"brightness","params":{"value":25}}]'
vexy-lines-cli add-image-filter 99 levels --params '{"left":10,"right":240}'
```

All MCP commands accept `--host` and `--port` (defaults: `127.0.0.1:47384`).

### MCP bridge

| Command | What it does |
|---|---|
| `mcp-serve` | Start the stdio-to-TCP bridge (same as running `vexy-lines-mcp`) |

### AI rename — auto-launches app + needs a vision model

Rename a `.lines` file's [layers and fills](https://help.vexy.art/lines/articles/layers-panel/) with a vision-language model. Each fill is rendered in isolation, boxed over a faint copy of the full artwork, and given a short descriptive caption; layers are named from their fills. Only captions change — every fill parameter and embedded image is preserved.

```bash
pip install "vexy-lines-cli[ai]"          # openai + pathvalidate + python-slugify

vexy-lines-cli ai-rename road-12.lines              # -> road-12-renamed.lines
vexy-lines-cli ai-rename road-12.lines --dry-run    # preview names, write nothing
vexy-lines-cli ai-rename road-12.lines --json-output
vexy-lines-cli ai-rename road-12.lines \
    --llm-api-url http://127.0.0.1:1234/v1 --llm-model-vision my-vision-model
```

The endpoint is an OpenAI-compatible `/v1` server, configured from the environment — `VEXY_LINES_LLM_API_URL`, `VEXY_LINES_LLM_API_KEY`, `VEXY_LINES_LLM_MODEL_VISION` (vision), `VEXY_LINES_VLM_MODEL` (text) — and overridable with `--llm-api-url`, `--llm-api-key`, `--llm-model-vision`, `--llm-model`. See the [full AI rename guide](https://vexy.dev/vexy-lines-apy/ai-rename/).

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
vexy-lines-cli mcp-serve --no-launch
vexy-lines-cli mcp-serve --host 127.0.0.1 --port 47384
```

## Full documentation

[Read the docs](https://vexyart.github.io/vexy-lines/vexy-lines-cli/) for the complete CLI reference, export pipeline internals, and more examples.

- [CLI Reference](https://vexyart.github.io/vexy-lines/vexy-lines-cli/cli-reference/) — every subcommand
- [MCP Bridge](https://vexyart.github.io/vexy-lines/vexy-lines-cli/mcp-bridge/) — Claude Desktop / Cursor setup
- [Export Pipeline](https://vexyart.github.io/vexy-lines/vexy-lines-cli/export-pipeline/) — dialog-less export internals
- [CHANGELOG](CHANGELOG.md) — release history

## License

MIT

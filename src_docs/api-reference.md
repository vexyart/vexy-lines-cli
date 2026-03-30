# API Reference

The CLI is built on Python Fire, so every public method on `VexyLinesCLI` is also callable from Python.

## VexyLinesCLI

```python
from vexy_lines_cli import VexyLinesCLI

cli = VexyLinesCLI()
```

### Parser methods

#### `info(input, json_output=False) -> dict`

Parse a `.lines` file and return metadata. No app needed.

```python
result = cli.info("artwork.lines")
# {"caption": "My Art", "version": "4.0", "dpi": 300, ...}
```

#### `file_tree(input, json_output=False) -> str`

Print the layer/group/fill hierarchy. Returns indented text or JSON.

#### `extract_source(input, output=None, format=".jpg") -> dict`

Extract the embedded JPEG source image.

#### `extract_preview(input, output=None, format=".png") -> dict`

Extract the embedded PNG preview image.

#### `batch_convert(input_dir, output_dir="./output", format="png", what="preview") -> dict`

Extract images from all `.lines` files in a directory.

### Style methods

#### `style_transfer(style, ...) -> dict`

Apply a `.lines` style to images via MCP. See [CLI Reference](cli-reference.md#style-transfer) for all options.

#### `style_video(style, input, output="output.mp4", ...) -> dict`

Apply a style to video frames. Requires `vexy-lines-run`.

### Export methods

#### `export(input, output=None, format="pdf", ...) -> dict`

Export `.lines` files to PDF/SVG via the plist injection pipeline.

### MCP methods

#### `mcp_status(host, port) -> dict`

Check MCP server connectivity.

#### `tree(host, port, json_output=False) -> dict | str`

Get the live document layer tree.

#### `new_document(width, height, dpi, source_image, host, port) -> dict`

Create a new document via MCP.

#### `open(input, host, port) -> dict`

Open a `.lines` file via MCP.

#### `add_fill(layer_id, fill_type, color, host, port) -> dict`

Add a fill to a layer via MCP.

#### `render(host, port) -> dict`

Trigger a full render via MCP.

### Bridge

#### `mcp_serve(host, port, no_launch=False) -> None`

Start the stdio-to-TCP MCP bridge.

---

## Export module

### ExportConfig

```python
from vexy_lines_cli.export.config import ExportConfig

config = ExportConfig(format="pdf", timeout_multiplier=1.5, max_retries=3)
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `app_name` | `str` | `"Vexy Lines"` | Application name |
| `format` | `str` | `"pdf"` | `"pdf"` or `"svg"` |
| `poll_interval` | `float` | `0.2` | Seconds between polls |
| `wait_for_app` | `float` | `20.0` | App launch timeout |
| `wait_for_file` | `float` | `20.0` | File window timeout |
| `post_action_delay` | `float` | `0.4` | Pause after each action |
| `timeout_multiplier` | `float` | `1.0` | Scale all timeouts |
| `max_retries` | `int` | `3` | Retries per file |

### VexyLinesExporter

```python
from vexy_lines_cli.export.exporter import VexyLinesExporter

exporter = VexyLinesExporter(config, dry_run=False, force=False)
stats = exporter.export(Path("./art/"), Path("./output/"))
```

### ExportStats

Tracks timing and file counts. Call `stats.as_dict()` for a serializable dict or `stats.human_summary()` for a readable string.

---

## Automation module

### AppleScriptBridge

Wraps `osascript` calls for app control: quit, launch, activate, menu items, window title queries.

### WindowWatcher

Polls window titles to detect file open and export completion.

---

## MCP server

### `serve(host, port, stdin, stdout, auto_launch) -> None`

Run the stdio-to-TCP bridge loop. Reads JSON-RPC from stdin, forwards to TCP, writes responses to stdout.

```python
from vexy_lines_cli.mcp_server import serve

serve(host="127.0.0.1", port=47384)
```

---

## Utility functions

### `speak(text) -> None`

Announce text via macOS `say` command. No-op on other platforms.

### `discover_lines_files(path) -> list[Path]`

Find `.lines` files in a path (single file or recursive directory search).

### `InterruptHandler`

Context manager that catches `SIGINT` for graceful shutdown during batch operations.

# CLI Reference

All commands use `vexy-lines-cli <subcommand>`. Add `--help` to any subcommand for usage details.

## Parser commands (no app required)

These work offline -- they parse `.lines` XML directly.

### `info`

Show metadata for a `.lines` file.

```bash
vexy-lines-cli info artwork.lines
vexy-lines-cli info artwork.lines --json-output
```

Returns: caption, version, DPI, dimensions, group/layer/fill counts, embedded image flags.

### `file-tree`

Print the layer/group/fill hierarchy.

```bash
vexy-lines-cli file-tree artwork.lines
vexy-lines-cli file-tree artwork.lines --json-output
```

Output shows nesting with indentation. Hidden layers are marked `[hidden]`. Fills show their algorithm in brackets.

### `extract-source`

Save the embedded JPEG source image to disk.

```bash
vexy-lines-cli extract-source artwork.lines
vexy-lines-cli extract-source artwork.lines --output photo.jpg
vexy-lines-cli extract-source artwork.lines --format .png
```

Default output: `<stem>-src.jpg` in the same directory.

### `extract-preview`

Save the embedded PNG preview image to disk.

```bash
vexy-lines-cli extract-preview artwork.lines
vexy-lines-cli extract-preview artwork.lines --output thumb.png
```

Default output: `<stem>-preview.png` in the same directory.

### `batch-convert`

Extract preview or source images from all `.lines` files in a directory.

```bash
vexy-lines-cli batch-convert --input-dir ./art/ --output-dir ./thumbs/
vexy-lines-cli batch-convert --input-dir ./art/ --what source --format jpg
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--input-dir` | (required) | Directory containing `.lines` files |
| `--output-dir` | `./output` | Where to write images |
| `--what` | `preview` | `preview` or `source` |
| `--format` | `png` | Output image format |

## Export command (auto-launches app)

### `export`

Export `.lines` files to PDF or SVG without save dialogs. Works on a single file or a directory (recursive).

```bash
vexy-lines-cli export artwork.lines
vexy-lines-cli export ./my-art/ --format svg --output ./exports/
vexy-lines-cli export artwork.lines --dry-run
vexy-lines-cli export ./art/ --force --timeout-multiplier 2
```

The pipeline: quits the app, injects export preferences into macOS defaults, relaunches, opens each file, triggers File > Export, restores original preferences.

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `pdf` | `pdf` or `svg` |
| `--output` | same folder | Destination file or directory |
| `--dry-run` | `False` | List files without exporting |
| `--force` | `False` | Re-export even if output exists |
| `--timeout-multiplier` | `1.0` | Scale all timeouts (range 0.1--10) |
| `--max-retries` | `3` | Retry attempts per file (range 0--10) |
| `--say-summary` | `False` | Announce result via macOS text-to-speech |
| `--verbose` | `False` | Enable debug logging |

## Style commands (app must be running)

### `style-transfer`

Apply a `.lines` style to images.

```bash
# Single style across all images
vexy-lines-cli style-transfer --style look.lines --input-dir ./frames/

# Interpolate between two styles
vexy-lines-cli style-transfer --style start.lines --end-style end.lines \
    --input-dir ./frames/ --output-dir ./out/

# Explicit image list
vexy-lines-cli style-transfer --style look.lines --images a.jpg b.jpg c.jpg
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--style` | (required) | Source style `.lines` file |
| `--end-style` | (none) | End style for interpolation |
| `--images` | (none) | Explicit list of image paths |
| `--input-dir` | (none) | Directory of images (jpg, jpeg, png) |
| `--output-dir` | `./output` | Where to write output |
| `--format` | `svg` | `svg`, `png`, or `jpg` |
| `--dpi` | `72` | Document DPI for rendering |
| `--host` | `127.0.0.1` | MCP server address |
| `--port` | `47384` | MCP server port |
| `--force` | `False` | Delete existing job folder and start fresh |
| `--cleanup` | `False` | Delete job folder after export completes |

### `style-video`

Apply a style to every frame of a video.

```bash
vexy-lines-cli style-video --style look.lines --input clip.mp4 --output result.mp4
vexy-lines-cli style-video --style start.lines --end-style end.lines --input clip.mp4
```

Requires `vexy-lines-run` (includes PyAV, OpenCV, and resvg).

Options:

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--style` | `str` | (required) | Source style `.lines` file |
| `--end-style` | `str` | (none) | End style for interpolation |
| `--input` | `str` | (required) | Input video path |
| `--output` | `str` | (none) | Output video path |
| `--host` | `str` | `127.0.0.1` | MCP server address |
| `--port` | `int` | `47384` | MCP server port |
| `--force` | `bool` | `False` | Delete existing job folder and start fresh |
| `--cleanup` | `bool` | `False` | Delete job folder after export completes |

## MCP commands (app must be running)

### `mcp-status`

Check MCP server connectivity.

```bash
vexy-lines-cli mcp-status
vexy-lines-cli mcp-status --host 192.168.1.10 --port 47384
```

### `tree`

Print the live document layer tree.

```bash
vexy-lines-cli tree
vexy-lines-cli tree --json-output
```

### `new-document`

Create a new document.

```bash
vexy-lines-cli new-document --width 210 --height 297 --dpi 300
vexy-lines-cli new-document --source-image photo.jpg
```

### `open`

Open a `.lines` file.

```bash
vexy-lines-cli open artwork.lines
```

### `add-fill`

Add a fill to a layer.

```bash
vexy-lines-cli add-fill 42 linear --color "#ff0000"
```

### `render`

Trigger a full render.

```bash
vexy-lines-cli render
```

All MCP commands accept `--host` and `--port` (defaults: `127.0.0.1:47384`).

## Bridge

### `mcp-serve`

Start the stdio-to-TCP bridge for Claude Desktop / Cursor.

```bash
vexy-lines-cli mcp-serve
vexy-lines-cli mcp-serve --no-launch
vexy-lines-mcp   # same thing, as an installed script
```

## Global flags

All commands support `--verbose` for debug logging.

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

## AI rename (auto-launches app + needs a vision model)

### `ai-rename`

Rename a `.lines` file's [layers and fills](https://help.vexy.art/lines/articles/layers-panel/) using a vision-language model (VLM). Each fill is rendered in isolation, shown to the model inside a red box over a faint copy of the full artwork, and given a short descriptive caption (e.g. `car-on-road`, `top-sky-bridge`); each layer is then named from the fills it contains. Only the `caption` attributes change -- every fill parameter, mask, mesh, and embedded image is preserved.

```bash
vexy-lines-cli ai-rename road-12.lines
vexy-lines-cli ai-rename road-12.lines road-12-named.lines
vexy-lines-cli ai-rename road-12.lines --dry-run
vexy-lines-cli ai-rename road-12.lines --json-output
vexy-lines-cli ai-rename road-12.lines \
    --llm-api-url http://127.0.0.1:1234/v1 --llm-model-vision my-vision-model
```

`INPUT` is required; `OUTPUT` defaults to `<stem>-renamed.lines`. The command needs both the Vexy Lines app (auto-launched) and an OpenAI-compatible `/v1` endpoint. The endpoint is configured from the environment -- `VEXY_LINES_LLM_API_URL`, `VEXY_LINES_LLM_API_KEY`, `VEXY_LINES_LLM_MODEL_VISION` (vision), and `VEXY_LINES_VLM_MODEL` (text) -- and the `--llm-*` flags below override whatever the environment resolves.

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--dpi` | `72` | Render DPI (lower is faster) |
| `--llm-api-url` | `$VEXY_LINES_LLM_API_URL` | OpenAI-compatible base URL |
| `--llm-api-key` | `$VEXY_LINES_LLM_API_KEY` | API key |
| `--llm-model-vision` | `$VEXY_LINES_LLM_MODEL_VISION` | Vision model (describes each fill) |
| `--llm-model` | `$VEXY_LINES_VLM_MODEL` | Text model (names each layer) |
| `--workdir` | `<stem>-rename/` | Directory for render artifacts |
| `--dry-run` | `False` | Compute names but write nothing |
| `--json-output` | `False` | Print the full plan as JSON |
| `--host` | `127.0.0.1` | MCP server address |
| `--port` | `47384` | MCP server port |

By default the command prints one line per fill (`fill <id>: 'old' -> 'new'  (description)`), one per layer, and the output path. With `--json-output` it prints the full plan dict (keys: `lines_path`, `fills[]`, `layers[]`, `output`, `dry_run`).

Artifacts land in the work dir: `_full.png` (all-fills render), `fill_<id>_single.png` (each fill in isolation), `fill_<id>_inspect.png` (each red-boxed inspection image), and `rename-plan.json`.

Requires the AI extras:

```bash
pip install "vexy-lines-cli[ai]"   # openai + pathvalidate + python-slugify
```

See the [full AI rename guide](https://vexy.dev/vexy-lines-apy/ai-rename/) for how it works and how to choose a model. Vexy Lines help: [Layers Panel](https://help.vexy.art/lines/articles/layers-panel/) · [Fill Properties](https://help.vexy.art/lines/articles/fill-properties-1/).

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

# Examples

## Inspect a .lines file

```bash
$ vexy-lines info artwork.lines
{'caption': 'Landscape', 'version': '4.0', 'dpi': 300,
 'width_mm': 210.0, 'height_mm': 148.0,
 'groups': 2, 'layers': 5, 'fills': 8,
 'has_source_image': True, 'has_preview_image': True}
```

JSON output for scripting:

```bash
$ vexy-lines info artwork.lines --json-output
{
  "caption": "Landscape",
  "version": "4.0",
  "dpi": 300,
  ...
}
```

## Browse the layer tree

```bash
$ vexy-lines file-tree artwork.lines
group: Background
  layer: Sky
    fill: Blue gradient [linear]
    fill: Cloud texture [scribble]
  layer: Ground
    fill: Grass [wave]
group: Foreground
  layer: Tree [hidden]
    fill: Bark [handmade]
    fill: Leaves [fractals]
```

## Extract embedded images

```bash
# Source image (the original photo)
$ vexy-lines extract-source artwork.lines
{'status': 'ok', 'output': 'artwork-src.jpg'}

# Preview image (the rendered thumbnail)
$ vexy-lines extract-preview artwork.lines
{'status': 'ok', 'output': 'artwork-preview.png'}
```

## Batch extract previews

```bash
$ vexy-lines batch-convert --input-dir ./artwork/ --output-dir ./thumbnails/ --what preview --format jpg
{'total': 42, 'successes': 40, 'failures': 2, 'output_dir': './thumbnails/'}
```

## Export to PDF

Single file:

```bash
$ vexy-lines export artwork.lines --format pdf
```

Entire directory:

```bash
$ vexy-lines export ./artwork/ --format svg --output ./exports/
```

Preview without exporting:

```bash
$ vexy-lines export ./artwork/ --dry-run
```

Force re-export with longer timeouts:

```bash
$ vexy-lines export ./artwork/ --force --timeout-multiplier 2.5
```

## Style transfer

Apply one style to a folder of photos:

```bash
$ vexy-lines style-transfer --style watercolor.lines --input-dir ./photos/ --output-dir ./styled/
{'total': 10, 'successes': 10, 'failures': 0, 'output_dir': './styled/'}
```

Interpolate between two styles across the sequence:

```bash
$ vexy-lines style-transfer \
    --style soft.lines --end-style bold.lines \
    --input-dir ./frames/ --output-dir ./animated/
```

The first image gets `soft.lines`, the last gets `bold.lines`, and everything in between is a linear blend.

## Style video

```bash
$ vexy-lines style-video --style sketch.lines --input clip.mp4 --output styled.mp4
{'status': 'ok', 'input': 'clip.mp4', 'output': 'styled.mp4',
 'width': 1920, 'height': 1080, 'fps': 30.0, 'total_frames': 150}
```

With style interpolation across the video:

```bash
$ vexy-lines style-video \
    --style start.lines --end-style end.lines \
    --input clip.mp4 --output morphing.mp4
```

## MCP status check

```bash
$ vexy-lines mcp-status
{'status': 'ok', 'server_info': {'width_mm': 210.0, ...}}
```

## MCP bridge for Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vexy-lines": {
      "command": "vexy-lines-mcp"
    }
  }
}
```

Now Claude can open, edit, render, and export Vexy Lines documents directly.

## Python scripting

```python
from vexy_lines_cli import VexyLinesCLI

cli = VexyLinesCLI()

# Inspect
info = cli.info("artwork.lines")
print(f"{info['caption']}: {info['layers']} layers, {info['fills']} fills")

# Export
stats = cli.export("./artwork/", format="pdf", verbose=True)
print(f"Exported {stats['success']} files in {stats['total_time']:.1f}s")
```

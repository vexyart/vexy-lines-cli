
[Vexy Lines for Mac & Windows](https://vexy.art/lines/) | [Download](https://www.vexy.art/lines/#buy) | [Buy](https://www.vexy.art/lines/#buy) | [Batch GUI](https://vexy.dev/vexy-lines-run/) | **CLI/MCP** | [API](https://vexy.dev/vexy-lines-apy/) | [.lines format](https://vexy.dev/vexy-lines-py/)

[![Vexy Lines](https://i.vexy.art/vl/websiteart/vexy-lines-hero-poster.png)](https://www.vexy.art/lines/)

# vexy-lines-cli

Command-line interface and MCP bridge for [Vexy Lines](https://vexy.art).

Parse `.lines` files, batch export to PDF/SVG, apply styles to images and video, and connect Claude Desktop or Cursor directly to the Vexy Lines MCP API -- all from the terminal.

## What you can do

**Without the app running:**

- Inspect `.lines` file metadata (caption, DPI, dimensions, layer counts)
- Print the full layer/group/fill hierarchy
- Extract embedded source and preview images
- Batch extract from entire directories

**With the app running:**

- Apply `.lines` styles to images via MCP
- Interpolate between two styles across an image sequence
- Process video frame-by-frame with style transfer
- Export `.lines` files to PDF/SVG without dialog interaction
- Query and manipulate the live document tree

**For AI assistants:**

- Bridge Claude Desktop and Cursor to the Vexy Lines MCP server via stdio

## Quick start

```bash
# Inspect a file (no app needed)
vexy-lines info artwork.lines

# Show the layer tree
vexy-lines file-tree artwork.lines

# Export a folder to PDF (auto-launches the app)
vexy-lines export ./my-art/ --format pdf

# Apply a style to photos
vexy-lines style-transfer --style template.lines --input-dir ./photos/

# Check MCP connectivity
vexy-lines mcp-status
```

Running `vexy-lines` with no arguments launches the GUI (requires `vexy-lines-run`).

## Next steps

- [Installation](installation.md) -- install options and extras
- [CLI Reference](cli-reference.md) -- every subcommand with examples
- [Export Pipeline](export-pipeline.md) -- how dialog-less export works
- [API Reference](api-reference.md) -- Python API for programmatic use
- [Examples](examples.md) -- real-world workflows

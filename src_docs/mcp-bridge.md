# MCP Bridge

`vexy-lines-cli` ships a built-in **stdio-to-TCP bridge** that lets Claude
Desktop, Cursor, and any other MCP-aware AI client talk directly to the Vexy
Lines app running on your machine.

The bridge is exposed as two equivalent entry points:

```bash
vexy-lines-mcp          # installed script — use this in config files
vexy-lines-cli mcp-serve    # same thing, as a CLI subcommand
```

## How it works

```
Claude Desktop  ──stdio──►  vexy-lines-mcp  ──TCP──►  Vexy Lines app
                                                         (localhost:47384)
```

1. The AI client starts `vexy-lines-mcp` as a child process and communicates
   over its stdin/stdout using newline-delimited JSON-RPC (the MCP stdio
   protocol).
2. The bridge forwards every message to the Vexy Lines TCP MCP server on
   `localhost:47384`.
3. Responses from the app flow back the same way.
4. If the app is not running when the bridge starts, it automatically launches
   `Vexy Lines.app` and waits up to 30 seconds for the TCP server to become
   available. Pass `--no-launch` to disable this behaviour.
5. The bridge injects one **local tool** on top of the app's own tool list:
   `export_bundle` — multi-format export plus embedded source image extraction,
   handled entirely by the bridge without round-tripping to the app.

## Claude Desktop setup

Add an entry to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vexy-lines": {
      "command": "vexy-lines-mcp",
      "args": []
    }
  }
}
```

If `vexy-lines-mcp` is not on Claude Desktop's `PATH` (common when installed
in a virtualenv), use the full path instead:

```json
{
  "mcpServers": {
    "vexy-lines": {
      "command": "/path/to/your/venv/bin/vexy-lines-mcp",
      "args": []
    }
  }
}
```

Find the full path with:

```bash
which vexy-lines-mcp
# e.g. /Users/you/.local/bin/vexy-lines-mcp
```

Restart Claude Desktop after editing the config. The Vexy Lines tools appear
in the tool picker the next time you start a conversation.

## Cursor setup

In Cursor's MCP settings (`.cursor/mcp.json` in your project or
`~/.cursor/mcp.json` globally):

```json
{
  "mcpServers": {
    "vexy-lines": {
      "command": "vexy-lines-mcp",
      "args": []
    }
  }
}
```

## Advanced options

```bash
vexy-lines-mcp --host 127.0.0.1 --port 47384   # defaults; change if app uses a different port
vexy-lines-mcp --no-launch                       # skip auto-launch on connection failure
```

Pass flags after `--` when configuring through a JSON config:

```json
{
  "mcpServers": {
    "vexy-lines": {
      "command": "vexy-lines-mcp",
      "args": ["--no-launch"]
    }
  }
}
```

## Tools exposed to the AI

The bridge exposes all tools that the Vexy Lines app registers over its TCP
MCP server, plus one bridge-local tool:

| Tool | Where it runs | Description |
|---|---|---|
| `open_document` | app | Open a `.lines` file |
| `get_document_info` | app | Metadata for the current document |
| `get_layer_tree` | app | Layer/group/fill hierarchy |
| `add_fill` | app | Add a fill to a layer |
| `set_fill_params` | app | Update fill parameters |
| `get_image_filters` | app | Read the image-filter chain |
| `set_image_filters` | app | Replace the image-filter chain |
| `add_image_filter` | app | Append one filter to a chain |
| `remove_image_filter` | app | Remove a filter by index |
| `render_all` | app | Trigger a full render |
| `export_svg` | app | Export the current document as SVG |
| `export_pdf` | app | Export the current document as PDF |
| `export_bundle` | **bridge** | Multi-format export + source image (no app dialog) |

`export_bundle` input schema:

```json
{
  "path": "/absolute/path/to/artwork.lines",
  "output_dir": "/optional/destination/",
  "formats": ["pdf", "svg", "png"],
  "source": true
}
```

## Troubleshooting

**"Cannot connect to Vexy Lines at 127.0.0.1:47384"**
: The app is not running. Start Vexy Lines manually, or remove `--no-launch`
  so the bridge auto-launches it.

**Tools not appearing in Claude Desktop**
: Restart Claude Desktop after editing `claude_desktop_config.json`. Check
  the Claude Desktop log at `~/Library/Logs/Claude/` for connection errors.

**Bridge exits immediately**
: Run `vexy-lines-mcp` in a terminal to see the error output. Common causes
  are a wrong path to the binary or the Vexy Lines TCP server being bound to
  a different port.

# this_file: CHANGELOG.md
# Changelog

All notable changes to `vexy-lines-cli` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are managed by [hatch-vcs](https://github.com/ofek/hatch-vcs) from git tags.

## [1.0.35] — 2026-06-28

### Added
- `extract-sources` subcommand: extracts the document-level source image and
  all group-level source images in one call.
- `style-transfer` and `style-video` `--force` / `--cleanup` flags for job
  folder management (resume-by-default; `--force` restarts; `--cleanup`
  removes the job folder after completion).
- Image-filter subcommands: `get-image-filters`, `set-image-filters`,
  `add-image-filter`, `remove-image-filter`.
- `interpolate-video` and `record-interpolation-screen` subcommands.
- MCP bridge (`vexy-lines-mcp` script): stdio-to-TCP passthrough with a
  local `export_bundle` tool injected on top of the app's own tool list.
- Explicit `vexy-lines-py>=1.0.0` dependency (previously pulled in
  transitively via `vexy-lines-apy`).
- `src_docs/mcp-bridge.md`: Claude Desktop / Cursor setup guide with a
  `claude_desktop_config.json` snippet.

### Changed
- `export-bundle` now uses the shared `MCPClient` context across all files
  in a batch, reducing app-launch overhead.
- `style-transfer` and `style-video` delegate rendering to the shared
  `process_export` pipeline from `vexy-lines-apy`, removing the legacy
  direct-MCP path.
- Minimum Python bumped to 3.11 (from 3.9 in older releases).

### Fixed
- `extract-source` default output path was incorrect when the input path
  contained dots in directory names.

## [1.0.20] — 2026-05-17

### Added
- `ai-rename` subcommand: vision-model-assisted layer/fill renaming
  (requires `vexy-lines-cli[ai]`).
- `interpolate` subcommand: generate one interpolated `.lines` file between
  two compatible documents.
- `mcp-serve` / `vexy-lines-mcp`: initial MCP stdio bridge release.

### Changed
- Refactored export pipeline into `export/config.py`, `export/exporter.py`,
  `export/stats.py`, `export/errors.py` for testability.
- All parser subcommands (`info`, `file-tree`, `extract-*`, `batch-convert`)
  now work without the Vexy Lines app.

## [1.0.0] — 2026-03-01

### Added
- Initial public release on PyPI as `vexy-lines-cli`.
- Fire-based CLI with `info`, `file-tree`, `extract-source`, `extract-preview`,
  `batch-convert`, `export`, `export-bundle`, `style-transfer`, `style-video`,
  `mcp-status`, `tree`, `new-document`, `open`, `add-fill`, `render`.

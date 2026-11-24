# this_file: CHANGELOG.md
# Changelog

All notable changes to `vexy-lines-cli` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions are managed by [hatch-vcs](https://github.com/ofek/hatch-vcs) from git tags.

## [Unreleased]

### Changed
- Documentation builds now use fly-january 0.4.0 or later (remote theme assets).
- Documentation builds now use fly-january 0.3.0 or later.
- PyPI releases use Trusted Publishing (`f0fd6e1`, verified by the 1.0.38 PyPI provenance). The owner must keep the trusted publisher configured for `vexyart/vexy-lines-cli`, workflow `release.yml`, and environment `pypi`.
- Site now uses the fly-january 0.2.1 theme (chrome: vexy)
- Line-edited `README.md` and `src_docs/` in the house style (dash repairs,
  active voice). No command, flag, or code changes. Rebuilt tracked `docs/`.

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

## 2026-10-18: documentation plugins

- Use MaterialX search, inherited metadata and a topic index; keep ordered navigation in awesome-nav.
- The documentation wrapper installs the plugins required by this site.
- Strict documentation build and rendered output checks passed.
- Documentation CI now uses the same isolated ProperDocs/plugin wrapper as local builds.

# Export Pipeline

The `vexy-lines-cli export` command exports `.lines` files to PDF or SVG without interacting with save dialogs. This page explains how it works under the hood.

## The problem

Vexy Lines has no headless export mode. Exporting normally requires: open file, click File > Export, choose format, pick destination, click Save. That's fine for one file. For a hundred, you need automation.

## The solution: plist injection

Instead of automating dialog clicks (fragile, slow), the CLI injects export settings directly into the macOS preferences domain (`com.fontlab.vexy-lines`) using `defaults write`, then triggers the menu item via AppleScript.

## Five-stage pipeline

### 1. Discovery

Find all `.lines` files to export. Input can be a single file or a directory (searched recursively). Files with existing outputs are skipped unless `--force` is set.

### 2. Plist injection

`PlistManager` is a context manager that:

1. Reads the current preferences via `defaults read`
2. Saves a snapshot of the original values
3. Writes the export format and destination path via `defaults write`
4. On exit (success or failure), restores the original preferences

This ensures the app's preferences are never permanently modified.

### 3. App activation

The pipeline quits the running app (if any), waits for it to fully close, then relaunches with the injected preferences. `AppleScriptBridge` handles the quit/launch/wait cycle.

### 4. Per-file export loop

For each `.lines` file:

1. Open the file via AppleScript (`open` command)
2. Wait for the file window to appear (polls window title)
3. Trigger File > Export via the menu item name (`"Export PDF File"` or `"Export SVG File"`)
4. Wait for the export to complete
5. Optionally validate the output file exists and has non-zero size

Failed files are retried up to `--max-retries` times (default 3).

### 5. Cleanup

`PlistManager.__exit__` restores the original preferences. The app is left running with its original settings.

## Timeout control

All internal timeouts scale with `--timeout-multiplier`:

| What | Base timeout | At 2.0x |
|------|-------------|---------|
| App launch | 20s | 40s |
| File window | 20s | 40s |
| Post-action delay | 0.4s | 0.8s |
| Poll interval | 0.2s | 0.4s |

Use higher multipliers on slower machines or when exporting complex files.

## Window watcher

`WindowWatcher` polls the app's window titles via AppleScript to detect when a file has opened and when an export has completed. It uses a configurable poll interval and timeout.

## Error handling

Each file export is wrapped in retry logic:

- Transient failures (window didn't appear, menu item failed) are retried
- Persistent failures are logged and counted
- The pipeline continues to the next file on failure
- Final stats report: processed, succeeded, skipped, failed

## Stats

The `ExportStats` dataclass tracks timing and counts:

```python
stats = exporter.export(Path("./art/"))
print(stats.human_summary())
# "Exported 42 files (3 skipped, 1 failed) in 2m 15s"
```

## macOS only

The export pipeline depends on:

- `defaults` command (macOS preferences system)
- AppleScript (`osascript`) for app automation
- The Vexy Lines macOS app

It does not work on Windows or Linux. For cross-platform export, use the MCP API directly via `MCPClient.export_document()`.

## Style export pipeline (job folders)

The `style-transfer` and `style-video` commands use a different pipeline from `export`. Instead of plist injection, they use the MCP API to apply styles programmatically.

### Job folder

Every style export creates a persistent **job folder** alongside the output:

| Output type | Output path | Job folder |
|-------------|-------------|------------|
| Video | `./06/styled.mp4` | `./06/styled-vljob/` |
| Frames | `./output/` | `./output-vljob/` |
| Images | `./results/` | `./results-vljob/` |

The job folder stores the complete artifact chain for each processed item:

| Step | File pattern | Description |
|------|-------------|-------------|
| 1 | `src--{stem}--{N}.png` | Raw decoded video frame (video only) |
| 2 | `{stem}--{N}.lines` | Styled `.lines` document from Vexy Lines |
| 3 | `{stem}--{N}.svg` | SVG export |
| 4 | `{stem}--{N}.png` | Rasterized output |
| 5 | `{stem}.mp4` | Assembled video (MP4 only) |

Frame numbers are 1-based and not zero-padded.

### Resume

Re-running the same command skips items whose final output already exists in the job folder. This makes long video jobs crash-safe — a 4-hour render that fails at frame 147/192 resumes from frame 148.

### Flags

- `--force`: Delete the job folder and start from scratch.
- `--cleanup`: Delete the job folder after the final output is copied to its destination.

### Environment

Set `VEXY_LINES_JOB_FOLDER` to override the computed job folder path.

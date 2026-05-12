# this_file: vexy-lines-cli/src/vexy_lines_cli/__init__.py
"""vexy-lines-cli: command-line tools and MCP passthrough for Vexy Lines.

Three capability groups, all under the ``vexy-lines-cli`` command:

**Parser** (no app required)
  ``info``, ``file-tree``, ``extract-source``, ``extract-preview``,
  ``batch-convert`` — read ``.lines`` files on any platform.

**Export** (auto-launches the macOS app)
  ``export`` — inject prefs, trigger ``File > Export``, collect PDF/SVG.
  Uses dialog-less plist injection; no GUI interaction needed.

**Style & MCP** (app must be running)
  ``style-transfer``, ``style-video`` — apply a ``.lines`` style to
  images or video via the MCP API.
  ``mcp-status``, ``tree``, ``new-document``, ``open``, ``add-fill``,
  ``render`` — direct JSON-RPC calls to the embedded server.

All parser commands accept ``--json-output`` for machine-readable output.
All style commands create a crash-safe job folder; re-running resumes
from where it left off. Use ``--force`` to start fresh.

Usage::

    vexy-lines-cli info artwork.lines
    vexy-lines-cli export ./art/ --format pdf --output ./pdf-out/
    vexy-lines-cli style-transfer --style look.lines --input-dir ./photos/
    vexy-lines-cli mcp-status
"""

from __future__ import annotations

from vexy_lines_cli.__main__ import VexyLinesCLI, main

__all__ = [
    "VexyLinesCLI",
    "main",
]

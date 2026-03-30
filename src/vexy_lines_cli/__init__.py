# this_file: vexy-lines-cli/src/vexy_lines_cli/__init__.py
"""vexy-lines-cli: CLI tool and MCP passthrough server for Vexy Lines.

Provides a command-line interface for parsing .lines files, applying styles
via the MCP API, batch exporting, and automating the Vexy Lines application.

Usage::

    vexy-lines info artwork.lines
    vexy-lines export ./my-art/ --format pdf
    vexy-lines style-transfer --style template.lines --input-dir ./photos/
"""

from __future__ import annotations

from vexy_lines_cli.__main__ import VexyLinesCLI, main

__all__ = [
    "VexyLinesCLI",
    "main",
]

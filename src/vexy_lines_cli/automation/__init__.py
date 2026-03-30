# this_file: vexy-lines-cli/src/vexy_lines_cli/automation/__init__.py
"""Automation modules for Vexy Lines app control."""

from __future__ import annotations

from vexy_lines_cli.automation.bridges import AppleScriptBridge, ApplicationBridge
from vexy_lines_cli.automation.window_watcher import WindowWatcher

__all__ = [
    "AppleScriptBridge",
    "ApplicationBridge",
    "WindowWatcher",
]

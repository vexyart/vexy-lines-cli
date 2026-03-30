# this_file: vexy-lines-cli/src/vexy_lines_cli/automation/window_watcher.py
"""Window monitoring utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger

from vexy_lines_cli.export.errors import AutomationError

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


@dataclass
class WindowWatcher:
    """Polls application windows until a condition is met.

    Attributes:
        title_provider: Callable that returns current window titles.
        poll_interval: Seconds between polls.
    """

    title_provider: Callable[[], Sequence[str]]
    poll_interval: float = 0.2

    def get_current_state(self) -> str:
        """Describe current window state for diagnostics."""
        titles = self.title_provider()
        if not titles:
            return "No windows visible"
        return f"Windows: {', '.join(repr(t) for t in titles)}"

    def wait_for_contains(self, needle: str, *, present: bool, timeout: float) -> None:
        """Wait until a window title contains (or stops containing) a substring.

        Args:
            needle: Substring to search for in window titles.
            present: True to wait for appearance, False for disappearance.
            timeout: Maximum seconds to wait.

        Raises:
            AutomationError: If the condition is not met within the timeout.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            titles = self.title_provider()
            has_title = any(needle in title for title in titles)
            if has_title == present:
                return
            time.sleep(self.poll_interval)
        state = "appear" if present else "disappear"
        current_state = self.get_current_state()
        msg = f"Timed out waiting for '{needle}' to {state}. Current state: {current_state}"
        logger.error(msg)
        raise AutomationError(msg, "WINDOW_TIMEOUT")

    def wait_for_any(self, timeout: float) -> None:
        """Wait until at least one window is visible.

        Args:
            timeout: Maximum seconds to wait.

        Raises:
            AutomationError: If no window appears within the timeout.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.title_provider():
                return
            time.sleep(self.poll_interval)
        msg = "Timed out waiting for the application window"
        raise AutomationError(msg, "APP_NOT_FOUND")

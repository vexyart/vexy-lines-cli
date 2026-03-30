# this_file: vexy-lines-cli/src/vexy_lines_cli/utils/interrupt.py
"""Interrupt handling for graceful shutdowns."""

from __future__ import annotations

import signal
import sys
from typing import Any

from loguru import logger


class InterruptHandler:
    """Gracefully handle Ctrl+C interruptions.

    First Ctrl+C sets a flag for cooperative shutdown.
    Second Ctrl+C forces immediate exit.
    """

    def __init__(self) -> None:
        self.interrupted = False
        self.original_handler = signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, _sig: int, _frame: Any) -> None:  # noqa: ANN401
        """Handle SIGINT: first sets flag, second force-quits."""
        if not self.interrupted:
            self.interrupted = True
            logger.warning("\nInterrupt received. Finishing current file...")
            logger.info("Press Ctrl+C again to force quit")
        else:
            logger.error("\nForce quit!")
            sys.exit(1)

    def restore(self) -> None:
        """Restore the original signal handler."""
        signal.signal(signal.SIGINT, self.original_handler)

    def check(self) -> bool:
        """Check if we should stop processing.

        Returns:
            True if an interrupt has been received.
        """
        return self.interrupted

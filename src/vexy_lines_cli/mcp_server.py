# this_file: vexy-lines-cli/src/vexy_lines_cli/mcp_server.py
"""MCP passthrough server: stdio <-> TCP bridge for Vexy Lines.

Bridges Claude Desktop / Cursor (which expect stdio-based MCP servers) to
the Vexy Lines embedded TCP server on localhost:47384.

Usage::

    vexy-lines-mcp          # as installed script
    vexy-lines mcp-serve    # as CLI subcommand
"""

from __future__ import annotations

import socket
import sys
import time
from typing import TextIO

from loguru import logger

from vexy_lines_api.client import APP_NAME, MCP_PORT, MCPError

_CONNECT_TIMEOUT = 30.0
_SOCKET_TIMEOUT = 120.0
_RECONNECT_DELAY = 1.0
_MAX_RECONNECT_ATTEMPTS = 3


def _connect(host: str, port: int, timeout: float = _CONNECT_TIMEOUT) -> socket.socket:
    """Connect to the MCP TCP server, retrying with backoff."""
    deadline = time.monotonic() + timeout
    interval = 0.5
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(_SOCKET_TIMEOUT)
            sock.connect((host, port))
            logger.debug("Connected to {}:{}", host, port)
            return sock
        except OSError as exc:
            last_error = exc
            sock.close()
            time.sleep(interval)
            interval = min(interval * 1.5, 2.0)
    msg = f"Cannot connect to {APP_NAME} at {host}:{port}: {last_error}"
    raise MCPError(msg)


def _try_launch_app() -> None:
    """Attempt to launch the Vexy Lines app."""
    import subprocess  # noqa: PLC0415

    if sys.platform == "darwin":
        subprocess.run(  # noqa: S603
            ["open", "-a", APP_NAME],  # noqa: S607
            capture_output=True,
            timeout=10,
            check=False,
        )
    else:
        logger.warning("Auto-launch not supported on {}. Start {} manually.", sys.platform, APP_NAME)


def serve(
    host: str = "127.0.0.1",
    port: int = MCP_PORT,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    auto_launch: bool = True,
) -> None:
    """Run the stdio-to-TCP bridge.

    Reads newline-delimited JSON-RPC messages from stdin, forwards them
    to the TCP server, reads responses, and writes them to stdout.

    Args:
        host: TCP server address.
        port: TCP server port.
        stdin: Input stream (default sys.stdin).
        stdout: Output stream (default sys.stdout).
        auto_launch: Launch the app if TCP connection fails.
    """
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout

    sock: socket.socket | None = None
    tcp_buffer = b""

    try:
        # Initial connection
        try:
            sock = _connect(host, port)
        except MCPError:
            if auto_launch:
                logger.info("Launching {}...", APP_NAME)
                _try_launch_app()
                sock = _connect(host, port)
            else:
                raise

        # Main message loop
        for line in stdin:
            line = line.strip()
            if not line:
                continue

            # Forward stdin message to TCP
            try:
                sock.sendall((line + "\n").encode("utf-8"))
            except OSError:
                logger.warning("TCP connection lost, reconnecting...")
                sock.close()
                sock = _connect(host, port)
                sock.sendall((line + "\n").encode("utf-8"))

            # Read response from TCP
            response_line: str | None = None
            while True:
                newline_pos = tcp_buffer.find(b"\n")
                if newline_pos != -1:
                    response_line = tcp_buffer[:newline_pos].decode("utf-8")
                    tcp_buffer = tcp_buffer[newline_pos + 1 :]
                    break
                try:
                    chunk = sock.recv(4096)
                except socket.timeout:
                    logger.error("Timeout waiting for TCP response")
                    break
                if not chunk:
                    logger.error("TCP connection closed")
                    break
                tcp_buffer += chunk
            else:
                continue

            # Forward TCP response to stdout
            if response_line is not None:
                stdout.write(response_line + "\n")
                stdout.flush()

    except KeyboardInterrupt:
        logger.info("Shutting down MCP bridge")
    finally:
        if sock is not None:
            sock.close()


def main() -> None:
    """Entry point for the vexy-lines-mcp script."""
    logger.disable("vexy_lines_cli")
    serve()


if __name__ == "__main__":
    main()

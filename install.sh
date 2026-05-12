#!/usr/bin/env bash
# install.sh - Install vexy-lines-cli in editable mode
# Vexy Lines is a macOS vector art application.
# CLI tool and MCP passthrough server for Vexy Lines.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing vexy-lines-cli in editable mode..."
uv pip install --system -e .

echo "==> Install complete."

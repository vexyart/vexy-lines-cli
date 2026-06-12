# this_file: vexy-lines-cli/tests/test_mcp_server.py
"""Tests for the MCP bridge's local export_bundle tool handling."""

from __future__ import annotations

import json
from unittest.mock import patch

from vexy_lines_cli.mcp_server import _augment_tools_list, _handle_bundle_call


class TestAugmentToolsList:
    def test_augment_when_tools_list_then_appends_bundle(self):
        response = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "open_document"}]}})
        patched = json.loads(_augment_tools_list(response))
        names = [t["name"] for t in patched["result"]["tools"]]
        assert names == ["open_document", "export_bundle"]

    def test_augment_when_not_json_then_passthrough(self):
        assert _augment_tools_list("not json") == "not json"

    def test_augment_when_no_tools_key_then_passthrough(self):
        response = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {}})
        assert _augment_tools_list(response) == response


class TestHandleBundleCall:
    def test_handle_when_bundle_succeeds_then_returns_paths(self, tmp_path):
        out = {"pdf": tmp_path / "a.pdf", "source": tmp_path / "a-src.jpg"}
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {"name": "export_bundle", "arguments": {"path": str(tmp_path / "a.lines")}},
        }
        with patch("vexy_lines_api.bundle.export_bundle", return_value=out):
            response = _handle_bundle_call(request)
        assert response["id"] == 7
        payload = json.loads(response["result"]["content"][0]["text"])
        assert payload == {"pdf": str(out["pdf"]), "source": str(out["source"])}

    def test_handle_when_bundle_raises_then_is_error(self):
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {"name": "export_bundle", "arguments": {"path": "/nope/missing.lines"}},
        }
        with patch("vexy_lines_api.bundle.export_bundle", side_effect=FileNotFoundError("missing")):
            response = _handle_bundle_call(request)
        assert response["result"]["isError"] is True
        assert "missing" in response["result"]["content"][0]["text"]

    def test_handle_when_no_arguments_then_is_error(self):
        request = {"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "export_bundle"}}
        response = _handle_bundle_call(request)
        assert response["result"]["isError"] is True

# this_file: vexy-lines-cli/tests/test_cli.py
"""Tests for VexyLinesCLI subcommands and helper functions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vexy_lines_cli.__main__ import VexyLinesCLI, _count_tree, _format_file_tree, _format_tree
from vexy_lines import (
    DocumentProps,
    FillNode,
    FillParams,
    GroupInfo,
    LayerInfo,
    LinesDocument,
)


# ---------------------------------------------------------------------------
# Helper factories using real types from vexy_lines
# ---------------------------------------------------------------------------


def _make_fill(caption: str = "Fill 1", fill_type: str = "linear") -> FillNode:
    return FillNode(xml_tag="LinearStrokesTmpl", caption=caption, params=FillParams(fill_type=fill_type, color="#000000"))


def _make_layer(caption: str = "Layer 1", visible: bool = True, fills: list | None = None) -> LayerInfo:
    return LayerInfo(caption=caption, visible=visible, fills=fills or [])


def _make_group(caption: str = "Group 1", children: list | None = None) -> GroupInfo:
    return GroupInfo(caption=caption, children=children or [])


@dataclass
class FakeLayerNode:
    type: str = "layer"
    caption: str = "Layer"
    id: int = 1
    fill_type: str | None = None
    visible: bool = True
    children: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# _format_tree tests
# ---------------------------------------------------------------------------


class TestFormatTree:
    def test_format_tree_single_node(self):
        node = FakeLayerNode(type="layer", caption="BG", id=1, fill_type=None, visible=True)
        result = _format_tree(node)
        assert "layer: BG (id=1)" in result

    def test_format_tree_with_fill_type(self):
        node = FakeLayerNode(type="fill", caption="Fill", id=2, fill_type="linear")
        result = _format_tree(node)
        assert "[linear]" in result

    def test_format_tree_hidden_node(self):
        node = FakeLayerNode(type="layer", caption="Hidden", id=3, visible=False)
        result = _format_tree(node)
        assert "[hidden]" in result

    def test_format_tree_nested_children(self):
        child = FakeLayerNode(type="fill", caption="Child", id=10)
        parent = FakeLayerNode(type="group", caption="Parent", id=5, children=[child])
        result = _format_tree(parent)
        lines = result.split("\n")
        assert len(lines) == 2
        assert "Parent" in lines[0]
        assert "  " in lines[1]  # indented


# ---------------------------------------------------------------------------
# _format_file_tree tests
# ---------------------------------------------------------------------------


class TestFormatFileTree:
    def test_format_file_tree_empty(self):
        result = _format_file_tree([])
        assert result == ""

    def test_format_file_tree_with_layer(self):
        layer = _make_layer(caption="BG Layer", visible=True, fills=[])
        with patch("vexy_lines_cli.__main__.isinstance") if False else _noop():
            result = _format_file_tree([layer])
        assert "layer: BG Layer" in result

    def test_format_file_tree_hidden_layer(self):
        layer = _make_layer(caption="Secret", visible=False)
        result = _format_file_tree([layer])
        assert "[hidden]" in result

    def test_format_file_tree_with_fills(self):
        fill = _make_fill(caption="Stripes", fill_type="wave")
        layer = _make_layer(caption="Art", fills=[fill])
        result = _format_file_tree([layer])
        assert "fill: Stripes [wave]" in result

    def test_format_file_tree_nested_group(self):
        layer = _make_layer(caption="Inner")
        group = _make_group(caption="Outer", children=[layer])
        result = _format_file_tree([group])
        assert "group: Outer" in result
        assert "layer: Inner" in result


# ---------------------------------------------------------------------------
# _count_tree tests
# ---------------------------------------------------------------------------


class TestCountTree:
    def test_count_tree_empty(self):
        assert _count_tree([]) == (0, 0, 0)

    def test_count_tree_single_layer_no_fills(self):
        layer = _make_layer(caption="L", fills=[])
        assert _count_tree([layer]) == (0, 1, 0)

    def test_count_tree_layer_with_fills(self):
        fills = [_make_fill(), _make_fill()]
        layer = _make_layer(caption="L", fills=fills)
        assert _count_tree([layer]) == (0, 1, 2)

    def test_count_tree_group_with_layers(self):
        layer1 = _make_layer(caption="L1", fills=[_make_fill()])
        layer2 = _make_layer(caption="L2", fills=[])
        group = _make_group(caption="G", children=[layer1, layer2])
        g, l, f = _count_tree([group])
        assert g == 1
        assert l == 2
        assert f == 1

    def test_count_tree_nested_groups(self):
        inner_layer = _make_layer(caption="IL", fills=[_make_fill()])
        inner_group = _make_group(caption="IG", children=[inner_layer])
        outer_group = _make_group(caption="OG", children=[inner_group])
        g, l, f = _count_tree([outer_group])
        assert g == 2  # outer + inner
        assert l == 1
        assert f == 1


# ---------------------------------------------------------------------------
# VexyLinesCLI.info tests
# ---------------------------------------------------------------------------


class TestCliInfo:
    def test_info_returns_metadata(self):
        doc = LinesDocument(
            caption="Art",
            version="2.0",
            dpi=150,
            groups=[_make_layer(fills=[_make_fill()])],
            source_image_data=b"img",
            preview_image_data=None,
        )
        with patch("vexy_lines_cli.__main__.parse_lines", return_value=doc):
            cli = VexyLinesCLI()
            result = cli.info("fake.lines")
        assert result["caption"] == "Art"
        assert result["dpi"] == 150
        assert result["layers"] == 1
        assert result["fills"] == 1
        assert result["has_source_image"] is True
        assert result["has_preview_image"] is False

    def test_info_returns_error_on_failure(self):
        with patch("vexy_lines_cli.__main__.parse_lines", side_effect=FileNotFoundError("nope")):
            cli = VexyLinesCLI()
            result = cli.info("missing.lines")
        assert "error" in result

    def test_info_json_output(self, capsys):
        doc = LinesDocument(groups=[])
        with patch("vexy_lines_cli.__main__.parse_lines", return_value=doc):
            cli = VexyLinesCLI()
            cli.info("fake.lines", json_output=True)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "caption" in data


# ---------------------------------------------------------------------------
# VexyLinesCLI.file_tree tests
# ---------------------------------------------------------------------------


class TestCliFileTree:
    def test_file_tree_text_output(self):
        layer = _make_layer(caption="BG")
        doc = LinesDocument(groups=[layer])
        with patch("vexy_lines_cli.__main__.parse_lines", return_value=doc):
            cli = VexyLinesCLI()
            result = cli.file_tree("fake.lines")
        assert "layer: BG" in result

    def test_file_tree_error_returns_string(self):
        with patch("vexy_lines_cli.__main__.parse_lines", side_effect=ValueError("bad")):
            cli = VexyLinesCLI()
            result = cli.file_tree("bad.lines")
        assert "bad" in result


# ---------------------------------------------------------------------------
# VexyLinesCLI.extract_source / extract_preview tests
# ---------------------------------------------------------------------------


class TestCliExtract:
    def test_extract_source_success(self, tmp_path):
        out = tmp_path / "out.jpg"
        with patch("vexy_lines_cli.__main__.extract_source_image", return_value=out):
            cli = VexyLinesCLI()
            result = cli.extract_source(str(tmp_path / "in.lines"))
        assert result["status"] == "ok"

    def test_extract_source_error(self):
        with patch("vexy_lines_cli.__main__.extract_source_image", side_effect=FileNotFoundError("nope")):
            cli = VexyLinesCLI()
            result = cli.extract_source("missing.lines")
        assert "error" in result

    def test_extract_preview_success(self, tmp_path):
        out = tmp_path / "out.png"
        with patch("vexy_lines_cli.__main__.extract_preview_image", return_value=out):
            cli = VexyLinesCLI()
            result = cli.extract_preview(str(tmp_path / "in.lines"))
        assert result["status"] == "ok"

    def test_extract_preview_error(self):
        with patch("vexy_lines_cli.__main__.extract_preview_image", side_effect=ValueError("no preview")):
            cli = VexyLinesCLI()
            result = cli.extract_preview("missing.lines")
        assert "error" in result


# ---------------------------------------------------------------------------
# VexyLinesCLI.export argument validation tests
# ---------------------------------------------------------------------------


class TestCliExportValidation:
    def test_export_rejects_low_timeout_multiplier(self):
        cli = VexyLinesCLI()
        with pytest.raises(ValueError, match="timeout_multiplier"):
            cli.export("fake.lines", timeout_multiplier=0.01)

    def test_export_rejects_high_timeout_multiplier(self):
        cli = VexyLinesCLI()
        with pytest.raises(ValueError, match="timeout_multiplier"):
            cli.export("fake.lines", timeout_multiplier=99.0)

    def test_export_rejects_negative_max_retries(self):
        cli = VexyLinesCLI()
        with pytest.raises(ValueError, match="max_retries"):
            cli.export("fake.lines", max_retries=-1)

    def test_export_rejects_excessive_max_retries(self):
        cli = VexyLinesCLI()
        with pytest.raises(ValueError, match="max_retries"):
            cli.export("fake.lines", max_retries=11)


# ---------------------------------------------------------------------------
# VexyLinesCLI.batch_convert tests
# ---------------------------------------------------------------------------


class TestCliBatchConvert:
    def test_batch_convert_invalid_what(self, tmp_path):
        cli = VexyLinesCLI()
        result = cli.batch_convert(input_dir=str(tmp_path), what="invalid")
        assert result["error"] == "invalid what: invalid"

    def test_batch_convert_no_files(self, tmp_path):
        cli = VexyLinesCLI()
        result = cli.batch_convert(input_dir=str(tmp_path))
        assert "no .lines files found" in result["error"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _noop:
    """No-op context manager for conditional patching."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

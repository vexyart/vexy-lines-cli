# this_file: vexy-lines-cli/tests/test_cli_ai_rename.py
"""Tests for the `ai_rename` CLI subcommand."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from vexy_lines_api import MCPError
from vexy_lines_api.rename import FillRename, LayerRename, RenamePlan
from vexy_lines_cli.__main__ import VexyLinesCLI

if TYPE_CHECKING:
    from pathlib import Path


def _plan(src: Path) -> RenamePlan:
    return RenamePlan(
        lines_path=src,
        fills=[
            FillRename(100, "L1", "linear", 10, "top left lines", "top-left-lines"),
            FillRename(101, "C1", "circular", 10, "round center dots", "round-center-dots"),
        ],
        layers=[LayerRename(10, "Layer 1", [100, 101], "the background", "the-background")],
    )


def test_ai_rename_invokes_engine_and_returns_summary(tmp_path: Path):
    src = tmp_path / "demo.lines"
    src.write_text("<Project/>", encoding="utf-8")
    plan = _plan(src)

    with (
        patch("vexy_lines_cli.__main__.MCPClient") as client_cls,
        patch("vexy_lines_api.rename.rename_lines", return_value=plan) as rl,
    ):
        client = client_cls.return_value.__enter__.return_value
        result = VexyLinesCLI().ai_rename(str(src), dpi=72)

    assert rl.call_count == 1
    # client was passed through to the engine
    _, kwargs = rl.call_args
    assert kwargs["client"] is client
    assert kwargs["dpi"] == 72
    assert result["output"] == str(src.with_name("demo-renamed.lines"))
    assert result["dry_run"] is False
    assert len(result["fills"]) == 2
    assert result["layers"][0]["new_caption"] == "the-background"


def test_ai_rename_dry_run_sets_output_none(tmp_path: Path):
    src = tmp_path / "demo.lines"
    src.write_text("<Project/>", encoding="utf-8")
    plan = _plan(src)

    with (
        patch("vexy_lines_cli.__main__.MCPClient"),
        patch("vexy_lines_api.rename.rename_lines", return_value=plan) as rl,
    ):
        result = VexyLinesCLI().ai_rename(str(src), dry_run=True)

    assert result["output"] is None
    assert result["dry_run"] is True
    _, kwargs = rl.call_args
    assert kwargs["dry_run"] is True


def test_ai_rename_applies_config_overrides(tmp_path: Path):
    src = tmp_path / "demo.lines"
    src.write_text("<Project/>", encoding="utf-8")
    plan = _plan(src)

    with (
        patch("vexy_lines_cli.__main__.MCPClient"),
        patch("vexy_lines_api.rename.rename_lines", return_value=plan) as rl,
    ):
        VexyLinesCLI().ai_rename(
            str(src),
            llm_api_url="http://host:9/v1",
            llm_api_key="secret",
            llm_model_vision="my-vision",
            llm_model="my-text",
        )

    _, kwargs = rl.call_args
    config = kwargs["config"]
    assert config.api_url == "http://host:9/v1"
    assert config.api_key == "secret"
    assert config.model_vision == "my-vision"
    assert config.model == "my-text"


def test_ai_rename_reports_mcp_error(tmp_path: Path):
    src = tmp_path / "demo.lines"
    src.write_text("<Project/>", encoding="utf-8")

    with (
        patch("vexy_lines_cli.__main__.MCPClient") as client_cls,
        patch("vexy_lines_api.rename.rename_lines", side_effect=MCPError("no app")),
    ):
        client_cls.return_value.__enter__.return_value = client_cls.return_value
        result = VexyLinesCLI().ai_rename(str(src))

    assert "no app" in result["error"]


def test_ai_rename_custom_output_path(tmp_path: Path):
    src = tmp_path / "demo.lines"
    src.write_text("<Project/>", encoding="utf-8")
    out = tmp_path / "named.lines"
    plan = _plan(src)

    with (
        patch("vexy_lines_cli.__main__.MCPClient"),
        patch("vexy_lines_api.rename.rename_lines", return_value=plan) as rl,
    ):
        result = VexyLinesCLI().ai_rename(str(src), str(out))

    assert result["output"] == str(out)
    args, _ = rl.call_args
    # second positional arg is the output path passed to rename_lines
    assert args[1] == out

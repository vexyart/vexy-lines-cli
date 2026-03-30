# this_file: vexy-lines-cli/tests/test_export.py
"""Tests for the export pipeline: config, stats, errors, file_utils, interrupt."""

from __future__ import annotations

import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from vexy_lines_cli.export.config import (
    MAX_RETRIES,
    MAX_TIMEOUT_MULTIPLIER,
    MIN_RETRIES,
    MIN_TIMEOUT_MULTIPLIER,
    ExportConfig,
)
from vexy_lines_cli.export.errors import (
    AutomationError,
    FileValidationError,
    format_error_with_context,
    get_error_suggestion,
)
from vexy_lines_cli.export.stats import ExportStats
from vexy_lines_cli.utils.file_utils import (
    find_lines_files,
    validate_lines_file,
    validate_pdf,
    validate_svg,
)
from vexy_lines_cli.utils.interrupt import InterruptHandler


# ===========================================================================
# ExportConfig tests
# ===========================================================================


class TestExportConfig:
    def test_default_config_is_valid(self):
        config = ExportConfig()
        assert config.format == "pdf"
        assert config.app_name == "Vexy Lines"
        assert config.timeout_multiplier == 1.0
        assert config.max_retries == 3

    def test_svg_format_accepted(self):
        config = ExportConfig(format="svg")
        assert config.format == "svg"

    def test_format_lowercased(self):
        config = ExportConfig(format="PDF")
        assert config.format == "pdf"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="format must be one of"):
            ExportConfig(format="bmp")

    def test_timeout_multiplier_too_low(self):
        with pytest.raises(ValueError, match="timeout_multiplier"):
            ExportConfig(timeout_multiplier=0.01)

    def test_timeout_multiplier_too_high(self):
        with pytest.raises(ValueError, match="timeout_multiplier"):
            ExportConfig(timeout_multiplier=100.0)

    def test_timeout_multiplier_boundary_low(self):
        config = ExportConfig(timeout_multiplier=MIN_TIMEOUT_MULTIPLIER)
        assert config.timeout_multiplier == MIN_TIMEOUT_MULTIPLIER

    def test_timeout_multiplier_boundary_high(self):
        config = ExportConfig(timeout_multiplier=MAX_TIMEOUT_MULTIPLIER)
        assert config.timeout_multiplier == MAX_TIMEOUT_MULTIPLIER

    def test_max_retries_too_low(self):
        with pytest.raises(ValueError, match="max_retries"):
            ExportConfig(max_retries=-1)

    def test_max_retries_too_high(self):
        with pytest.raises(ValueError, match="max_retries"):
            ExportConfig(max_retries=11)

    def test_max_retries_boundary_zero(self):
        config = ExportConfig(max_retries=MIN_RETRIES)
        assert config.max_retries == 0

    def test_max_retries_boundary_max(self):
        config = ExportConfig(max_retries=MAX_RETRIES)
        assert config.max_retries == MAX_RETRIES

    def test_empty_app_name_raises(self):
        with pytest.raises(ValueError, match="app_name cannot be empty"):
            ExportConfig(app_name="   ")

    def test_custom_app_name(self):
        config = ExportConfig(app_name="My App")
        assert config.app_name == "My App"

    def test_export_menu_item_pdf(self):
        config = ExportConfig(format="pdf")
        assert config.export_menu_item == "Export PDF File"

    def test_export_menu_item_svg(self):
        config = ExportConfig(format="svg")
        assert config.export_menu_item == "Export SVG File"

    def test_export_extension_pdf(self):
        config = ExportConfig(format="pdf")
        assert config.export_extension == ".pdf"

    def test_export_extension_svg(self):
        config = ExportConfig(format="svg")
        assert config.export_extension == ".svg"

    def test_scale_timeout(self):
        config = ExportConfig(timeout_multiplier=2.0)
        assert config.scale_timeout(10.0) == 20.0

    def test_scale_timeout_default(self):
        config = ExportConfig()
        assert config.scale_timeout(5.0) == 5.0


# ===========================================================================
# ExportStats tests
# ===========================================================================


class TestExportStats:
    def test_initial_state(self):
        stats = ExportStats()
        assert stats.processed == 0
        assert stats.success == 0
        assert stats.skipped == 0
        assert stats.failures == []

    def test_record_success(self, tmp_path):
        stats = ExportStats()
        p = tmp_path / "test.lines"
        stats.record_success(p, elapsed=1.5)
        assert stats.processed == 1
        assert stats.success == 1
        assert stats.file_times == [1.5]

    def test_record_success_no_elapsed(self, tmp_path):
        stats = ExportStats()
        stats.record_success(tmp_path / "t.lines")
        assert stats.success == 1
        assert stats.file_times == []

    def test_record_skipped(self, tmp_path):
        stats = ExportStats()
        stats.record_skipped(tmp_path / "t.lines")
        assert stats.skipped == 1
        assert stats.processed == 1

    def test_record_failure(self, tmp_path):
        stats = ExportStats()
        p = tmp_path / "t.lines"
        stats.record_failure(p, "timeout")
        assert len(stats.failures) == 1
        assert stats.failures[0][1] == "timeout"
        assert stats.processed == 1

    def test_record_validation_failure(self, tmp_path):
        stats = ExportStats()
        stats.record_validation_failure(tmp_path / "t.lines", "bad header")
        assert len(stats.validation_failures) == 1

    def test_get_average_time_empty(self):
        stats = ExportStats()
        assert stats.get_average_time() == 0.0

    def test_get_average_time(self, tmp_path):
        stats = ExportStats()
        stats.record_success(tmp_path / "a.lines", elapsed=2.0)
        stats.record_success(tmp_path / "b.lines", elapsed=4.0)
        assert stats.get_average_time() == 3.0

    def test_human_summary_basic(self, tmp_path):
        stats = ExportStats()
        stats.record_success(tmp_path / "a.lines", elapsed=1.0)
        summary = stats.human_summary()
        assert "1/1 exports succeeded" in summary

    def test_human_summary_dry_run(self):
        stats = ExportStats(dry_run=True)
        summary = stats.human_summary()
        assert summary.startswith("dry-run")

    def test_human_summary_with_skips_and_failures(self, tmp_path):
        stats = ExportStats()
        stats.record_success(tmp_path / "a.lines", elapsed=1.0)
        stats.record_skipped(tmp_path / "b.lines")
        stats.record_failure(tmp_path / "c.lines", "err")
        summary = stats.human_summary()
        assert "skipped" in summary
        assert "failed" in summary

    def test_as_dict_structure(self, tmp_path):
        stats = ExportStats()
        stats.record_success(tmp_path / "a.lines", elapsed=1.0)
        d = stats.as_dict()
        assert d["processed"] == 1
        assert d["success"] == 1
        assert d["failed"] == 0
        assert isinstance(d["total_time"], float)

    def test_as_dict_no_average_when_empty(self):
        stats = ExportStats()
        d = stats.as_dict()
        assert d["average_time"] is None


# ===========================================================================
# Error tests
# ===========================================================================


class TestErrors:
    def test_automation_error_attributes(self):
        err = AutomationError("boom", "TEST_CODE")
        assert str(err) == "boom"
        assert err.error_code == "TEST_CODE"

    def test_automation_error_default_code(self):
        err = AutomationError("oops")
        assert err.error_code == "UNKNOWN"

    def test_file_validation_error_is_automation_error(self):
        err = FileValidationError("bad file")
        assert isinstance(err, AutomationError)
        assert err.error_code == "FILE_INVALID"

    def test_get_error_suggestion_known_code(self):
        suggestion = get_error_suggestion("APP_NOT_FOUND")
        assert "Vexy Lines" in suggestion

    def test_get_error_suggestion_unknown_code(self):
        suggestion = get_error_suggestion("TOTALLY_UNKNOWN")
        assert "Check logs" in suggestion

    def test_get_error_suggestion_all_known_codes(self):
        known_codes = [
            "APP_NOT_FOUND", "OPEN_FAILED", "WINDOW_TIMEOUT",
            "EXPORT_MENU_TIMEOUT", "SAVE_DIALOG_TIMEOUT", "EXPORT_TIMEOUT",
            "INVALID_PDF", "FILE_INVALID", "NO_FILES", "USER_INTERRUPT",
            "PLIST_ERROR",
        ]
        for code in known_codes:
            suggestion = get_error_suggestion(code)
            assert suggestion != "Check logs for more details and try again", f"No suggestion for {code}"

    def test_format_error_with_context_basic(self):
        result = format_error_with_context("APP_NOT_FOUND", "Cannot find app")
        assert "Cannot find app" in result
        assert "\u2192" in result  # arrow

    def test_format_error_with_context_with_file(self):
        result = format_error_with_context("OPEN_FAILED", "Cannot open", file_path="/tmp/test.lines")
        assert "File: /tmp/test.lines" in result


# ===========================================================================
# File utils tests
# ===========================================================================


class TestFileUtils:
    def test_find_lines_files_single_file(self, tmp_path):
        f = tmp_path / "art.lines"
        f.write_text("data")
        result = find_lines_files(f)
        assert result == [f]

    def test_find_lines_files_wrong_extension(self, tmp_path):
        f = tmp_path / "art.txt"
        f.write_text("data")
        assert find_lines_files(f) == []

    def test_find_lines_files_directory(self, tmp_path):
        (tmp_path / "a.lines").write_text("a")
        (tmp_path / "b.lines").write_text("b")
        (tmp_path / "c.txt").write_text("c")
        result = find_lines_files(tmp_path)
        assert len(result) == 2

    def test_find_lines_files_nonexistent(self, tmp_path):
        assert find_lines_files(tmp_path / "nope") == []

    def test_validate_lines_file_missing(self, tmp_path):
        with pytest.raises(FileValidationError, match="does not exist"):
            validate_lines_file(tmp_path / "nope.lines")

    def test_validate_lines_file_directory(self, tmp_path):
        with pytest.raises(FileValidationError, match="Not a file"):
            validate_lines_file(tmp_path)

    def test_validate_lines_file_wrong_ext(self, tmp_path):
        f = tmp_path / "art.txt"
        f.write_text("data")
        with pytest.raises(FileValidationError, match="Not a .lines file"):
            validate_lines_file(f)

    def test_validate_lines_file_empty(self, tmp_path):
        f = tmp_path / "art.lines"
        f.write_text("")
        with pytest.raises(FileValidationError, match="empty"):
            validate_lines_file(f)

    def test_validate_lines_file_valid(self, tmp_path):
        f = tmp_path / "art.lines"
        f.write_bytes(b"x" * 100)
        validate_lines_file(f)  # should not raise

    def test_validate_pdf_missing(self, tmp_path):
        assert validate_pdf(tmp_path / "nope.pdf") is False

    def test_validate_pdf_too_small(self, tmp_path):
        f = tmp_path / "tiny.pdf"
        f.write_bytes(b"%PDF-1.4" + b"\x00" * 10)
        assert validate_pdf(f) is False

    def test_validate_pdf_bad_header(self, tmp_path):
        f = tmp_path / "bad.pdf"
        f.write_bytes(b"NOT_A_PDF" + b"\x00" * 2000)
        assert validate_pdf(f) is False

    def test_validate_pdf_valid(self, tmp_path):
        f = tmp_path / "good.pdf"
        f.write_bytes(b"%PDF-1.4" + b"\x00" * 2000)
        assert validate_pdf(f) is True

    def test_validate_svg_missing(self, tmp_path):
        assert validate_svg(tmp_path / "nope.svg") is False

    def test_validate_svg_empty(self, tmp_path):
        f = tmp_path / "empty.svg"
        f.write_text("")
        assert validate_svg(f) is False

    def test_validate_svg_bad_content(self, tmp_path):
        f = tmp_path / "bad.svg"
        f.write_text("this is not svg")
        assert validate_svg(f) is False

    def test_validate_svg_xml_header(self, tmp_path):
        f = tmp_path / "good.svg"
        f.write_text('<?xml version="1.0"?><svg></svg>')
        assert validate_svg(f) is True

    def test_validate_svg_svg_header(self, tmp_path):
        f = tmp_path / "good2.svg"
        f.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        assert validate_svg(f) is True


# ===========================================================================
# InterruptHandler tests
# ===========================================================================


class TestInterruptHandler:
    def test_initial_state_not_interrupted(self):
        handler = InterruptHandler()
        try:
            assert handler.check() is False
        finally:
            handler.restore()

    def test_first_interrupt_sets_flag(self):
        handler = InterruptHandler()
        try:
            handler._handle_interrupt(signal.SIGINT, None)
            assert handler.check() is True
        finally:
            handler.restore()

    def test_second_interrupt_exits(self):
        handler = InterruptHandler()
        try:
            handler._handle_interrupt(signal.SIGINT, None)
            with pytest.raises(SystemExit):
                handler._handle_interrupt(signal.SIGINT, None)
        finally:
            handler.restore()

    def test_restore_resets_handler(self):
        original = signal.getsignal(signal.SIGINT)
        handler = InterruptHandler()
        handler.restore()
        current = signal.getsignal(signal.SIGINT)
        # After restore, should be back to original
        assert current == original

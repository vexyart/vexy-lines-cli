# this_file: vexy-lines-cli/src/vexy_lines_cli/utils/file_utils.py
"""File handling utilities for Vexy Lines automation."""

from __future__ import annotations

from pathlib import Path  # noqa: TCH003

from loguru import logger

from vexy_lines_cli.export.errors import FileValidationError

MIN_PDF_SIZE = 1024
MAX_FILE_SIZE = 500 * 1024 * 1024


def find_lines_files(path: Path) -> list[Path]:
    """Find .lines files at a path (single file or recursive directory search).

    Args:
        path: A .lines file or directory to search recursively.

    Returns:
        Sorted list of .lines file paths.
    """
    if path.is_file() and path.suffix.lower() == ".lines":
        return [path]
    if path.is_dir():
        return sorted(path.rglob("*.lines"))
    return []


def validate_lines_file(path: Path) -> None:
    """Validate that a path is a readable, non-empty .lines file.

    Args:
        path: File path to validate.

    Raises:
        FileValidationError: If the file is missing, not a file, wrong extension, or empty.
    """
    if not path.exists():
        msg = f"File does not exist: {path}"
        raise FileValidationError(msg)
    if not path.is_file():
        msg = f"Not a file: {path}"
        raise FileValidationError(msg)
    if path.suffix.lower() != ".lines":
        msg = f"Not a .lines file: {path}"
        raise FileValidationError(msg)
    try:
        size = path.stat().st_size
        if size == 0:
            msg = f"File is empty: {path}"
            raise FileValidationError(msg)
        if size > MAX_FILE_SIZE:
            logger.warning(f"Large file detected ({size // (1024 * 1024)} MB): {path}")
    except OSError as e:
        msg = f"Cannot access file {path}: {e}"
        raise FileValidationError(msg) from e


def validate_pdf(path: Path) -> bool:
    """Check that a file is a valid PDF (exists, has correct header, reasonable size).

    Args:
        path: Path to the PDF file.

    Returns:
        True if the file passes all checks.
    """
    if not path.exists():
        logger.error(f"PDF does not exist: {path}")
        return False
    if not path.is_file():
        logger.error(f"PDF path is not a file: {path}")
        return False
    try:
        size = path.stat().st_size
        if size < MIN_PDF_SIZE:
            logger.error(f"PDF suspiciously small ({size} bytes): {path}")
            return False
        if size > MAX_FILE_SIZE:
            logger.warning(f"PDF unusually large ({size // (1024 * 1024)} MB): {path}")
        with path.open("rb") as f:
            header = f.read(5)
            if not header.startswith(b"%PDF-"):
                logger.error(f"Invalid PDF header (got {header!r}): {path}")
                return False
        logger.debug(f"PDF validation passed for {path.name} ({size} bytes)")
        return True
    except OSError as e:
        logger.error(f"Cannot access PDF {path}: {e}")
        return False


def validate_svg(path: Path) -> bool:
    """Check that a file is a valid SVG (exists, has XML/SVG header).

    Args:
        path: Path to the SVG file.

    Returns:
        True if the file passes all checks.
    """
    if not path.exists():
        logger.error(f"SVG does not exist: {path}")
        return False
    if not path.is_file():
        logger.error(f"SVG path is not a file: {path}")
        return False
    try:
        size = path.stat().st_size
        if size == 0:
            logger.error(f"SVG is empty: {path}")
            return False
        with path.open("rb") as f:
            header = f.read(256)
            header_str = header.decode("utf-8", errors="ignore").lstrip()
            if not (header_str.startswith("<?xml") or header_str.startswith("<svg")):
                logger.error(f"Invalid SVG content (got {header_str[:40]!r}): {path}")
                return False
        logger.debug(f"SVG validation passed for {path.name} ({size} bytes)")
        return True
    except OSError as e:
        logger.error(f"Cannot access SVG {path}: {e}")
        return False


def validate_export(path: Path, fmt: str) -> bool:
    """Validate an exported file based on its format.

    Args:
        path: Path to the exported file.
        fmt: Export format ('pdf' or 'svg').

    Returns:
        True if the file passes validation for the given format.
    """
    if fmt == "pdf":
        return validate_pdf(path)
    if fmt == "svg":
        return validate_svg(path)
    return False


def expected_export_path(lines_file: Path, fmt: str) -> Path:
    """Derive the expected export output path from a .lines file path.

    Args:
        lines_file: Source .lines file.
        fmt: Export format ('pdf' or 'svg').

    Returns:
        Path with the .lines extension replaced by the format extension.
    """
    return lines_file.with_suffix(f".{fmt}")


def resolve_output_path(input_file: Path, output: Path | None, fmt: str) -> Path | None:
    """Resolve the final output path, handling directory vs file destinations.

    Args:
        input_file: Source .lines file.
        output: User-specified output path (file or directory), or None.
        fmt: Export format ('pdf' or 'svg').

    Returns:
        Resolved output path, or None if no output was specified.
    """
    if output is None:
        return None
    if output.is_dir():
        return output / f"{input_file.stem}.{fmt}"
    return output

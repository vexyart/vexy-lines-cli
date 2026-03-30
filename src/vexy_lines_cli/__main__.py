# this_file: vexy-lines-cli/src/vexy_lines_cli/__main__.py
"""Command-line interface for Vexy Lines."""

from __future__ import annotations

import json as _json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

import fire
from loguru import logger

from vexy_lines import (
    GroupInfo,
    LayerInfo,
    extract_preview_image,
    extract_source_image,
)
from vexy_lines import (
    parse as parse_lines,
)
from vexy_lines_api import MCPClient, MCPError, apply_style, extract_style, interpolate_style, styles_compatible
from vexy_lines_cli.export.config import ExportConfig
from vexy_lines_cli.export.exporter import VexyLinesExporter
from vexy_lines_cli.utils.system import speak

if TYPE_CHECKING:
    from vexy_lines_api import LayerNode


def _format_tree(node: LayerNode, indent: int = 0) -> str:
    """Recursively format a LayerNode tree with indentation.

    Each node is rendered as:
        {indent}{type}: {caption} (id={id})
    Fills append [{fill_type}].  Hidden nodes append [hidden].
    """
    prefix = "  " * indent
    line = f"{prefix}{node.type}: {node.caption} (id={node.id})"
    if node.fill_type:
        line += f" [{node.fill_type}]"
    if not node.visible:
        line += " [hidden]"
    lines = [line]
    for child in node.children:
        lines.append(_format_tree(child, indent + 1))
    return "\n".join(lines)


def _format_file_tree(nodes: list[GroupInfo | LayerInfo], indent: int = 0) -> str:
    """Recursively format a parsed layer tree (GroupInfo/LayerInfo) with indentation.

    Each node is rendered as:
        {indent}{type}: {caption}
    Fills append [{fill_type}].  Hidden layers append [hidden].
    """
    lines: list[str] = []
    prefix = "  " * indent
    for node in nodes:
        if isinstance(node, GroupInfo):
            lines.append(f"{prefix}group: {node.caption}")
            lines.append(_format_file_tree(node.children, indent + 1))
        elif isinstance(node, LayerInfo):
            vis = "" if node.visible else " [hidden]"
            lines.append(f"{prefix}layer: {node.caption}{vis}")
            for fill in node.fills:
                lines.append(f"{prefix}  fill: {fill.caption} [{fill.params.fill_type}]")
    return "\n".join(lines)


def _count_tree(nodes: list[GroupInfo | LayerInfo]) -> tuple[int, int, int]:
    """Count groups, layers, and fills in a parsed tree.

    Returns:
        Tuple of (groups, layers, fills).
    """
    n_groups = 0
    n_layers = 0
    n_fills = 0
    for node in nodes:
        if isinstance(node, GroupInfo):
            n_groups += 1
            sub_g, sub_l, sub_f = _count_tree(node.children)
            n_groups += sub_g
            n_layers += sub_l
            n_fills += sub_f
        elif isinstance(node, LayerInfo):
            n_layers += 1
            n_fills += len(node.fills)
    return n_groups, n_layers, n_fills


class VexyLinesCLI:
    """Command-line interface for Vexy Lines.

    Subcommands fall into three groups:

    **Parser** (no app needed): info, file-tree, extract-source, extract-preview, batch-convert
    **Style / MCP** (app must be running): style-transfer, style-video, tree, new-document,
        open, add-fill, render, mcp-status
    **Export** (app auto-launched): export
    **Bridge**: mcp-serve

    Run ``vexy-lines-cli <subcommand> --help`` for per-command options.
    """

    MIN_TIMEOUT_MULTIPLIER = 0.1
    MAX_TIMEOUT_MULTIPLIER = 10
    MAX_RETRY_LIMIT = 10

    # -- Parser subcommands (no app/MCP needed) ----------------------------

    def info(self, input: str, *, json_output: bool = False) -> dict[str, object]:  # noqa: A002
        """Show metadata for a .lines file without opening the app.

        Prints caption, version, DPI, dimensions, layer/fill counts, and
        whether source or preview images are embedded.

        Args:
            input: Path to the .lines file.
            json_output: Print result as JSON instead of the default repr.

        Returns:
            Dict with keys: caption, version, dpi, width_mm, height_mm,
            groups, layers, fills, has_source_image, has_preview_image.
            On parse failure, returns ``{"error": "<message>"}``.
        """
        try:
            doc = parse_lines(input)
        except (FileNotFoundError, Exception) as exc:
            return {"error": str(exc)}

        n_groups, n_layers, n_fills = _count_tree(doc.groups)
        result: dict[str, object] = {
            "caption": doc.caption,
            "version": doc.version,
            "dpi": doc.dpi,
            "width_mm": doc.props.width_mm,
            "height_mm": doc.props.height_mm,
            "groups": n_groups,
            "layers": n_layers,
            "fills": n_fills,
            "has_source_image": doc.source_image_data is not None,
            "has_preview_image": doc.preview_image_data is not None,
        }

        if json_output:
            print(_json.dumps(result, indent=2))  # noqa: T201

        return result

    def file_tree(self, input: str, *, json_output: bool = False) -> str:  # noqa: A002
        """Print the layer/group/fill tree from a .lines file without opening the app.

        Each node is indented to show nesting. Hidden layers are marked ``[hidden]``.

        Args:
            input: Path to the .lines file.
            json_output: Emit the tree as a JSON array of dataclass dicts.

        Returns:
            Indented text tree, or JSON string when ``--json-output`` is set.
            On parse failure, returns an error string (or JSON error object).
        """
        try:
            doc = parse_lines(input)
        except (FileNotFoundError, Exception) as exc:
            return _json.dumps({"error": str(exc)}) if json_output else str(exc)

        if json_output:
            from dataclasses import asdict as _asdict  # noqa: PLC0415

            tree_data = [_asdict(g) for g in doc.groups]
            return _json.dumps(tree_data, indent=2)

        return _format_file_tree(doc.groups)

    def extract_source(
        self,
        input: str,  # noqa: A002
        *,
        output: str | None = None,
        format: str = ".jpg",  # noqa: A002
    ) -> dict[str, object]:
        """Extract the embedded source image from a .lines file.

        The source image is the raster original that fills were applied to.
        Does not require the app to be running.

        Args:
            input: Path to the .lines file.
            output: Destination file path. Defaults to ``<stem>-src<format>``
                in the same directory as the input.
            format: Image format extension, e.g. ``.jpg`` or ``.png``.

        Returns:
            ``{"status": "ok", "output": "<path>"}`` on success,
            or ``{"error": "<message>"}`` on failure.
        """
        input_path = Path(input)
        output_path = input_path.with_name(f"{input_path.stem}-src{format}") if output is None else Path(output)

        try:
            result_path = extract_source_image(input_path, output_path)
            return {"status": "ok", "output": str(result_path)}
        except (FileNotFoundError, ValueError) as exc:
            return {"error": str(exc)}

    def extract_preview(
        self,
        input: str,  # noqa: A002
        *,
        output: str | None = None,
        format: str = ".png",  # noqa: A002
    ) -> dict[str, object]:
        """Extract the embedded preview image from a .lines file.

        The preview is the rendered thumbnail stored inside the document.
        Does not require the app to be running.

        Args:
            input: Path to the .lines file.
            output: Destination file path. Defaults to ``<stem>-preview<format>``
                in the same directory as the input.
            format: Image format extension, e.g. ``.jpg`` or ``.png``.

        Returns:
            ``{"status": "ok", "output": "<path>"}`` on success,
            or ``{"error": "<message>"}`` on failure.
        """
        input_path = Path(input)
        output_path = input_path.with_name(f"{input_path.stem}-preview{format}") if output is None else Path(output)

        try:
            result_path = extract_preview_image(input_path, output_path)
            return {"status": "ok", "output": str(result_path)}
        except (FileNotFoundError, ValueError) as exc:
            return {"error": str(exc)}

    # -- Style subcommands (require MCP for apply) -------------------------

    def style_transfer(
        self,
        *,
        style: str,
        end_style: str | None = None,
        images: list[str] | None = None,
        input_dir: str | None = None,
        output_dir: str = "./output",
        format: str = "svg",  # noqa: A002
        dpi: int = 72,
        host: str = "127.0.0.1",
        port: int = 47384,
        relative_style: bool = False,
        verbose: bool = False,
    ) -> dict[str, object]:
        """Apply a .lines style to one or more images via the MCP API.

        Reads fill parameters from ``--style``, opens each image in a new
        document via MCP, applies the style, then saves the rendered output.
        Requires the Vexy Lines app to be running.

        With ``--end-style``, linearly interpolates fill parameters between
        the two styles across the image sequence (useful for animations).

        Examples::

            vexy-lines style-transfer --style art.lines --input-dir ./photos/
            vexy-lines style-transfer --style a.lines --end-style b.lines --images 1.jpg 2.jpg
            vexy-lines style-transfer --style art.lines --relative-style --input-dir ./photos/

        Args:
            style: Path to the source style .lines file.
            end_style: Optional end style for interpolation across the sequence.
            images: Explicit list of image file paths to process.
            input_dir: Directory of images (``*.jpg``, ``*.jpeg``, ``*.png``).
                Use this or ``--images``, not both.
            output_dir: Where to write output files (created if absent).
            format: Output format: ``svg`` (default), ``png``, or ``jpg``.
                Raster formats require ``vexy-lines-run``.
            dpi: Document DPI passed to the MCP renderer (default 72).
            host: MCP server address (default 127.0.0.1).
            port: MCP server port (default 47384).
            relative_style: Scale spatial fill parameters to match the target
                image dimensions.  Default ``False`` (absolute mode).
            verbose: Enable debug logging.

        Returns:
            Dict with keys: total, successes, failures, output_dir.
            On connection failure, returns ``{"error": "<message>"}``.
        """
        if verbose:
            logger.enable("vexy_lines_cli")

        # Collect images
        image_paths: list[Path] = []
        if images:
            image_paths = [Path(p) for p in images]
        elif input_dir:
            src_dir = Path(input_dir)
            for ext in ("*.jpg", "*.jpeg", "*.png"):
                image_paths.extend(sorted(src_dir.glob(ext)))
        if not image_paths:
            return {"error": "no images found"}

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Extract style(s)
        try:
            start_style = extract_style(style)
            end_style_obj = extract_style(end_style) if end_style else None
        except (FileNotFoundError, Exception) as exc:
            return {"error": str(exc)}

        if end_style_obj and not styles_compatible(start_style, end_style_obj):
            logger.warning(
                "Start and end styles are incompatible (different fill structure). Interpolation may produce unexpected results."
            )

        n = len(image_paths)
        successes = 0
        failures = 0

        try:
            with MCPClient(host=host, port=port) as client:
                for i, img_path in enumerate(image_paths):
                    try:
                        # Determine style for this frame
                        if end_style_obj and n > 1:
                            t = i / (n - 1)
                            current_style = interpolate_style(start_style, end_style_obj, t)
                        else:
                            current_style = start_style

                        svg_string = apply_style(client, current_style, img_path, dpi=dpi, relative=relative_style)

                        # Save output
                        stem = img_path.stem
                        if format == "svg":
                            out_file = out / f"{stem}.svg"
                            out_file.write_text(svg_string, encoding="utf-8")
                        else:
                            try:
                                from vexy_lines_api.video import svg_to_pil  # noqa: PLC0415
                            except ImportError:
                                return {"error": "raster output requires: pip install av resvg-py Pillow"}
                            pil_img = svg_to_pil(svg_string, 1920, 1080)
                            out_file = out / f"{stem}.{format}"
                            pil_img.save(str(out_file))

                        successes += 1
                    except Exception:
                        failures += 1
                        logger.exception("Failed to process {}", img_path)
        except MCPError as exc:
            return {"error": str(exc)}

        result: dict[str, object] = {
            "total": n,
            "successes": successes,
            "failures": failures,
            "output_dir": str(out),
        }
        return result

    def style_video(
        self,
        *,
        style: str,
        input: str,  # noqa: A002
        output: str = "output.mp4",
        end_style: str | None = None,
        start_frame: int = 1,  # noqa: ARG002
        end_frame: int | None = None,
        dpi: int = 72,
        host: str = "127.0.0.1",
        port: int = 47384,
        relative_style: bool = False,
        verbose: bool = False,
    ) -> dict[str, object]:
        """Apply a .lines style to every frame of a video file.

        Decodes the video, renders each frame through the MCP API with the
        given style, then re-encodes to a new video. Requires the Vexy Lines
        app to be running and ``vexy-lines-run`` installed
        (``pip install vexy-lines-run``).

        With ``--end-style``, interpolates fill parameters between the two
        styles across frames — the first frame uses ``--style``, the last
        uses ``--end-style``.

        Args:
            style: Path to the source style .lines file.
            input: Path to the input video (MP4, MOV, etc.).
            output: Output video path (default ``output.mp4``).
            end_style: Optional end style for per-frame interpolation.
            start_frame: First frame to render (1-based, currently unused).
            end_frame: Last frame to render inclusive; ``None`` renders all.
            dpi: Document DPI passed to the MCP renderer (default 72).
            host: MCP server address (default 127.0.0.1).
            port: MCP server port (default 47384).
            relative_style: Scale spatial fill parameters to match the target
                video frame dimensions.  Default ``False`` (absolute mode).
            verbose: Enable debug logging.

        Returns:
            Dict with keys: status, input, output, width, height, fps,
            total_frames. On failure, returns ``{"error": "<message>"}``.
        """
        if verbose:
            logger.enable("vexy_lines_cli")

        try:
            from vexy_lines_api.video import process_video  # noqa: PLC0415
        except ImportError:
            return {"error": "video processing requires: pip install av resvg-py Pillow"}

        try:
            start_style_obj = extract_style(style)
            end_style_obj = extract_style(end_style) if end_style else None
        except (FileNotFoundError, Exception) as exc:
            return {"error": str(exc)}

        # Build frame_params callback using the style engine
        def _style_frame_params(frame_index: int, total_frames: int) -> dict:  # type: ignore[type-arg]
            """Per-frame callback that interpolates style and returns fill params."""
            if end_style_obj and total_frames > 1:
                t = frame_index / max(total_frames - 1, 1)
                current = interpolate_style(start_style_obj, end_style_obj, t)
            else:
                current = start_style_obj
            # Extract the first fill's numeric params as the frame override
            for node in current.groups:
                if isinstance(node, LayerInfo):
                    if node.fills:
                        p = node.fills[0].params
                        return {"angle": p.angle, "interval": p.interval}
                elif isinstance(node, GroupInfo):
                    for child in node.children:
                        if isinstance(child, LayerInfo) and child.fills:
                            p = child.fills[0].params
                            return {"angle": p.angle, "interval": p.interval}
            return {}

        max_frames = end_frame if end_frame else None

        def _on_progress(frame_idx: int, total: int) -> None:
            if verbose or frame_idx % 10 == 0 or frame_idx == total:
                pass

        try:
            info = process_video(
                input_path=input,
                output_path=output,
                frame_params=_style_frame_params,
                max_frames=max_frames,
                on_progress=_on_progress,
                host=host,
                port=port,
                dpi=dpi,
            )
            result: dict[str, object] = {
                "status": "ok",
                "input": input,
                "output": output,
                "width": info.width,
                "height": info.height,
                "fps": info.fps,
                "total_frames": info.total_frames,
            }
            return result
        except ImportError as exc:
            return {"error": str(exc)}
        except Exception as exc:
            return {"error": str(exc)}

    # -- Batch operations --------------------------------------------------

    def batch_convert(
        self,
        *,
        input_dir: str,
        output_dir: str = "./output",
        format: str = "png",  # noqa: A002
        what: str = "preview",
        verbose: bool = False,
    ) -> dict[str, object]:
        """Extract images from all .lines files in a directory.

        Pulls either the embedded preview or source image from each file.
        Does not require the app to be running.

        Args:
            input_dir: Directory containing ``.lines`` files.
            output_dir: Where to write extracted images (created if absent).
            format: Image format: ``png`` (default) or ``jpg``.
            what: Which image to extract: ``preview`` (rendered thumbnail)
                or ``source`` (original raster input).
            verbose: Enable debug logging.

        Returns:
            Dict with keys: total, successes, failures, output_dir.
            On invalid ``--what``, returns ``{"error": "invalid what: ..."}``.
        """
        if verbose:
            logger.enable("vexy_lines_cli")

        src = Path(input_dir)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        if what not in ("preview", "source"):
            return {"error": f"invalid what: {what}"}

        files = sorted(src.glob("*.lines"))
        if not files:
            return {"error": "no .lines files found"}

        ext = f".{format}" if not format.startswith(".") else format
        successes = 0
        failures = 0

        for _, lines_file in enumerate(files):
            out_file = out / f"{lines_file.stem}{ext}"
            try:
                if what == "source":
                    extract_source_image(lines_file, out_file)
                else:
                    extract_preview_image(lines_file, out_file)
                successes += 1
            except (FileNotFoundError, ValueError):
                failures += 1

        result: dict[str, object] = {
            "total": len(files),
            "successes": successes,
            "failures": failures,
            "output_dir": str(out),
        }
        return result

    # -- Export subcommand -------------------------------------------------

    def export(
        self,
        input: str,  # noqa: A002
        *,
        output: str | None = None,
        format: str = "pdf",  # noqa: A002
        verbose: bool = False,
        dry_run: bool = False,
        force: bool = False,
        say_summary: bool = False,
        timeout_multiplier: float = 1.0,
        max_retries: int = 3,
    ) -> dict[str, object]:
        """Export .lines documents to PDF or SVG without save dialogs.

        Quits the app, injects export preferences into macOS defaults, relaunches
        the app, opens each file, triggers File > Export, then restores the
        original preferences on exit — no save dialog interaction required.

        Examples::

            vexy-lines export artwork.lines
            vexy-lines export ./my-art/ --format svg --output ./exports/
            vexy-lines export artwork.lines --dry-run

        Args:
            input: A single ``.lines`` file or directory to search recursively.
            output: Destination file (single input) or directory (multiple
                inputs). Defaults to the same folder as each source file.
            format: Export format: ``pdf`` (default) or ``svg``.
            verbose: Enable debug logging.
            dry_run: List files that would be exported without exporting them.
            force: Re-export files even if the output already exists.
            say_summary: Announce the result via macOS text-to-speech.
            timeout_multiplier: Scale all internal timeouts (e.g. 2.0 = double).
                Range: 0.1–10.
            max_retries: Retry attempts per file on transient failures. Range: 0–10.

        Returns:
            Dict with keys: processed, success, skipped, failed, failures,
            validation_failed, validation_failures, dry_run, total_time,
            average_time.
        """
        if verbose:
            logger.enable("vexy_lines_cli")

        if timeout_multiplier < self.MIN_TIMEOUT_MULTIPLIER or timeout_multiplier > self.MAX_TIMEOUT_MULTIPLIER:
            msg = f"timeout_multiplier must be between {self.MIN_TIMEOUT_MULTIPLIER} and {self.MAX_TIMEOUT_MULTIPLIER}"
            raise ValueError(msg)
        if max_retries < 0 or max_retries > self.MAX_RETRY_LIMIT:
            msg = f"max_retries must be between 0 and {self.MAX_RETRY_LIMIT}"
            raise ValueError(msg)

        config = ExportConfig(
            format=format,
            timeout_multiplier=timeout_multiplier,
            max_retries=max_retries,
        )
        exporter = VexyLinesExporter(config, dry_run=dry_run, force=force)
        stats = exporter.export(
            Path(input),
            Path(output) if output else None,
        )

        if say_summary:
            speak(stats.human_summary())

        return stats.as_dict()

    # -- MCP subcommands --------------------------------------------------

    def mcp_status(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 47384,
    ) -> dict[str, object]:
        """Check whether the Vexy Lines MCP server is reachable.

        Connects to the TCP server and calls ``get_document_info``. Use this
        to confirm the app is running before issuing MCP commands.

        Args:
            host: TCP server address (default 127.0.0.1).
            port: TCP server port (default 47384).

        Returns:
            ``{"status": "ok", "server_info": {...}}`` on success,
            or ``{"error": "<message>"}`` if the server is unreachable.
        """
        try:
            with MCPClient(host=host, port=port) as client:
                info = client.get_document_info()
            return {"status": "ok", "server_info": asdict(info)}
        except MCPError as exc:
            return {"error": str(exc)}

    def tree(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 47384,
        json_output: bool = False,
    ) -> dict[str, object] | str:
        """Print the layer tree of the current document.

        Args:
            host: Server address.
            port: Server port.
            json_output: Output the tree as JSON instead of indented text.
        """
        try:
            with MCPClient(host=host, port=port) as client:
                root = client.get_layer_tree()
        except MCPError as exc:
            return {"error": str(exc)}

        if json_output:
            return _json.dumps(asdict(root), indent=2)

        return _format_tree(root)

    def new_document(
        self,
        *,
        width: float | None = None,
        height: float | None = None,
        dpi: float = 300,
        source_image: str | None = None,
        host: str = "127.0.0.1",
        port: int = 47384,
    ) -> dict[str, object]:
        """Create a new document via MCP.

        Args:
            width: Document width in mm.
            height: Document height in mm.
            dpi: Resolution (default 300).
            source_image: Optional path to a source image.
            host: Server address.
            port: Server port.
        """
        try:
            with MCPClient(host=host, port=port) as client:
                result = client.new_document(
                    width=width,
                    height=height,
                    dpi=dpi,
                    source_image=source_image,
                )
            return asdict(result)
        except MCPError as exc:
            return {"error": str(exc)}

    def open(
        self,
        input: str,  # noqa: A002
        *,
        host: str = "127.0.0.1",
        port: int = 47384,
    ) -> dict[str, object]:
        """Open a .lines file via MCP.

        Args:
            input: Path to the .lines file.
            host: Server address.
            port: Server port.
        """
        try:
            with MCPClient(host=host, port=port) as client:
                result = client.open_document(input)
            return {"status": "ok", "result": result}
        except MCPError as exc:
            return {"error": str(exc)}

    def add_fill(
        self,
        layer_id: int,
        fill_type: str,
        *,
        color: str | None = None,
        host: str = "127.0.0.1",
        port: int = 47384,
    ) -> dict[str, object]:
        """Add a fill to a layer.

        Args:
            layer_id: Target layer ID.
            fill_type: Fill type (e.g. 'solid', 'gradient').
            color: Optional colour value.
            host: Server address.
            port: Server port.
        """
        try:
            with MCPClient(host=host, port=port) as client:
                return client.add_fill(
                    layer_id=layer_id,
                    fill_type=fill_type,
                    color=color,
                )
        except MCPError as exc:
            return {"error": str(exc)}

    def render(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 47384,
    ) -> dict[str, object]:
        """Trigger a full render of the current document.

        Args:
            host: Server address.
            port: Server port.
        """
        try:
            with MCPClient(host=host, port=port) as client:
                result = client.render_all()
            return {"status": "ok", "result": result}
        except MCPError as exc:
            return {"error": str(exc)}

    # -- MCP bridge --------------------------------------------------------

    def mcp_serve(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 47384,
        no_launch: bool = False,
    ) -> None:
        """Start the MCP passthrough server (stdio <-> TCP bridge).

        Bridges Claude Desktop / Cursor to the Vexy Lines TCP MCP server.

        Args:
            host: TCP server address.
            port: TCP server port.
            no_launch: Don't auto-launch the app on connection failure.
        """
        from vexy_lines_cli.mcp_server import serve  # noqa: PLC0415

        serve(host=host, port=port, auto_launch=not no_launch)


def main() -> None:
    """Entry point: dispatch subcommands via Fire."""
    fire.Fire(VexyLinesCLI)


if __name__ == "__main__":
    main()

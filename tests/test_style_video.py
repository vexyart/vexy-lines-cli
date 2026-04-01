# this_file: vexy-lines-cli/tests/test_style_video.py

from __future__ import annotations

from unittest.mock import patch

from vexy_lines_cli.__main__ import VexyLinesCLI


class TestCliStyleVideo:
    def test_style_video_converts_user_frame_range_to_zero_based_export_request(self):
        cli = VexyLinesCLI()

        with patch("vexy_lines_cli.__main__.process_export") as mock_process_export:
            result = cli.style_video(
                style="style.lines",
                input="input.mp4",
                output="styled.mp4",
                start_frame=5,
                end_frame=12,
            )

        assert result["status"] == "ok"
        request = mock_process_export.call_args.kwargs["request"]
        assert request.mode == "video"
        assert request.format == "MP4"
        assert request.frame_range == (4, 11)

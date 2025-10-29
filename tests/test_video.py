"""Tests for video processing module."""

import os
import tempfile
import pytest
from pathlib import Path
from autothumb.core.video import VideoProcessor


class TestVideoProcessor:
    """Test VideoProcessor class."""

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            VideoProcessor("/path/to/nonexistent/video.mp4")

    def test_metadata_structure(self, sample_video):
        """Test that metadata has expected structure."""
        processor = VideoProcessor(sample_video)

        assert "duration" in processor.metadata
        assert "width" in processor.metadata
        assert "height" in processor.metadata
        assert "fps" in processor.metadata
        assert "codec" in processor.metadata
        assert "bitrate" in processor.metadata

        assert isinstance(processor.metadata["duration"], float)
        assert isinstance(processor.metadata["width"], int)
        assert isinstance(processor.metadata["height"], int)
        assert isinstance(processor.metadata["fps"], float)

    def test_context_manager(self, sample_video):
        """Test context manager properly cleans up."""
        with VideoProcessor(sample_video) as processor:
            frames = processor.extract_frames(num_frames=3)
            temp_dir = processor.temp_dir
            assert temp_dir is not None
            assert os.path.exists(temp_dir)

        # After context exit, temp dir should be cleaned up
        assert not os.path.exists(temp_dir)

    def test_extract_frames_count(self, sample_video):
        """Test that correct number of frames are extracted."""
        with VideoProcessor(sample_video) as processor:
            frames = processor.extract_frames(num_frames=5)
            assert len(frames) == 5

            # Check all frame files exist
            for frame_path in frames:
                assert os.path.exists(frame_path)
                assert frame_path.endswith(".jpg")

    def test_extract_frames_with_custom_output(self, sample_video):
        """Test frame extraction to custom output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            processor = VideoProcessor(sample_video)
            frames = processor.extract_frames(
                num_frames=3,
                output_dir=temp_dir
            )

            assert len(frames) == 3
            for frame_path in frames:
                assert temp_dir in frame_path
                assert os.path.exists(frame_path)

    def test_extract_frames_interval(self, sample_video):
        """Test interval-based frame extraction."""
        with VideoProcessor(sample_video) as processor:
            frames = processor.extract_frames_interval(
                interval_seconds=2.0,
                max_frames=5
            )

            assert len(frames) <= 5
            assert len(frames) > 0

    def test_get_thumbnail_at_time(self, sample_video):
        """Test extracting single frame at specific time."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            output_path = tmp.name

        try:
            processor = VideoProcessor(sample_video)
            result = processor.get_thumbnail_at_time(1.0, output_path)

            assert result == output_path
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0

        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_repr(self, sample_video):
        """Test string representation."""
        processor = VideoProcessor(sample_video)
        repr_str = repr(processor)

        assert "VideoProcessor" in repr_str
        assert "duration" in repr_str
        assert "resolution" in repr_str


# Fixtures
@pytest.fixture
def sample_video():
    """
    Fixture providing path to a sample video.

    Note: In real tests, you would need an actual video file.
    For CI/CD, you might generate a test video or download one.
    """
    # This is a placeholder - in real tests you'd need an actual video
    video_path = os.getenv("TEST_VIDEO_PATH")

    if video_path and os.path.exists(video_path):
        return video_path

    pytest.skip("No test video available. Set TEST_VIDEO_PATH environment variable.")

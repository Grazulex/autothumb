"""Module for video processing and frame extraction using FFmpeg."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
import json


class VideoProcessor:
    """Handle video processing and frame extraction."""

    def __init__(self, video_path: str):
        """
        Initialize the video processor.

        Args:
            video_path: Path to the video file

        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video file is invalid
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        self.metadata = self._get_metadata()
        self.temp_dir = None

    def _get_metadata(self) -> Dict:
        """
        Extract video metadata using FFprobe.

        Returns:
            Dictionary containing video metadata (duration, width, height, fps)

        Raises:
            RuntimeError: If FFprobe fails to extract metadata
        """
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(self.video_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)

            # Find video stream
            video_stream = next(
                (s for s in data["streams"] if s["codec_type"] == "video"),
                None
            )

            if not video_stream:
                raise ValueError("No video stream found in file")

            # Extract FPS
            fps_str = video_stream.get("r_frame_rate", "30/1")
            fps_parts = fps_str.split("/")
            fps = float(fps_parts[0]) / float(fps_parts[1])

            return {
                "duration": float(data["format"].get("duration", 0)),
                "width": int(video_stream.get("width", 0)),
                "height": int(video_stream.get("height", 0)),
                "fps": fps,
                "codec": video_stream.get("codec_name", "unknown"),
                "bitrate": int(data["format"].get("bit_rate", 0)),
            }

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFprobe failed: {e.stderr}")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise RuntimeError(f"Failed to parse video metadata: {e}")

    def extract_frames(
        self,
        num_frames: int = 10,
        output_dir: Optional[str] = None,
        skip_start_seconds: float = 2.0,
        skip_end_seconds: float = 2.0
    ) -> List[str]:
        """
        Extract evenly spaced frames from the video.

        Args:
            num_frames: Number of frames to extract
            output_dir: Directory to save frames (uses temp dir if None)
            skip_start_seconds: Skip this many seconds from the start
            skip_end_seconds: Skip this many seconds from the end

        Returns:
            List of paths to extracted frame images

        Raises:
            RuntimeError: If FFmpeg fails to extract frames
        """
        # Create output directory
        if output_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="autothumb_")
            output_dir = self.temp_dir
        else:
            os.makedirs(output_dir, exist_ok=True)

        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

        # Calculate timestamps for frame extraction
        duration = self.metadata["duration"]
        usable_duration = duration - skip_start_seconds - skip_end_seconds

        if usable_duration <= 0:
            raise ValueError("Video too short after skipping start/end")

        # Calculate timestamps for frame extraction
        timestamps = [
            skip_start_seconds + (i * usable_duration / (num_frames - 1))
            for i in range(num_frames)
        ]

        # Extract each frame individually using seek
        frame_files = []
        try:
            for idx, timestamp in enumerate(timestamps, start=1):
                frame_path = os.path.join(output_dir, f"frame_{idx:04d}.jpg")

                cmd = [
                    "ffmpeg",
                    "-ss", str(timestamp),
                    "-i", str(self.video_path),
                    "-vframes", "1",
                    "-vf", "scale=1280:-1",
                    "-q:v", "2",
                    "-y",
                    frame_path
                ]

                subprocess.run(
                    cmd,
                    capture_output=True,
                    check=True,
                    text=True
                )

                if os.path.exists(frame_path):
                    frame_files.append(frame_path)

            if not frame_files:
                raise RuntimeError("No frames were extracted")

            return sorted(frame_files)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed to extract frames: {e.stderr}")

    def extract_frames_interval(
        self,
        interval_seconds: float = 5.0,
        output_dir: Optional[str] = None,
        max_frames: int = 20
    ) -> List[str]:
        """
        Extract frames at regular intervals.

        Args:
            interval_seconds: Extract one frame every N seconds
            output_dir: Directory to save frames (uses temp dir if None)
            max_frames: Maximum number of frames to extract

        Returns:
            List of paths to extracted frame images
        """
        # Create output directory
        if output_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix="autothumb_")
            output_dir = self.temp_dir
        else:
            os.makedirs(output_dir, exist_ok=True)

        output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

        try:
            cmd = [
                "ffmpeg",
                "-i", str(self.video_path),
                "-vf", f"fps=1/{interval_seconds},scale=1280:-1",
                "-frames:v", str(max_frames),
                "-q:v", "2",
                output_pattern
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                text=True
            )

            # Get list of extracted frames
            frame_files = sorted([
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.startswith("frame_") and f.endswith(".jpg")
            ])

            return frame_files

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed to extract frames: {e.stderr}")

    def get_thumbnail_at_time(
        self,
        timestamp: float,
        output_path: str
    ) -> str:
        """
        Extract a single frame at a specific timestamp.

        Args:
            timestamp: Time in seconds
            output_path: Path to save the frame

        Returns:
            Path to the extracted frame

        Raises:
            RuntimeError: If FFmpeg fails
        """
        try:
            cmd = [
                "ffmpeg",
                "-ss", str(timestamp),
                "-i", str(self.video_path),
                "-vframes", "1",
                "-q:v", "2",
                "-y",  # Overwrite output file
                output_path
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                text=True
            )

            return output_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed to extract frame: {e.stderr}")

    def cleanup(self):
        """Clean up temporary files and directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"VideoProcessor("
            f"path={self.video_path}, "
            f"duration={self.metadata['duration']:.2f}s, "
            f"resolution={self.metadata['width']}x{self.metadata['height']}"
            f")"
        )

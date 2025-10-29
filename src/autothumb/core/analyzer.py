"""Module for analyzing video frames using Claude Vision API."""

import os
import base64
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import anthropic
from anthropic import Anthropic


class FrameAnalyzer:
    """Analyze video frames using Claude Vision to select the best thumbnail."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the frame analyzer.

        Args:
            api_key: Anthropic API key (reads from ANTHROPIC_API_KEY env var if None)

        Raises:
            ValueError: If no API key is provided or found in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. "
                "Provide via api_key parameter or ANTHROPIC_API_KEY environment variable."
            )

        self.client = Anthropic(api_key=self.api_key)

    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.standard_b64encode(image_file.read()).decode("utf-8")

    def _get_image_media_type(self, image_path: str) -> str:
        """
        Get media type from image file extension.

        Args:
            image_path: Path to image file

        Returns:
            Media type string (e.g., 'image/jpeg')
        """
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(ext, "image/jpeg")

    def analyze_frames(
        self,
        frame_paths: List[str],
        video_description: str,
        criteria: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Analyze multiple frames and select the best one for thumbnail.

        Args:
            frame_paths: List of paths to frame images
            video_description: Description/prompt about the video content
            criteria: Optional custom criteria for frame selection

        Returns:
            Dictionary containing:
                - best_frame_index: Index of the best frame
                - best_frame_path: Path to the best frame
                - reasoning: Claude's reasoning for selection
                - scores: Scores for each frame

        Raises:
            RuntimeError: If API call fails
        """
        if not frame_paths:
            raise ValueError("No frames provided for analysis")

        # Build prompt for frame analysis
        default_criteria = {
            "visual_appeal": "Clear, well-lit, and visually engaging",
            "composition": "Good framing and subject positioning",
            "text_overlay": "Space for text overlay without obscuring key elements",
            "engagement": "Likely to attract clicks and viewer interest",
            "clarity": "Sharp focus, not blurry or transitional",
        }

        criteria = criteria or default_criteria
        criteria_text = "\n".join([f"- {k}: {v}" for k, v in criteria.items()])

        prompt = f"""You are an expert at analyzing video frames to select the best thumbnail image for YouTube videos.

Video Description: {video_description}

I'm providing you with {len(frame_paths)} frames from a video. Please analyze each frame based on these criteria:
{criteria_text}

For each frame, provide:
1. A score from 1-10
2. Brief assessment of strengths and weaknesses
3. Suitability for thumbnail with text overlay

Finally, recommend which frame would make the best thumbnail and explain why.

Format your response as JSON with this structure:
{{
    "frames": [
        {{
            "index": 0,
            "score": 8,
            "strengths": ["clear subject", "good lighting"],
            "weaknesses": ["slightly off-center"],
            "thumbnail_suitability": "Good space for text overlay at top"
        }},
        ...
    ],
    "best_frame_index": 3,
    "reasoning": "Frame 3 is the best choice because..."
}}"""

        # Prepare content with all frames
        content = []

        # Add each frame as an image
        for i, frame_path in enumerate(frame_paths):
            if not os.path.exists(frame_path):
                raise FileNotFoundError(f"Frame not found: {frame_path}")

            image_data = self._encode_image(frame_path)
            media_type = self._get_image_media_type(frame_path)

            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_data,
                },
            })

        # Add the text prompt
        content.append({
            "type": "text",
            "text": prompt
        })

        try:
            # Call Claude Vision API
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            # Parse response
            response_text = response.content[0].text

            # Try to extract JSON from response
            import json
            import re

            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: parse the response manually
                analysis = {
                    "best_frame_index": 0,
                    "reasoning": response_text,
                    "frames": []
                }

            best_index = analysis.get("best_frame_index", 0)

            return {
                "best_frame_index": best_index,
                "best_frame_path": frame_paths[best_index],
                "reasoning": analysis.get("reasoning", ""),
                "scores": analysis.get("frames", []),
                "raw_response": response_text
            }

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to analyze frames: {e}")

    def generate_thumbnail_text(
        self,
        video_description: str,
        style: str = "youtube",
        max_words: int = 6
    ) -> Dict[str, str]:
        """
        Generate catchy text for thumbnail overlay.

        Args:
            video_description: Description of the video content
            style: Style of text (youtube, minimalist, bold, tech, clickbait)
            max_words: Maximum number of words in the text

        Returns:
            Dictionary containing:
                - main_text: Primary text for thumbnail
                - subtext: Optional secondary text
                - reasoning: Why this text was chosen

        Raises:
            RuntimeError: If API call fails
        """
        style_guidelines = {
            "youtube": "Engaging, attention-grabbing, uses power words, creates curiosity",
            "minimalist": "Clean, simple, direct, 2-3 words max",
            "bold": "Strong, impactful, uses action verbs and emotion",
            "tech": "Professional, technical, clear value proposition",
            "clickbait": "Extremely attention-grabbing, uses numbers, urgency, curiosity gaps"
        }

        style_guide = style_guidelines.get(style, style_guidelines["youtube"])

        prompt = f"""You are an expert at creating catchy, effective thumbnail text for YouTube videos.

Video Description: {video_description}

Style: {style}
Style Guidelines: {style_guide}
Maximum Words: {max_words}

Create compelling thumbnail text that will:
1. Grab attention immediately
2. Clearly communicate the video's value
3. Encourage clicks without being misleading
4. Work well visually when overlaid on an image

Provide:
- Main text (large, primary text - max {max_words} words)
- Optional subtext (smaller supporting text - 1-3 words)
- Brief reasoning for your choices

Format as JSON:
{{
    "main_text": "YOUR MAIN TEXT HERE",
    "subtext": "optional subtext",
    "reasoning": "why this text is effective..."
}}"""

        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            # Parse JSON response
            import json
            import re

            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback
                result = {
                    "main_text": video_description[:max_words * 7],  # Rough estimate
                    "subtext": "",
                    "reasoning": "Fallback text generation"
                }

            return result

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate text: {e}")

    def analyze_and_generate(
        self,
        frame_paths: List[str],
        video_description: str,
        style: str = "youtube",
        max_words: int = 6
    ) -> Tuple[Dict, Dict]:
        """
        Combined analysis: select best frame and generate text.

        Args:
            frame_paths: List of frame image paths
            video_description: Video description/prompt
            style: Text style
            max_words: Max words for text

        Returns:
            Tuple of (frame_analysis, text_generation) dictionaries
        """
        frame_analysis = self.analyze_frames(frame_paths, video_description)
        text_result = self.generate_thumbnail_text(video_description, style, max_words)

        return frame_analysis, text_result

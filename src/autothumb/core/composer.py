"""Module for composing thumbnail images with text overlays."""

import os
from typing import Tuple, Optional, Dict, List
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance


class ThumbnailComposer:
    """Compose thumbnails by adding text overlays to images."""

    # Style presets
    STYLES = {
        "youtube": {
            "font_size_main": 72,
            "font_size_sub": 36,
            "text_color": (255, 255, 255),
            "outline_color": (0, 0, 0),
            "outline_width": 4,
            "position": "center",
            "background_opacity": 0.3,
            "shadow": True,
            "bold": True,
        },
        "minimalist": {
            "font_size_main": 60,
            "font_size_sub": 30,
            "text_color": (255, 255, 255),
            "outline_color": None,
            "outline_width": 0,
            "position": "bottom",
            "background_opacity": 0.5,
            "shadow": False,
            "bold": False,
        },
        "bold": {
            "font_size_main": 120,
            "font_size_sub": 50,
            "text_color": (255, 215, 0),  # Gold
            "outline_color": (0, 0, 0),
            "outline_width": 6,
            "position": "center",
            "background_opacity": 0.4,
            "shadow": True,
            "bold": True,
        },
        "tech": {
            "font_size_main": 64,
            "font_size_sub": 32,
            "text_color": (0, 255, 255),  # Cyan
            "outline_color": (0, 0, 0),
            "outline_width": 3,
            "position": "top",
            "background_opacity": 0.6,
            "shadow": True,
            "bold": False,
        },
    }

    def __init__(self, style: str = "youtube"):
        """
        Initialize the thumbnail composer.

        Args:
            style: Style preset name (youtube, minimalist, bold, tech)
        """
        self.style_name = style
        self.style = self.STYLES.get(style, self.STYLES["youtube"])

    def _get_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """
        Get a font object.

        Args:
            size: Font size
            bold: Use bold font if available

        Returns:
            Font object
        """
        font_paths = [
            # Try common font locations
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "arial.ttf",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue

        # Fallback to default font
        return ImageFont.load_default()

    def _add_shadow(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        offset: int = 4
    ):
        """
        Add shadow to text.

        Args:
            draw: ImageDraw object
            text: Text to draw
            position: Text position (x, y)
            font: Font object
            offset: Shadow offset in pixels
        """
        shadow_pos = (position[0] + offset, position[1] + offset)
        draw.text(shadow_pos, text, font=font, fill=(0, 0, 0, 180))

    def _draw_text_with_outline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        text_color: Tuple[int, int, int],
        outline_color: Optional[Tuple[int, int, int]],
        outline_width: int
    ):
        """
        Draw text with outline.

        Args:
            draw: ImageDraw object
            text: Text to draw
            position: Text position (x, y)
            font: Font object
            text_color: RGB color for text
            outline_color: RGB color for outline (None for no outline)
            outline_width: Width of outline
        """
        x, y = position

        # Draw outline if specified
        if outline_color and outline_width > 0:
            for adj_x in range(-outline_width, outline_width + 1):
                for adj_y in range(-outline_width, outline_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text(
                            (x + adj_x, y + adj_y),
                            text,
                            font=font,
                            fill=outline_color
                        )

        # Draw main text
        draw.text(position, text, font=font, fill=text_color)

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int
    ) -> List[str]:
        """
        Wrap text to fit within max width.

        Args:
            text: Text to wrap
            font: Font object
            max_width: Maximum width in pixels

        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _add_background_overlay(
        self,
        image: Image.Image,
        position: str,
        opacity: float,
        height_ratio: float = 0.4
    ) -> Image.Image:
        """
        Add semi-transparent background overlay for text.

        Args:
            image: Base image
            position: Position of overlay (top, center, bottom)
            opacity: Opacity of overlay (0-1)
            height_ratio: Height of overlay as ratio of image height

        Returns:
            Image with overlay
        """
        width, height = image.size
        overlay_height = int(height * height_ratio)

        # Create overlay
        overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Calculate position
        if position == "top":
            y_start = 0
            y_end = overlay_height
        elif position == "bottom":
            y_start = height - overlay_height
            y_end = height
        else:  # center
            y_start = (height - overlay_height) // 2
            y_end = y_start + overlay_height

        # Draw gradient overlay
        alpha = int(255 * opacity)
        overlay_draw.rectangle(
            [(0, y_start), (width, y_end)],
            fill=(0, 0, 0, alpha)
        )

        # Apply Gaussian blur for smoother edges
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=10))

        # Composite overlay with image
        return Image.alpha_composite(image.convert("RGBA"), overlay)

    def compose(
        self,
        image_path: str,
        main_text: str,
        output_path: str,
        subtext: Optional[str] = None,
        resolution: Tuple[int, int] = (1280, 720),
        custom_style: Optional[Dict] = None
    ) -> str:
        """
        Compose thumbnail with text overlay.

        Args:
            image_path: Path to base image
            main_text: Main text to overlay
            output_path: Path to save final thumbnail
            subtext: Optional secondary text
            resolution: Target resolution (width, height)
            custom_style: Optional custom style overrides

        Returns:
            Path to generated thumbnail

        Raises:
            FileNotFoundError: If image file doesn't exist
            RuntimeError: If composition fails
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            # Load and resize image
            image = Image.open(image_path)
            image = image.convert("RGB")
            image = image.resize(resolution, Image.Resampling.LANCZOS)

            # Apply style overrides
            style = self.style.copy()
            if custom_style:
                style.update(custom_style)

            # Convert to RGBA for compositing
            image = image.convert("RGBA")

            # Add background overlay if specified
            if style.get("background_opacity", 0) > 0:
                image = self._add_background_overlay(
                    image,
                    style["position"],
                    style["background_opacity"]
                )

            # Create drawing context
            draw = ImageDraw.Draw(image)

            # Get fonts
            main_font = self._get_font(
                style["font_size_main"],
                style.get("bold", False)
            )
            sub_font = self._get_font(
                style["font_size_sub"],
                False
            )

            # Wrap text
            max_width = int(resolution[0] * 0.9)  # 90% of image width
            main_lines = self._wrap_text(main_text, main_font, max_width)

            # Calculate text dimensions
            line_height = style["font_size_main"] + 10
            total_text_height = len(main_lines) * line_height

            if subtext:
                sub_lines = self._wrap_text(subtext, sub_font, max_width)
                total_text_height += len(sub_lines) * (style["font_size_sub"] + 10) + 20

            # Calculate starting Y position based on style
            if style["position"] == "top":
                y = 50
            elif style["position"] == "bottom":
                y = resolution[1] - total_text_height - 50
            else:  # center
                y = (resolution[1] - total_text_height) // 2

            # Draw main text
            for line in main_lines:
                bbox = main_font.getbbox(line)
                text_width = bbox[2] - bbox[0]
                x = (resolution[0] - text_width) // 2

                # Add shadow if enabled
                if style.get("shadow", False):
                    self._add_shadow(draw, line, (x, y), main_font, offset=5)

                # Draw text with outline
                self._draw_text_with_outline(
                    draw,
                    line,
                    (x, y),
                    main_font,
                    style["text_color"],
                    style["outline_color"],
                    style["outline_width"]
                )

                y += line_height

            # Draw subtext if provided
            if subtext:
                y += 20  # Add spacing
                for line in self._wrap_text(subtext, sub_font, max_width):
                    bbox = sub_font.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    x = (resolution[0] - text_width) // 2

                    if style.get("shadow", False):
                        self._add_shadow(draw, line, (x, y), sub_font, offset=3)

                    self._draw_text_with_outline(
                        draw,
                        line,
                        (x, y),
                        sub_font,
                        style["text_color"],
                        style["outline_color"],
                        max(style["outline_width"] - 1, 1)
                    )

                    y += style["font_size_sub"] + 10

            # Convert back to RGB for saving
            image = image.convert("RGB")

            # Enhance image slightly
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.2)

            # Save with high quality
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            image.save(output_path, "JPEG", quality=95, optimize=True)

            return output_path

        except Exception as e:
            raise RuntimeError(f"Failed to compose thumbnail: {e}")

    def create_thumbnail_from_analysis(
        self,
        frame_path: str,
        text_data: Dict,
        output_path: str,
        resolution: Tuple[int, int] = (1280, 720)
    ) -> str:
        """
        Create thumbnail from Claude Vision analysis results.

        Args:
            frame_path: Path to selected frame
            text_data: Dictionary with 'main_text' and optional 'subtext'
            output_path: Output path for thumbnail
            resolution: Target resolution

        Returns:
            Path to generated thumbnail
        """
        return self.compose(
            image_path=frame_path,
            main_text=text_data["main_text"],
            output_path=output_path,
            subtext=text_data.get("subtext"),
            resolution=resolution
        )

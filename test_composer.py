#!/usr/bin/env python3
"""Script de test pour la composition de thumbnails."""

import sys
from pathlib import Path
import glob

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autothumb.core.composer import ThumbnailComposer


def test_composer():
    """Test la composition de thumbnails avec différents styles."""

    # Find test frames
    frame_dir = "./output/test_frames"
    frames = glob.glob(f"{frame_dir}/frame_*.jpg")

    if not frames:
        print("✗ Aucune frame trouvée. Exécutez d'abord test_video_extraction.py")
        return False

    test_frame = frames[0]
    print("=" * 60)
    print("TEST: Composition de thumbnails")
    print("=" * 60)
    print(f"Frame de test: {test_frame}\n")

    styles = ["youtube", "minimalist", "bold", "tech"]
    success_count = 0

    for style in styles:
        print(f"📐 Test du style '{style}'...")

        try:
            composer = ThumbnailComposer(style=style)

            output_path = f"./output/thumbnail_{style}.jpg"

            # Test with main text only
            result = composer.compose(
                image_path=test_frame,
                main_text="Tutoriel Python Avancé",
                output_path=output_path,
                resolution=(1280, 720)
            )

            print(f"  ✓ Thumbnail créé: {result}")
            success_count += 1

            # Test with subtext
            output_path_sub = f"./output/thumbnail_{style}_subtext.jpg"
            result_sub = composer.compose(
                image_path=test_frame,
                main_text="Maîtrisez Python",
                subtext="En 30 minutes",
                output_path=output_path_sub,
                resolution=(1920, 1080)
            )

            print(f"  ✓ Thumbnail avec sous-titre: {result_sub}")
            success_count += 1

        except Exception as e:
            print(f"  ✗ Erreur: {e}")
            import traceback
            traceback.print_exc()

        print()

    print("=" * 60)
    if success_count == len(styles) * 2:
        print("✓ TOUS LES TESTS PASSÉS")
        print("=" * 60)
        print("\n📂 Thumbnails générés dans ./output/:")
        for style in styles:
            print(f"  - thumbnail_{style}.jpg (1280x720)")
            print(f"  - thumbnail_{style}_subtext.jpg (1920x1080)")
        return True
    else:
        print(f"⚠ {success_count}/{len(styles) * 2} tests réussis")
        print("=" * 60)
        return False


def test_custom_style():
    """Test avec un style personnalisé."""

    frame_dir = "./output/test_frames"
    frames = glob.glob(f"{frame_dir}/frame_*.jpg")

    if not frames:
        return True  # Skip if no frames

    print("\n" + "=" * 60)
    print("TEST BONUS: Style personnalisé")
    print("=" * 60)

    try:
        composer = ThumbnailComposer(style="youtube")

        custom_style = {
            "font_size_main": 96,
            "text_color": (255, 0, 255),  # Magenta
            "outline_color": (255, 255, 0),  # Yellow
            "outline_width": 5,
            "position": "center",
        }

        result = composer.compose(
            image_path=frames[0],
            main_text="Style Custom",
            subtext="Couleurs folles !",
            output_path="./output/thumbnail_custom.jpg",
            resolution=(1280, 720),
            custom_style=custom_style
        )

        print(f"✓ Thumbnail personnalisé créé: {result}")
        return True

    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False


if __name__ == "__main__":
    success1 = test_composer()
    success2 = test_custom_style()

    sys.exit(0 if (success1 and success2) else 1)

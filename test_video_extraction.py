#!/usr/bin/env python3
"""Script de test pour l'extraction de frames vidéo."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autothumb.core.video import VideoProcessor


def test_video_extraction(video_path: str):
    """Test l'extraction de frames d'une vidéo."""

    print("=" * 60)
    print("TEST 1: Chargement de la vidéo et métadonnées")
    print("=" * 60)

    try:
        processor = VideoProcessor(video_path)
        print(f"✓ Vidéo chargée: {video_path}")
        print(f"\nMétadonnées:")
        print(f"  - Durée: {processor.metadata['duration']:.2f} secondes")
        print(f"  - Résolution: {processor.metadata['width']}x{processor.metadata['height']}")
        print(f"  - FPS: {processor.metadata['fps']:.2f}")
        print(f"  - Codec: {processor.metadata['codec']}")
        print(f"  - Bitrate: {processor.metadata['bitrate']} bits/s")

    except Exception as e:
        print(f"✗ Erreur lors du chargement: {e}")
        return False

    print("\n" + "=" * 60)
    print("TEST 2: Extraction de 5 frames")
    print("=" * 60)

    try:
        frames = processor.extract_frames(num_frames=5, output_dir="./output/test_frames")
        print(f"✓ {len(frames)} frames extraites")

        for i, frame_path in enumerate(frames, 1):
            print(f"  Frame {i}: {frame_path}")

    except Exception as e:
        print(f"✗ Erreur lors de l'extraction: {e}")
        return False
    finally:
        processor.cleanup()

    print("\n" + "=" * 60)
    print("TEST 3: Extraction à intervalle régulier (1 frame/2s)")
    print("=" * 60)

    try:
        processor2 = VideoProcessor(video_path)
        frames = processor2.extract_frames_interval(
            interval_seconds=2.0,
            max_frames=10,
            output_dir="./output/test_frames_interval"
        )
        print(f"✓ {len(frames)} frames extraites")

        for i, frame_path in enumerate(frames, 1):
            print(f"  Frame {i}: {frame_path}")

        processor2.cleanup()

    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ TOUS LES TESTS PASSÉS")
    print("=" * 60)
    print(f"\nVous pouvez maintenant vérifier les images dans:")
    print(f"  - ./output/test_frames/")
    print(f"  - ./output/test_frames_interval/")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_video_extraction.py <chemin_video>")
        print("\nExemple:")
        print("  python test_video_extraction.py ./videos/ma_video.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    if not Path(video_path).exists():
        print(f"✗ Erreur: Le fichier '{video_path}' n'existe pas")
        sys.exit(1)

    success = test_video_extraction(video_path)
    sys.exit(0 if success else 1)

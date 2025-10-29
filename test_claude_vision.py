#!/usr/bin/env python3
"""Script de test pour l'analyse Claude Vision."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from autothumb.core.video import VideoProcessor
from autothumb.core.analyzer import FrameAnalyzer


def test_claude_vision(video_path: str, video_description: str):
    """Test l'analyse Claude Vision sur une vidéo."""

    print("=" * 60)
    print("TEST 1: Extraction de frames")
    print("=" * 60)

    try:
        processor = VideoProcessor(video_path)
        print(f"✓ Vidéo chargée: {video_path}")
        print(f"  Durée: {processor.metadata['duration']:.2f}s")

        # Extract 5 frames for analysis
        frames = processor.extract_frames(
            num_frames=5,
            output_dir="./output/claude_test_frames"
        )
        print(f"✓ {len(frames)} frames extraites pour l'analyse")

    except Exception as e:
        print(f"✗ Erreur lors de l'extraction: {e}")
        return False
    finally:
        processor.cleanup()

    print("\n" + "=" * 60)
    print("TEST 2: Analyse Claude Vision - Sélection de frame")
    print("=" * 60)

    try:
        analyzer = FrameAnalyzer()
        print(f"✓ Analyseur Claude initialisé")
        print(f"  Prompt: {video_description}")
        print(f"\n⏳ Analyse en cours (cela peut prendre 10-30 secondes)...\n")

        analysis = analyzer.analyze_frames(frames, video_description)

        print(f"✓ Analyse terminée !")
        print(f"\n📊 Résultats:")
        print(f"  Meilleure frame: #{analysis['best_frame_index'] + 1}")
        print(f"  Fichier: {os.path.basename(analysis['best_frame_path'])}")
        print(f"\n💡 Raisonnement de Claude:")
        print(f"  {analysis['reasoning'][:300]}...")

        if analysis['scores']:
            print(f"\n📈 Scores des frames:")
            for i, score_info in enumerate(analysis['scores'][:5], 1):
                score = score_info.get('score', 'N/A')
                print(f"  Frame {i}: {score}/10")

    except Exception as e:
        print(f"✗ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("TEST 3: Génération de texte pour thumbnail")
    print("=" * 60)

    try:
        print(f"⏳ Génération du texte...\n")

        text_result = analyzer.generate_thumbnail_text(
            video_description,
            style="youtube",
            max_words=6
        )

        print(f"✓ Texte généré !")
        print(f"\n📝 Texte principal: \"{text_result['main_text']}\"")
        if text_result.get('subtext'):
            print(f"   Sous-texte: \"{text_result['subtext']}\"")
        print(f"\n💡 Justification:")
        print(f"  {text_result.get('reasoning', 'N/A')[:300]}...")

    except Exception as e:
        print(f"✗ Erreur lors de la génération: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("TEST 4: Analyse complète (frame + texte)")
    print("=" * 60)

    try:
        print(f"⏳ Analyse complète en cours...\n")

        frame_analysis, text_gen = analyzer.analyze_and_generate(
            frames,
            video_description,
            style="bold",
            max_words=5
        )

        print(f"✓ Analyse complète terminée !")
        print(f"\n🎯 Résumé final:")
        print(f"  Meilleure frame: {os.path.basename(frame_analysis['best_frame_path'])}")
        print(f"  Texte suggéré: \"{text_gen['main_text']}\"")

    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("✓ TOUS LES TESTS PASSÉS")
    print("=" * 60)

    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_claude_vision.py <chemin_video> <description>")
        print("\nExemple:")
        print('  python test_claude_vision.py ./videos/test_video.mp4 "Tutoriel Python pour débutants"')
        sys.exit(1)

    video_path = sys.argv[1]
    video_description = " ".join(sys.argv[2:])

    if not Path(video_path).exists():
        print(f"✗ Erreur: Le fichier '{video_path}' n'existe pas")
        sys.exit(1)

    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("✗ Erreur: ANTHROPIC_API_KEY non défini")
        print("  Assurez-vous que le fichier .env contient votre clé API")
        sys.exit(1)

    success = test_claude_vision(video_path, video_description)
    sys.exit(0 if success else 1)

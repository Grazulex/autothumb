"""Main CLI application for AutoThumb."""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from autothumb.core.video import VideoProcessor
from autothumb.core.analyzer import FrameAnalyzer
from autothumb.core.composer import ThumbnailComposer


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    AutoThumb - Générateur automatique de thumbnails YouTube avec IA

    Utilisez Claude Vision pour analyser vos vidéos et créer des thumbnails optimisées.
    """
    pass


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--prompt", "-p",
    required=True,
    help="Description du contenu de la vidéo"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Chemin de sortie du thumbnail (défaut: ./output/thumbnail.jpg)"
)
@click.option(
    "--style", "-s",
    type=click.Choice(["youtube", "minimalist", "bold", "tech"]),
    default="youtube",
    help="Style du thumbnail"
)
@click.option(
    "--resolution", "-r",
    type=click.Choice(["720p", "1080p"]),
    default="720p",
    help="Résolution du thumbnail"
)
@click.option(
    "--frames", "-f",
    type=int,
    default=10,
    help="Nombre de frames à analyser"
)
def generate(
    video_path: str,
    prompt: str,
    output: Optional[str],
    style: str,
    resolution: str,
    frames: int
):
    """
    Génère un thumbnail complet : extraction, analyse IA, composition.

    Cette commande exécute le pipeline complet automatiquement.

    Example:
        autothumb generate video.mp4 -p "Tutoriel Python" -s youtube
    """
    # Set default output
    if not output:
        output = "./output/thumbnail.jpg"

    # Parse resolution - will be adjusted based on video format
    res_map = {"720p": (1280, 720), "1080p": (1920, 1080)}
    base_resolution = res_map[resolution]

    console.print(Panel.fit(
        f"[bold cyan]AutoThumb - Génération de Thumbnail[/bold cyan]\n\n"
        f"[yellow]Vidéo:[/yellow] {video_path}\n"
        f"[yellow]Prompt:[/yellow] {prompt}\n"
        f"[yellow]Style:[/yellow] {style}\n"
        f"[yellow]Résolution:[/yellow] {resolution}\n"
        f"[yellow]Frames à analyser:[/yellow] {frames}",
        border_style="cyan"
    ))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:

            # Step 1: Extract frames
            task1 = progress.add_task("[cyan]Extraction des frames...", total=1)

            processor = VideoProcessor(video_path)
            video_width = processor.metadata['width']
            video_height = processor.metadata['height']

            console.print(f"\n[green]✓[/green] Vidéo chargée: {processor.metadata['duration']:.1f}s, "
                         f"{video_width}x{video_height}")

            # Detect video format and adjust thumbnail resolution
            is_vertical = video_height > video_width
            if is_vertical:
                # For vertical videos (shorts), swap width and height
                target_resolution = (base_resolution[1], base_resolution[0])
                console.print(f"[cyan]ℹ[/cyan] Format vertical détecté, thumbnail: {target_resolution[0]}x{target_resolution[1]}")
            else:
                # For horizontal videos, use base resolution
                target_resolution = base_resolution
                console.print(f"[cyan]ℹ[/cyan] Format horizontal détecté, thumbnail: {target_resolution[0]}x{target_resolution[1]}")

            # Extract to a persistent directory, not temp
            frame_output_dir = os.path.join(os.path.dirname(output), "frames_temp")
            frame_paths = processor.extract_frames(num_frames=frames, output_dir=frame_output_dir)
            console.print(f"[green]✓[/green] {len(frame_paths)} frames extraites")

            progress.update(task1, completed=1)

            # Step 2: Analyze with Claude Vision
            task2 = progress.add_task("[cyan]Analyse IA avec Claude Vision...", total=1)

            analyzer = FrameAnalyzer()
            frame_analysis, text_result = analyzer.analyze_and_generate(
                frame_paths,
                prompt,
                style=style,
                max_words=6
            )

            console.print(f"\n[green]✓[/green] Meilleure frame sélectionnée: "
                         f"#{frame_analysis['best_frame_index'] + 1}")
            console.print(f"[green]✓[/green] Texte généré: \"{text_result['main_text']}\"")

            progress.update(task2, completed=1)

            # Step 3: Compose final thumbnail
            task3 = progress.add_task("[cyan]Composition du thumbnail...", total=1)

            composer = ThumbnailComposer(style=style)
            final_path = composer.create_thumbnail_from_analysis(
                frame_analysis['best_frame_path'],
                text_result,
                output,
                resolution=target_resolution
            )

            progress.update(task3, completed=1)

        # Cleanup temporary frames
        import shutil
        if os.path.exists(frame_output_dir):
            shutil.rmtree(frame_output_dir)

        console.print(f"\n[bold green]✓ Thumbnail généré avec succès![/bold green]")
        console.print(f"[yellow]→[/yellow] Fichier: [bold]{final_path}[/bold]")

        # Show reasoning
        if frame_analysis.get('reasoning'):
            console.print(f"\n[dim]💡 Raison du choix: {frame_analysis['reasoning'][:200]}...[/dim]")

    except FileNotFoundError as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}", style="red")
        sys.exit(1)
    except RuntimeError as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Erreur inattendue:[/bold red] {e}", style="red")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--prompt", "-p",
    required=True,
    help="Description du contenu"
)
@click.option(
    "--frames", "-f",
    type=int,
    default=10,
    help="Nombre de frames à analyser"
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(),
    default="./output/frames",
    help="Dossier pour sauvegarder les frames"
)
def analyze(video_path: str, prompt: str, frames: int, output_dir: str):
    """
    Analyse une vidéo et recommande la meilleure frame + texte.

    N'effectue pas la composition finale, seulement l'analyse.

    Example:
        autothumb analyze video.mp4 -p "DevOps Tutorial" -f 15
    """
    console.print(Panel.fit(
        f"[bold cyan]AutoThumb - Analyse de Vidéo[/bold cyan]\n\n"
        f"[yellow]Vidéo:[/yellow] {video_path}\n"
        f"[yellow]Prompt:[/yellow] {prompt}\n"
        f"[yellow]Frames:[/yellow] {frames}",
        border_style="cyan"
    ))

    try:
        # Extract frames
        console.print("\n[cyan]→[/cyan] Extraction des frames...")

        with VideoProcessor(video_path) as processor:
            console.print(f"  Durée: {processor.metadata['duration']:.1f}s")
            frame_paths = processor.extract_frames(num_frames=frames, output_dir=output_dir)
            console.print(f"  [green]✓[/green] {len(frame_paths)} frames extraites")

        # Analyze with Claude
        console.print("\n[cyan]→[/cyan] Analyse avec Claude Vision...")

        analyzer = FrameAnalyzer()
        frame_analysis, text_result = analyzer.analyze_and_generate(
            frame_paths,
            prompt,
            style="youtube",
            max_words=6
        )

        # Display results
        console.print("\n[bold green]✓ Analyse terminée![/bold green]\n")

        # Create results table
        table = Table(title="Résultats de l'Analyse", show_header=True, header_style="bold magenta")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="yellow")

        table.add_row("Meilleure Frame", f"#{frame_analysis['best_frame_index'] + 1}")
        table.add_row("Fichier", Path(frame_analysis['best_frame_path']).name)
        table.add_row("Texte Principal", text_result['main_text'])
        if text_result.get('subtext'):
            table.add_row("Sous-texte", text_result['subtext'])

        console.print(table)

        # Show reasoning
        console.print(f"\n[bold]💡 Raisonnement:[/bold]")
        console.print(Panel(frame_analysis.get('reasoning', 'N/A'), border_style="dim"))

        console.print(f"\n[dim]Frames sauvegardées dans: {output_dir}[/dim]")

    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
@click.option(
    "--text", "-t",
    required=True,
    help="Texte principal"
)
@click.option(
    "--subtext",
    help="Texte secondaire (optionnel)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./output/thumbnail.jpg",
    help="Chemin de sortie"
)
@click.option(
    "--style", "-s",
    type=click.Choice(["youtube", "minimalist", "bold", "tech"]),
    default="youtube",
    help="Style du thumbnail"
)
@click.option(
    "--resolution", "-r",
    type=click.Choice(["720p", "1080p"]),
    default="720p",
    help="Résolution"
)
def compose(
    image_path: str,
    text: str,
    subtext: Optional[str],
    output: str,
    style: str,
    resolution: str
):
    """
    Compose un thumbnail à partir d'une image existante.

    Ajoute du texte stylisé sur une image sans analyse IA.

    Example:
        autothumb compose frame.jpg -t "Python Tips" --subtext "2024" -s bold
    """
    res_map = {"720p": (1280, 720), "1080p": (1920, 1080)}
    target_resolution = res_map[resolution]

    console.print(Panel.fit(
        f"[bold cyan]AutoThumb - Composition de Thumbnail[/bold cyan]\n\n"
        f"[yellow]Image:[/yellow] {image_path}\n"
        f"[yellow]Texte:[/yellow] {text}\n"
        f"[yellow]Style:[/yellow] {style}\n"
        f"[yellow]Résolution:[/yellow] {resolution}",
        border_style="cyan"
    ))

    try:
        console.print("\n[cyan]→[/cyan] Composition en cours...")

        composer = ThumbnailComposer(style=style)
        result = composer.compose(
            image_path=image_path,
            main_text=text,
            subtext=subtext,
            output_path=output,
            resolution=target_resolution
        )

        console.print(f"\n[bold green]✓ Thumbnail créé![/bold green]")
        console.print(f"[yellow]→[/yellow] Fichier: [bold]{result}[/bold]")

    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}", style="red")
        sys.exit(1)


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
def info(video_path: str):
    """
    Affiche les informations sur une vidéo.

    Example:
        autothumb info video.mp4
    """
    try:
        processor = VideoProcessor(video_path)
        meta = processor.metadata

        table = Table(title=f"Informations: {Path(video_path).name}", show_header=True)
        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="yellow")

        table.add_row("Durée", f"{meta['duration']:.2f} secondes ({meta['duration']/60:.1f} minutes)")
        table.add_row("Résolution", f"{meta['width']}x{meta['height']}")
        table.add_row("FPS", f"{meta['fps']:.2f}")
        table.add_row("Codec", meta['codec'])
        table.add_row("Bitrate", f"{meta['bitrate']/1_000_000:.2f} Mbps")
        table.add_row("Taille", f"{Path(video_path).stat().st_size / 1_000_000:.2f} MB")

        console.print("\n")
        console.print(table)
        console.print("\n")

    except Exception as e:
        console.print(f"[bold red]✗ Erreur:[/bold red] {e}", style="red")
        sys.exit(1)


@cli.command()
def styles():
    """
    Affiche les styles de thumbnail disponibles.
    """
    console.print("\n[bold cyan]Styles de Thumbnail Disponibles[/bold cyan]\n")

    for style_name, style_config in ThumbnailComposer.STYLES.items():
        console.print(f"[bold yellow]• {style_name.upper()}[/bold yellow]")
        console.print(f"  Taille police: {style_config['font_size_main']}px")
        console.print(f"  Position: {style_config['position']}")
        console.print(f"  Ombre: {'Oui' if style_config['shadow'] else 'Non'}")
        console.print(f"  Contour: {'Oui' if style_config['outline_width'] > 0 else 'Non'}")
        console.print()


if __name__ == "__main__":
    cli()

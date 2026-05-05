"""
chunk_audio.py — Découpe un audio long en chunks via ffmpeg.

Usage :
    python chunk_audio.py path/to/audio.mp3 --duration 600 --output-dir chunks/

Pré-requis :
    - ffmpeg installé (`apt-get install ffmpeg` ou `brew install ffmpeg`)
"""
import argparse
import subprocess
import sys
from pathlib import Path


def chunk_audio(
    input_path: str,
    chunk_duration_s: int = 600,
    output_dir: str = "chunks",
) -> list[Path]:
    """Découpe un audio en chunks via ffmpeg.

    Args:
        input_path: chemin vers le fichier audio source
        chunk_duration_s: durée de chaque chunk en secondes (défaut 600 = 10 min)
        output_dir: dossier de sortie pour les chunks

    Returns:
        Liste des chemins des chunks générés, triés par ordre.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = str(out_dir / "chunk_%03d.mp3")

    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-f", "segment",
        "-segment_time", str(chunk_duration_s),
        "-c", "copy",
        output_pattern,
        "-y",
        "-loglevel", "error",
    ]
    subprocess.run(cmd, check=True)
    return sorted(out_dir.glob("chunk_*.mp3"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Découpe un audio en chunks")
    parser.add_argument("audio", help="Chemin vers le fichier audio")
    parser.add_argument(
        "--duration", "-d", type=int, default=600,
        help="Durée d'un chunk en secondes (défaut 600 = 10 min)",
    )
    parser.add_argument(
        "--output-dir", "-o", default="chunks", help="Dossier de sortie",
    )
    args = parser.parse_args()

    if not Path(args.audio).exists():
        print(f"❌ Fichier introuvable : {args.audio}", file=sys.stderr)
        return 1

    print(f"📦 Découpage de {args.audio} en chunks de {args.duration}s...")
    chunks = chunk_audio(args.audio, args.duration, args.output_dir)
    print(f"✅ {len(chunks)} chunks générés dans {args.output_dir}/")
    for c in chunks:
        print(f"   - {c.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

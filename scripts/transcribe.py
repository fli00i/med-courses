"""
transcribe.py — Transcription audio multilingue via Groq Whisper

Usage :
    python transcribe.py path/to/audio.mp3 --output transcription.md

Variables d'environnement requises :
    GROQ_API_KEY : clé API Groq (https://console.groq.com)

Optionnel :
    OPENAI_API_KEY : fallback Whisper officiel si Groq quota épuisé
    GOOGLE_API_KEY : fallback Gemini 2.5 Pro si darija mal transcrite
"""
import argparse
import os
import sys
from pathlib import Path

from groq import Groq


GROQ_MODEL = "whisper-large-v3"
GROQ_FILE_LIMIT_MB = 24  # limite Groq = 25 MB, on garde 1 MB de marge
DEFAULT_PROMPT = (
    "Cours de médecine en Algérie. Le professeur alterne entre français, "
    "darija algérienne et arabe standard. Termes médicaux : hypertension, "
    "cardiopathie, hémodynamique, physiopathologie, diagnostic différentiel."
)


def transcribe_with_groq(
    audio_path: str,
    language: str | None = None,
    prompt: str = DEFAULT_PROMPT,
) -> dict:
    """Transcrit un fichier audio via Groq Whisper-large-v3.

    Args:
        audio_path: chemin vers le fichier audio (mp3, wav, m4a, ogg, flac)
        language: code ISO de la langue principale ("fr", "ar", None=auto)
        prompt: prompt initial pour guider Whisper (vocabulaire, contexte)

    Returns:
        dict avec 'text', 'segments' (avec timestamps), 'language', 'duration'
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY manquant. Obtiens une clé sur https://console.groq.com"
        )
    client = Groq(api_key=api_key)

    with open(audio_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=(Path(audio_path).name, audio_file.read()),
            model=GROQ_MODEL,
            response_format="verbose_json",
            language=language,
            temperature=0.0,
            prompt=prompt,
        )
    return result.to_dict() if hasattr(result, "to_dict") else dict(result)


def format_as_markdown(transcription: dict, audio_filename: str = "") -> str:
    """Formate la sortie Whisper en markdown avec timestamps."""
    lines = ["# Transcription du cours\n"]
    if audio_filename:
        lines.append(f"**Fichier source** : `{audio_filename}`")
    lines.append(f"**Langue détectée** : {transcription.get('language', 'auto')}")
    duration = transcription.get("duration", 0)
    if duration:
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        lines.append(f"**Durée** : {h:02d}:{m:02d}:{s:02d}")
    lines.append("")
    lines.append("## Transcription complète avec timestamps\n")

    for seg in transcription.get("segments", []):
        start = seg.get("start", 0)
        m, s = divmod(int(start), 60)
        text = seg.get("text", "").strip()
        lines.append(f"[{m:02d}:{s:02d}] {text}")

    lines.append("")
    lines.append("## Texte intégral (sans timestamps)\n")
    lines.append(transcription.get("text", "").strip())

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcription audio multilingue via Groq Whisper"
    )
    parser.add_argument("audio", help="Chemin vers le fichier audio")
    parser.add_argument(
        "--output", "-o", default="transcription.md", help="Fichier de sortie markdown"
    )
    parser.add_argument(
        "--language", "-l", default=None, help='Langue principale ("fr", "ar", None)'
    )
    parser.add_argument(
        "--prompt", "-p", default=DEFAULT_PROMPT, help="Prompt initial pour Whisper"
    )
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"❌ Fichier introuvable : {audio_path}", file=sys.stderr)
        return 1

    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb > GROQ_FILE_LIMIT_MB:
        print(
            f"⚠️  Audio trop gros ({size_mb:.1f} MB > {GROQ_FILE_LIMIT_MB} MB). "
            f"Utilise chunk_audio.py pour découper avant.",
            file=sys.stderr,
        )
        return 2

    print(f"🎤 Transcription de {audio_path} ({size_mb:.1f} MB)...")
    result = transcribe_with_groq(
        str(audio_path), language=args.language, prompt=args.prompt
    )

    md = format_as_markdown(result, audio_filename=audio_path.name)
    Path(args.output).write_text(md, encoding="utf-8")

    n_segments = len(result.get("segments", []))
    print(f"✅ Transcription sauvegardée dans {args.output}")
    print(f"   Langue détectée : {result.get('language')}")
    print(f"   Durée : {result.get('duration', 0):.1f} s")
    print(f"   Segments : {n_segments}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

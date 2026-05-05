"""
fallback_gemini.py — Transcription audio via Gemini 2.5 Pro.

À utiliser comme fallback quand Whisper galère sur les passages en darija
algérienne. Gemini 2.5 Pro gère nativement le code-switching FR/AR/darija.

Usage :
    python fallback_gemini.py path/to/audio.mp3 --output transcription_gemini.md

Variables d'environnement requises :
    GOOGLE_API_KEY : clé API Gemini (https://aistudio.google.com)

Note : utilise le SDK officiel `google-genai` (et non l'ancien `google-generativeai`).
"""
import argparse
import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types


GEMINI_MODEL = "gemini-2.5-pro"
GEMINI_PROMPT = """Tu es un transcripteur expert spécialisé dans les contenus académiques médicaux multilingues.

CONTEXTE
Voici un enregistrement d'un cours de médecine donné en Algérie. Le professeur alterne entre français, darija algérienne et arabe standard. Les termes médicaux sont essentiellement en français.

TÂCHES
1. Transcris l'INTÉGRALITÉ de l'audio en respectant la langue parlée pour chaque segment.
2. Marque chaque changement de langue avec une étiquette : [FR], [DARIJA], [AR].
3. Ajoute des timestamps tous les 30 secondes au format [MM:SS].
4. À la fin, fournis une version 100 % française du cours, en traduisant les segments en darija/arabe tout en CONSERVANT les termes médicaux dans leur langue d'origine.

FORMAT DE SORTIE EXACT

## TRANSCRIPTION ORIGINALE (multilingue)
[00:00] [FR] ...
[00:30] [DARIJA] ... (traduction française : ...)

## TRANSCRIPTION FRANÇAISE COMPLÈTE
[00:00] ...

CONTRAINTES
- Ne résume rien : transcription mot pour mot.
- Si tu n'es pas sûr d'un mot médical, écris-le entre guillemets et propose une alternative.
"""


def transcribe_with_gemini(audio_path: str, prompt: str = GEMINI_PROMPT) -> str:
    """Transcrit un audio via Gemini 2.5 Pro (gère le code-switching FR/AR/darija).

    Args:
        audio_path: chemin vers le fichier audio
        prompt: prompt pour Gemini

    Returns:
        Transcription brute en markdown.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY manquant. Obtiens une clé sur https://aistudio.google.com"
        )

    client = genai.Client(api_key=api_key)

    print(f"📤 Upload de {audio_path} vers Gemini...")
    audio_file = client.files.upload(file=audio_path)

    # Attendre que le fichier soit ACTIVE
    while audio_file.state == "PROCESSING":
        print("   ⏳ Traitement en cours...")
        time.sleep(2)
        audio_file = client.files.get(name=audio_file.name)

    if audio_file.state != "ACTIVE":
        raise RuntimeError(f"Échec upload Gemini : {audio_file.state}")

    print("🎤 Transcription via Gemini 2.5 Pro...")
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt, audio_file],
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=65536,
        ),
    )
    return response.text


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcription audio via Gemini 2.5 Pro (fallback darija)"
    )
    parser.add_argument("audio", help="Chemin vers le fichier audio")
    parser.add_argument(
        "--output", "-o", default="transcription_gemini.md", help="Fichier de sortie",
    )
    args = parser.parse_args()

    if not Path(args.audio).exists():
        print(f"❌ Fichier introuvable : {args.audio}", file=sys.stderr)
        return 1

    transcription = transcribe_with_gemini(args.audio)
    Path(args.output).write_text(transcription, encoding="utf-8")
    print(f"✅ Transcription sauvegardée dans {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

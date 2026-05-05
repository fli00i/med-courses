"""
pipeline.py — Pipeline complet : Whisper + extraction slides + Claude Opus 4.7.

Usage :
    python pipeline.py audio.mp3 slides.pdf "Cardiologie" "HTA de l'adulte" 2026-01-15

Variables d'environnement requises :
    GROQ_API_KEY      : Whisper (https://console.groq.com)
    ANTHROPIC_API_KEY : Claude Opus 4.7 (https://console.anthropic.com)

Optionnel :
    GOOGLE_API_KEY : fallback Gemini si Whisper darija mauvais
    OPENAI_API_KEY : fallback Whisper officiel si Groq quota épuisé
"""
import argparse
import os
import sys
from pathlib import Path

# Imports locaux
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from chunk_audio import chunk_audio
from extract_slides import extract_slides_text, slides_to_markdown
from transcribe import transcribe_with_groq, format_as_markdown


GROQ_FILE_LIMIT_MB = 24
CHUNK_DURATION_S = 600  # 10 min
CLAUDE_MODEL = "claude-opus-4-5-20250929"  # adapte si Opus 4.7 dispo
CLAUDE_MAX_TOKENS = 16000
CLAUDE_MAX_CONTINUE_ROUNDS = 5

PROMPTS_DIR = SCRIPT_DIR.parent / "prompts"


def transcribe_full_audio(audio_path: str, work_dir: Path) -> dict:
    """Transcrit un audio complet, en découpant en chunks si nécessaire."""
    size_mb = Path(audio_path).stat().st_size / (1024 * 1024)
    print(f"🎤 Audio : {size_mb:.1f} MB")

    if size_mb <= GROQ_FILE_LIMIT_MB:
        print("   → 1 seul appel Groq")
        return transcribe_with_groq(audio_path)

    print(f"   → découpage en chunks de {CHUNK_DURATION_S}s")
    chunks_dir = work_dir / "chunks"
    chunks = chunk_audio(audio_path, CHUNK_DURATION_S, str(chunks_dir))

    all_segments = []
    full_text_parts = []
    detected_languages = []
    total_duration = 0.0

    for i, chunk_path in enumerate(chunks):
        offset_s = i * CHUNK_DURATION_S
        print(f"   🎤 Chunk {i + 1}/{len(chunks)} (offset {offset_s}s)...")
        data = transcribe_with_groq(str(chunk_path))

        # Décale les timestamps de l'offset
        for seg in data.get("segments", []):
            seg["start"] = seg.get("start", 0) + offset_s
            seg["end"] = seg.get("end", 0) + offset_s
            all_segments.append(seg)

        full_text_parts.append(data.get("text", "").strip())
        detected_languages.append(data.get("language", ""))
        total_duration += data.get("duration", 0)

    # Détermine la langue dominante
    from collections import Counter
    lang_counts = Counter(l for l in detected_languages if l)
    dominant_lang = lang_counts.most_common(1)[0][0] if lang_counts else "auto"

    return {
        "text": " ".join(full_text_parts),
        "segments": all_segments,
        "language": dominant_lang,
        "duration": total_duration,
    }


def call_claude_opus(system_prompt: str, user_prompt: str) -> str:
    """Appelle Claude Opus avec gestion automatique du 'continue' si tronqué."""
    from anthropic import Anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY manquant")
    client = Anthropic(api_key=api_key)

    accumulated = []
    for round_n in range(CLAUDE_MAX_CONTINUE_ROUNDS):
        if round_n == 0:
            messages = [{"role": "user", "content": user_prompt}]
        else:
            messages = [
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": "".join(accumulated)},
                {"role": "user", "content": "continue"},
            ]

        print(f"   🤖 Round {round_n + 1}/{CLAUDE_MAX_CONTINUE_ROUNDS}...")
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=system_prompt,
            messages=messages,
        )

        text = "".join(
            block.text for block in msg.content if hasattr(block, "text")
        )
        accumulated.append(text)

        if msg.stop_reason != "max_tokens":
            print(f"   ✅ Réponse complète (stop_reason={msg.stop_reason})")
            break
        print(f"   ⏩ Réponse tronquée → continue...")
    else:
        print(f"   ⚠️  Max rounds atteint ({CLAUDE_MAX_CONTINUE_ROUNDS})")

    return "".join(accumulated)


def build_user_prompt(
    template: str,
    transcription_md: str,
    slides_text: str,
    specialite: str,
    titre: str,
    date: str,
    duree: str = "?",
    nb_diapos: int = 0,
    referentiels: str = "Aucun référentiel fourni dans cet appel.",
) -> str:
    return template.format(
        specialite=specialite,
        titre=titre,
        date=date,
        duree=duree,
        nb_diapos=nb_diapos,
        referentiels=referentiels,
        transcription=transcription_md,
        slides_text=slides_text,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline complet cours médical : Whisper + slides + Claude Opus"
    )
    parser.add_argument("audio", help="Chemin vers le fichier audio (mp3, etc.)")
    parser.add_argument("slides", help="Chemin vers le PDF des diapositives")
    parser.add_argument("specialite", help='ex. "Cardiologie"')
    parser.add_argument("titre", help='ex. "Hypertension artérielle"')
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument(
        "--out-dir", "-o", default=None,
        help="Dossier de sortie (défaut : cours/{date}_{specialite}_{titre_slug}/)",
    )
    parser.add_argument(
        "--skip-claude", action="store_true",
        help="Skipper l'appel Claude (utile pour tester juste Whisper + slides)",
    )
    args = parser.parse_args()

    # Préparation du dossier de sortie
    if args.out_dir:
        out_dir = Path(args.out_dir)
    else:
        slug = args.titre.lower().replace(" ", "_").replace("'", "")[:40]
        out_dir = (
            SCRIPT_DIR.parent
            / "cours"
            / f"{args.date}_{args.specialite.lower()}_{slug}"
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 Output : {out_dir}/")

    # Étape 1 — Whisper
    print("\n🎯 Étape 1/3 — Transcription Whisper")
    transcription = transcribe_full_audio(args.audio, out_dir)
    transcription_md = format_as_markdown(transcription, audio_filename=Path(args.audio).name)
    (out_dir / "transcription.md").write_text(transcription_md, encoding="utf-8")
    print(f"   → {out_dir / 'transcription.md'}")

    # Étape 2 — Slides
    print("\n🎯 Étape 2/3 — Extraction texte des slides")
    slides = extract_slides_text(args.slides)
    slides_md = slides_to_markdown(slides, pdf_filename=Path(args.slides).name)
    (out_dir / "slides_text.md").write_text(slides_md, encoding="utf-8")
    print(f"   → {out_dir / 'slides_text.md'} ({len(slides)} diapositives)")

    if args.skip_claude:
        print("\n⏩ Skip Claude (--skip-claude)")
        return 0

    # Étape 3 — Claude Opus
    print("\n🎯 Étape 3/3 — Analyse Claude Opus 4.7")
    system_prompt = (PROMPTS_DIR / "system_prompt_claude_med_tuteur.md").read_text(
        encoding="utf-8"
    )
    task_template = (PROMPTS_DIR / "task_prompt_claude_med.md").read_text(
        encoding="utf-8"
    )
    duration_s = int(transcription.get("duration", 0))
    h, m = divmod(duration_s, 3600)
    m, s = divmod(m, 60)
    duree = f"{h:02d}:{m:02d}:{s:02d}"

    user_prompt = build_user_prompt(
        task_template,
        transcription_md=transcription_md,
        slides_text=slides_md,
        specialite=args.specialite,
        titre=args.titre,
        date=args.date,
        duree=duree,
        nb_diapos=len(slides),
    )
    synthese = call_claude_opus(system_prompt, user_prompt)
    (out_dir / "synthese_complete.md").write_text(synthese, encoding="utf-8")
    print(f"   → {out_dir / 'synthese_complete.md'}")

    print("\n✅ Pipeline terminé.")
    print(f"   Tous les fichiers sont dans {out_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

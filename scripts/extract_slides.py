"""
extract_slides.py — Extraction du texte des diapositives d'un PDF.

Usage :
    python extract_slides.py path/to/slides.pdf --output slides_text.md

Utilise PyMuPDF (fitz) pour extraire le texte de chaque page.
"""
import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF


def extract_slides_text(pdf_path: str) -> list[dict]:
    """Extrait le texte de chaque diapositive d'un PDF.

    Args:
        pdf_path: chemin vers le fichier PDF

    Returns:
        Liste de dicts {numero, texte, n_caracteres}
    """
    doc = fitz.open(pdf_path)
    slides = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        slides.append({
            "numero": i,
            "texte": text,
            "n_caracteres": len(text),
        })
    doc.close()
    return slides


def slides_to_markdown(slides: list[dict], pdf_filename: str = "") -> str:
    """Formate les slides en markdown."""
    lines = ["# Texte des diapositives\n"]
    if pdf_filename:
        lines.append(f"**Fichier source** : `{pdf_filename}`")
    lines.append(f"**Nombre de diapositives** : {len(slides)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for slide in slides:
        n = slide["numero"]
        text = slide["texte"]
        lines.append(f"### Diapositive {n}")
        lines.append("")
        if text:
            lines.append(text)
        else:
            lines.append("*(diapositive sans texte extractible — image, schéma ou diapo vide)*")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extraction texte d'un PDF de slides")
    parser.add_argument("pdf", help="Chemin vers le fichier PDF")
    parser.add_argument(
        "--output", "-o", default="slides_text.md", help="Fichier de sortie markdown",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"❌ Fichier introuvable : {pdf_path}", file=sys.stderr)
        return 1

    print(f"📄 Extraction du texte de {pdf_path}...")
    slides = extract_slides_text(str(pdf_path))

    md = slides_to_markdown(slides, pdf_filename=pdf_path.name)
    Path(args.output).write_text(md, encoding="utf-8")

    total_chars = sum(s["n_caracteres"] for s in slides)
    print(f"✅ Extraction sauvegardée dans {args.output}")
    print(f"   {len(slides)} diapositives, {total_chars} caractères au total")
    return 0


if __name__ == "__main__":
    sys.exit(main())

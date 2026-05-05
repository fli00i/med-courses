"""Génère un échantillon de test : 5 diapositives PDF sur l'HTA + une transcription factice.

Utilité : valider le pipeline sans devoir uploader un vrai cours.
"""
import fitz
from pathlib import Path

OUT_DIR = Path(__file__).parent
SLIDES_PDF = OUT_DIR / "slides.pdf"
TRANSCRIPT_MD = OUT_DIR / "transcription_factice.md"


SLIDES = [
    {
        "titre": "Hypertension artérielle (HTA) — Définition",
        "contenu": [
            "PA ≥ 140/90 mmHg au cabinet (mesure répétée)",
            "PA ≥ 135/85 mmHg en automesure tensionnelle (AMT)",
            "PA ≥ 130/80 mmHg en MAPA diurne",
            "1ère cause de morbi-mortalité cardiovasculaire",
            "Prévalence : 30 % des adultes en France",
        ],
    },
    {
        "titre": "Classification de l'HTA (ESC/ESH 2023)",
        "contenu": [
            "PA optimale : <120/80",
            "PA normale : 120-129/80-84",
            "PA normale haute : 130-139/85-89",
            "HTA grade 1 : 140-159/90-99",
            "HTA grade 2 : 160-179/100-109",
            "HTA grade 3 : ≥180/≥110",
        ],
    },
    {
        "titre": "HTA secondaire : étiologies",
        "contenu": [
            "Endocrines : hyperaldostéronisme primaire (Conn), phéochromocytome, Cushing",
            "Rénales : sténose des artères rénales, glomérulopathies",
            "Iatrogènes : AINS, corticoïdes, oestroprogestatifs",
            "Apnée du sommeil",
            "Coarctation aortique",
        ],
    },
    {
        "titre": "Bilan initial OMS de l'HTA",
        "contenu": [
            "Biologie : créatininémie + DFG, kaliémie, glycémie, bilan lipidique",
            "BU + microalbuminurie",
            "ECG 12 dérivations",
            "Recherche signes d'atteinte d'organe cible",
            "Évaluation du risque cardiovasculaire global (SCORE2)",
        ],
    },
    {
        "titre": "Traitement de 1ère intention",
        "contenu": [
            "Mesures hygiéno-diététiques : sel <6 g/j, activité physique, perte de poids",
            "Bithérapie d'emblée recommandée",
            "5 classes de 1ère intention : IEC, ARA II, inhibiteurs calciques, diurétiques thiazidiques, β-bloquants",
            "Cible : <140/90 (<130/80 si bien toléré)",
            "ATTENTION : β-bloquants désormais en 4e ligne sauf indication spécifique",
        ],
    },
]

# Transcription factice — ce qu'un prof aurait pu dire (mélange de lecture +
# d'ajouts) pour tester le filtrage verbatim
TRANSCRIPTION = """# Transcription du cours
**Fichier source** : `audio_factice.mp3`
**Langue détectée** : fr
**Durée** : 00:08:30

## Transcription complète avec timestamps

[00:00] Donc bonjour à tous, aujourd'hui on va parler de l'hypertension artérielle, c'est un sujet qui tombe quasiment chaque année au résidanat, donc soyez attentifs.
[00:30] On définit l'HTA par une pression artérielle supérieure ou égale à 140 sur 90 millimètres de mercure mesurée au cabinet, en mesures répétées bien sûr, jamais sur une seule mesure.
[01:00] Pour l'automesure, le seuil descend à 135 sur 85, et en MAPA diurne c'est 130 sur 80. Retenez ces trois chiffres, vous aurez forcément une question dessus.
[01:30] La prévalence en France est de 30%, en Algérie c'est plutôt autour de 35-40% selon les études récentes du registre TAHINA, donc encore plus fréquent chez nous.
[02:00] Passons à la classification de l'ESC 2023. Donc PA optimale moins de 120 sur 80, PA normale 120-129, normale haute 130-139, et on commence l'HTA à 140-159 pour le grade 1.
[02:30] Petit moyen mnémotechnique : "Optimal-Normal-Normale haute-puis grades", en augmentant de 20 mmHg systolique à chaque cran.
[03:00] Pour les étiologies secondaires, c'est important parce qu'il faut TOUJOURS éliminer une cause secondaire chez un patient jeune, moins de 30 ans, ou en cas d'HTA résistante.
[03:30] Les principales : l'hyperaldostéronisme primaire ou maladie de Conn, le phéochromocytome qui donne la triade de Ménard — céphalées, sueurs, palpitations — apprenez-la par cœur.
[04:00] Le syndrome de Cushing aussi, on cherche le faciès lunaire, la bosse de bison. Et n'oubliez pas la sténose des artères rénales, surtout chez le sujet âgé athéromateux.
[04:30] Iatrogènes : AINS attention, corticoïdes, et la pilule oestroprogestative — toujours demander à une jeune femme.
[05:00] Le bilan initial selon l'OMS comprend : créatininémie avec DFG, kaliémie — c'est crucial avant d'introduire un IEC ou un ARA II — glycémie à jeun, bilan lipidique avec LDL.
[05:30] Bandelette urinaire pour la microalbuminurie, c'est un marqueur précoce d'atteinte rénale, et l'ECG 12 dérivations pour chercher l'hypertrophie ventriculaire gauche.
[06:00] Le SCORE2 c'est le nouveau calculateur européen de risque cardiovasculaire à 10 ans, il a remplacé le SCORE classique en 2021. Apprenez bien ça pour les EDN.
[06:30] Traitement, sujet majeur. D'abord les RHD : sel moins de 6 grammes par jour — en pratique en Algérie c'est dur avec le pain et l'olive — activité physique 30 minutes 5 fois par semaine, et perte de poids si IMC élevé.
[07:00] Bithérapie d'emblée : c'est la grande nouveauté ESC 2018 confirmée en 2023. On ne fait plus de monothérapie sauf chez les sujets très âgés fragiles.
[07:30] Les 5 classes : IEC, ARA II, inhibiteurs calciques type amlodipine, diurétiques thiazidiques comme l'hydrochlorothiazide ou l'indapamide, et les bêta-bloquants.
[08:00] ATTENTION POINT D'EXAMEN : depuis 2018 les bêta-bloquants ne sont plus de 1ère intention sauf s'il y a une indication spécifique — coronaropathie, insuffisance cardiaque à FE altérée, post-IDM. Sinon ils sont en 4ème ligne. Ça tombe TRÈS souvent.
[08:30] La cible tensionnelle c'est moins de 140 sur 90 pour tout le monde, et on peut viser moins de 130 sur 80 si c'est bien toléré, surtout chez le diabétique ou le coronarien.
"""


def build_pdf():
    """Génère un PDF de 5 diapositives sur l'HTA."""
    doc = fitz.open()
    for i, slide in enumerate(SLIDES, start=1):
        # Format slide 16:9 horizontal
        page = doc.new_page(width=842, height=595)
        # Titre
        page.insert_textbox(
            fitz.Rect(40, 40, 802, 100),
            f"Diapo {i}/{len(SLIDES)} — {slide['titre']}",
            fontsize=22,
            fontname="helvetica-bold",
            color=(0.1, 0.1, 0.4),
        )
        # Contenu (puces)
        y = 130
        for puce in slide["contenu"]:
            page.insert_textbox(
                fitz.Rect(60, y, 802, y + 50),
                f"• {puce}",
                fontsize=14,
                fontname="helvetica",
            )
            y += 35
        # Footer
        page.insert_textbox(
            fitz.Rect(40, 560, 802, 590),
            "Cardiologie — 6e année — Fac. de Médecine d'Alger — Échantillon de test",
            fontsize=9,
            fontname="helvetica-oblique",
            color=(0.5, 0.5, 0.5),
        )
    doc.save(SLIDES_PDF)
    doc.close()
    print(f"✅ PDF généré : {SLIDES_PDF}")


def build_transcription():
    TRANSCRIPT_MD.write_text(TRANSCRIPTION, encoding="utf-8")
    print(f"✅ Transcription factice : {TRANSCRIPT_MD}")


if __name__ == "__main__":
    build_pdf()
    build_transcription()
    print("\nÉchantillon prêt :")
    print(f"  - {SLIDES_PDF}")
    print(f"  - {TRANSCRIPT_MD}")

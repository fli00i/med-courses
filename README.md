# med-courses — Pipeline IA pour cours de médecine

Pipeline automatisé pour traiter des cours de médecine (audio + slides) :
1. **Whisper** → transcription multilingue (FR / Darija / Arabe)
2. **PyMuPDF** → extraction du texte des diapositives
3. **Claude Opus 4.7** → alignement, filtrage du verbatim, explications enrichies, génération de QCM (EDN + résidanat algérien)

Conçu pour un étudiant de 6e année à la Faculté de Médecine d'Alger préparant les EDN françaises et le concours de résidanat algérien.

---

## Structure du repo

```
med-courses/
├── prompts/
│   ├── system_prompt_claude_med_tuteur.md   # Identité permanente de Claude
│   └── task_prompt_claude_med.md             # Prompt à coller à chaque cours
├── scripts/
│   ├── transcribe.py                         # Transcription Whisper (Groq)
│   ├── chunk_audio.py                        # Découpe audio long en chunks
│   ├── extract_slides.py                     # Extraction texte des PDFs
│   ├── pipeline.py                           # Pipeline complet tout-en-un
│   └── fallback_gemini.py                    # Fallback transcription Gemini 2.5 Pro
├── cours/                                    # Un dossier par cours traité
│   └── YYYY-MM-DD_specialite_titre/
│       ├── audio.mp3
│       ├── slides.pdf
│       ├── transcription.md
│       ├── slides_text.md
│       └── synthese_complete.md
├── referentiels/                             # Sources fiables
│   ├── colleges_edn/
│   ├── polycopies_alger/
│   ├── has_recommandations/
│   ├── annales_edn/
│   └── annales_residanat/
├── sample/                                   # Échantillon de test
└── requirements.txt
```

---

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/fli00i/med-courses.git
cd med-courses

# 2. Installer les dépendances système
sudo apt-get install -y ffmpeg

# 3. Installer les dépendances Python
pip install -r requirements.txt

# 4. Configurer les clés API
export GROQ_API_KEY=...           # Whisper rapide gratuit (https://console.groq.com)
export ANTHROPIC_API_KEY=...      # Claude Opus 4.7 (https://console.anthropic.com)
export GOOGLE_API_KEY=...         # Optionnel, fallback Gemini 2.5 Pro
export OPENAI_API_KEY=...         # Optionnel, fallback Whisper officiel
```

---

## Utilisation

### Option A — Pipeline complet en une commande (local)

```bash
python scripts/pipeline.py \
  path/to/audio.mp3 \
  path/to/slides.pdf \
  "Cardiologie" \
  "Hypertension artérielle de l'adulte" \
  2026-01-15
```

Sortie dans `output/` :
- `transcription.md`
- `slides_text.md`
- `synthese_complete.md`

### Option B — Étape par étape

```bash
# 1. Transcription
python scripts/transcribe.py audio.mp3 --output transcription.md

# 2. Extraction texte des slides
python scripts/extract_slides.py slides.pdf --output slides_text.md

# 3. Analyse Claude Opus (à faire manuellement avec les prompts)
#    Utilise prompts/system_prompt_claude_med_tuteur.md comme system prompt
#    et prompts/task_prompt_claude_med.md comme user prompt
```

### Option C — Via Devin AI (recommandé)

1. Lance le Playbook **Med Course Pipeline** dans Devin AI.
2. Upload `audio.mp3` + `slides.pdf` dans la session.
3. Renseigne les variables : `cours_specialite`, `cours_titre`, `cours_date`.
4. Devin exécute tout et ouvre une PR sur ce repo avec les fichiers générés.

---

## Coûts indicatifs

| Service | Coût |
|---|---|
| Groq Whisper | **Gratuit** (free tier 14 400 req/jour) |
| Claude Opus 4.7 | ~3-5 USD par cours complet |
| Gemini 2.5 Pro (fallback) | Gratuit (quota AI Studio) |
| OpenAI Whisper (fallback) | ~0.50 USD par heure d'audio |

---

## Niveau et programme

- **Étudiant cible** : 6e année de médecine
- **Examens visés** :
  - EDN françaises / R2C (Épreuves Dématérialisées Nationales)
  - Concours de résidanat algérien
- **Sources prioritaires** : Collèges des Enseignants français, polycopiés des facultés algériennes, recommandations HAS, Pilly, Manuel MSD

---

## Licence

Usage strictement personnel. Les contenus de cours et les enregistrements ne doivent pas être redistribués.

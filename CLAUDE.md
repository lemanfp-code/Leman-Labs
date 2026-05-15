# Dossier Synthesizer — Instructions pour Claude Code

## Contexte

**Dossier Synthesizer** est l'outil interne unifié qui transforme les replays
vidéo de webinaires/conférences crypto en dossiers de synthèse formatés.
Il remplace les deux outils séparés historiques (CPC Synthesizer, CRY
Synthesizer) : ~95 % du code était commun, la seule vraie spécificité étant
le **prompt système** et quelques métadonnées. Tout cela est désormais
factorisé derrière la notion de **programme**.

Un membre de l'équipe interne choisit son programme (CPC, CRY, ou un futur
programme), envoie sa vidéo, et récupère sa synthèse. Les synthèses passées
sont conservées par programme (la « mémoire »).

**Stack :**
- Python 3.13 (venv arm64 sur Apple Silicon) / FastAPI + uvicorn
- Transcription : faster-whisper local (modèle `small`)
- Synthèse : Anthropic Claude (`claude-sonnet-4-6`)
- Extraction audio : ffmpeg
- Front : HTML/CSS/JS vanilla, mono-page, thème dynamique par programme
- Pas de base de données — fichiers locaux (`outputs/<programme>/`)

## Architecture

```
dossier-synthesizer/
├── app/
│   ├── main.py              ← FastAPI : routes, pipeline async, program-aware
│   ├── programs/__init__.py ← REGISTRE des programmes (LE point d'extension)
│   ├── pipeline/
│   │   ├── audio.py         ← ffmpeg : vidéo → WAV 16kHz mono
│   │   ├── transcriber.py   ← faster-whisper + glossaire crypto
│   │   └── synthesizer.py   ← Claude API, prompt = celui du programme
│   ├── prompts/
│   │   ├── cpc_prompt.txt   ← prompt système CPC (8 blocs)
│   │   └── cry_prompt.txt   ← prompt système CRY (6 blocs)
│   └── static/index.html    ← sélecteur de programme + upload + historique
├── uploads/                 ← vidéos temporaires (auto-nettoyées)
├── outputs/<programme>/     ← synthèses + transcriptions persistées
├── .env                     ← clés API (JAMAIS commité)
├── Dockerfile / docker-compose.yml
└── run.py                   ← point d'entrée local
```

## Notion de « programme »

Tout ce qui distingue un dossier d'un autre vit dans `app/programs/__init__.py` :
`id`, `name`, `short` (préfixe fichier), `webinar_name`, `prompt_file`,
`tagline`, `format_label`, `speakers`, `theme` (surcharges CSS).

**Ajouter un programme = 2 gestes, zéro autre code :**
1. Déposer `app/prompts/<x>_prompt.txt`
2. Ajouter une entrée `Program(...)` dans `PROGRAMS`

Le front lit `/api/programs` et génère seul le sélecteur + le thème.

## Pipeline

1. Choix du programme (front) → 2. Upload vidéo → 3. Extraction audio ffmpeg
→ 4. Transcription faster-whisper → 5. Synthèse Claude avec le prompt du
programme → 6. Sauvegarde dans `outputs/<programme>/` + affichage.

## Règles critiques

- **Le prompt EST le produit** — 80 % de la qualité. Ne jamais le dégrader
  pour « simplifier ». Chaque programme garde son prompt validé en prod.
- **Ne JAMAIS inventer de données** : uniquement ce qui est dans le transcript.
- **Fidélité des intervenants** : noms exacts, depuis `program.speakers`.
- **Ne jamais committer `.env`** ni `venv/` ni `outputs/` (gitignored).
- Le pipeline (audio/transcriber) est commun à tous les programmes : ne pas
  y introduire de logique spécifique à un programme — ça va dans le registre.
- Coût API à surveiller : `claude-sonnet-4-6` ≈ $3/$15 par 1M tokens.

## Config (.env)

```
ANTHROPIC_API_KEY=sk-ant-xxxxx
CLAUDE_MODEL=claude-sonnet-4-6
CLAUDE_MAX_TOKENS=16000
WHISPER_MODEL=small
PORT=8000
```

## État

- Issu de la fusion CPC + CRY (mai 2026), tous deux validés en prod.
- Phase 1 faite : codebase unifié, sélecteur de programme, thème dynamique,
  sorties par programme.
- À venir : Phase 2 (page mémoire/historique enrichie), Phase 3 (déploiement
  en ligne — VPS Hetzner + Cloudflare Tunnel + auth HTTP Basic).

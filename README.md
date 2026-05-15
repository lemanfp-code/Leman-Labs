# Dossier Synthesizer

Outil interne unifié de synthèse de webinaires/conférences crypto.
Vidéo → transcription locale → dossier de synthèse formaté, par **programme**.

Remplace les outils séparés *CPC Synthesizer* et *CRY Synthesizer* : un seul
codebase, le programme (CPC, CRY, ou futur) n'est plus que de la configuration.

## Démarrage local

```bash
python3.13 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # puis renseigner ANTHROPIC_API_KEY
python run.py                  # → http://localhost:8000
```
Pré-requis : `ffmpeg` (`brew install ffmpeg`).

## Utilisation

1. Ouvrir http://localhost:8000
2. Choisir le programme (CPC / CRY / …)
3. Glisser-déposer la vidéo du replay, renseigner mois/année
4. Récupérer le `.md` (et la transcription `.txt`)

Les dossiers générés sont conservés dans `outputs/<programme>/`.

## Ajouter un programme

1. Déposer le prompt système dans `app/prompts/<id>_prompt.txt`
2. Ajouter une entrée `Program(...)` dans `app/programs/__init__.py`

Aucune autre modification : le front et le pipeline s'adaptent seuls.

## Déploiement (à venir)

Dockerfile + docker-compose fournis. Cible : VPS + Cloudflare Tunnel + auth.

## Privé / interne

Outil propriétaire. Ne jamais committer `.env`, `venv/`, ni `outputs/`.

"""Persistance de la « mémoire » : un sidecar JSON par dossier généré.

Pas de base de données (choix assumé). Pour chaque synthèse terminée on
écrit `outputs/<programme>/<job_id>.json` avec ses métadonnées, à côté du
`<job_id>_synthese.md` et `<job_id>_transcription.txt`. L'historique
survit donc aux redémarrages du serveur.
"""

import json
import os
from pathlib import Path

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

# Champs persistés (sous-ensemble sérialisable du job en mémoire)
RECORD_FIELDS = (
    "id", "program", "program_name", "status",
    "month", "year", "title", "filename",
    "created_at", "completed_at", "cost_usd",
    "video_size_mb", "audio_duration_min",
    "synthesis_path", "transcription_path", "docx_path",
    "slides_used",
)


def to_record(job: dict) -> dict:
    return {k: job.get(k) for k in RECORD_FIELDS}


def save_record(job: dict) -> None:
    """Écrit le sidecar JSON. Appelé quand un job se termine avec succès."""
    program = job.get("program") or "_unknown"
    d = OUTPUTS_DIR / program
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{job['id']}.json").write_text(
        json.dumps(to_record(job), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def list_records(program_id: str = "") -> list[dict]:
    """Tous les dossiers persistés, pour un programme ou tous."""
    if not OUTPUTS_DIR.exists():
        return []
    dirs = [OUTPUTS_DIR / program_id] if program_id else [
        p for p in OUTPUTS_DIR.iterdir() if p.is_dir()
    ]
    out: list[dict] = []
    for d in dirs:
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                pass
    return out


def find_record(job_id: str) -> dict | None:
    """Retrouve un dossier persisté par son id, quel que soit le programme."""
    if not OUTPUTS_DIR.exists():
        return None
    for f in OUTPUTS_DIR.glob(f"*/{job_id}.json"):
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    return None


def delete_record(job_id: str) -> None:
    """Supprime le sidecar + les fichiers .md/.txt associés."""
    if not OUTPUTS_DIR.exists():
        return
    for f in OUTPUTS_DIR.glob(f"*/{job_id}.json"):
        rec = None
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if rec:
            for key in ("synthesis_path", "transcription_path", "docx_path"):
                p = rec.get(key)
                if p and os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        try:
            f.unlink()
        except OSError:
            pass

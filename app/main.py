import os
import sys
from pathlib import Path

# Permet d'importer `pipeline` et `programs` comme modules top-level
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ffmpeg/ffprobe installés via Homebrew sur macOS Apple Silicon
os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")

"""Dossier Synthesizer — Serveur FastAPI unifié (multi-programmes)."""
import uuid
import shutil
import asyncio
import logging
import traceback
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from programs import get_program, list_programs

load_dotenv()

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dossier-synthesizer")

# --- Validation clé API au démarrage ---
api_key = os.getenv("ANTHROPIC_API_KEY", "")
if not api_key or api_key.startswith("sk-ant-xxx"):
    logger.warning("⚠️  ANTHROPIC_API_KEY manquante ou invalide dans .env")

# --- App ---
app = FastAPI(title="Dossier Synthesizer", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Dossiers
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
OUTPUTS_DIR = BASE_DIR / "outputs"
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)


def program_output_dir(program_id: str) -> Path:
    """outputs/<programme>/ — la 'mémoire' des dossiers, isolée par programme."""
    d = OUTPUTS_DIR / program_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# Statut des jobs en cours (en mémoire ; les fichiers persistent sur disque)
jobs = {}

# --- Servir la landing page ---
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = Path(__file__).parent / "static" / "index.html"
    return index_path.read_text(encoding="utf-8")


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/api/programs")
async def get_programs():
    """Liste des programmes disponibles (pour le sélecteur du front)."""
    return list_programs()


# --- API Endpoints ---

@app.post("/api/upload")
async def upload_video(
    video: UploadFile = File(...),
    month: str = Form(""),
    year: str = Form(""),
    title: str = Form(""),
    program: str = Form(""),
):
    """Upload une vidéo et lance le pipeline de traitement pour un programme donné."""
    prog = get_program(program)

    if not video.filename.lower().endswith(('.mp4', '.webm', '.mkv', '.avi', '.mov', '.mp3', '.m4a', '.wav', '.ogg', '.flac')):
        raise HTTPException(400, "Format non supporté.")

    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-xxx"):
        raise HTTPException(400, "Clé API Anthropic non configurée. Ajoute-la dans le fichier .env")

    job_id = str(uuid.uuid4())[:8]
    video_path = UPLOADS_DIR / f"{job_id}_{video.filename}"

    with open(video_path, "wb") as f:
        while chunk := await video.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)

    size_mb = os.path.getsize(video_path) / (1024 * 1024)
    logger.info(f"[JOB {job_id}] {prog.id} — vidéo uploadée : {video.filename} ({size_mb:.0f} MB)")

    if not month or not year:
        now = datetime.now()
        month = month or now.strftime("%B")
        year = year or str(now.year)

    jobs[job_id] = {
        "id": job_id,
        "program": prog.id,
        "program_name": prog.name,
        "status": "uploaded",
        "step": "upload",
        "progress": 0,
        "video_path": str(video_path),
        "video_size_mb": round(size_mb, 1),
        "month": month,
        "year": year,
        "title": title,
        "filename": video.filename,
        "created_at": datetime.now().isoformat(),
        "transcription": None,
        "synthesis": None,
        "error": None,
    }

    asyncio.create_task(run_pipeline(job_id))
    return {"job_id": job_id, "program": prog.id, "message": "Pipeline lancé", "video_size_mb": round(size_mb, 1)}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job non trouvé")
    return jobs[job_id]


@app.get("/api/result/{job_id}")
async def get_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job non trouvé")
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(400, f"Job en cours : {job['step']}")
    return {
        "synthesis": job["synthesis"],
        "transcription_preview": job.get("transcription_preview", ""),
        "usage": job.get("usage", {}),
        "processing_times": job.get("processing_times", {}),
    }


@app.get("/api/transcription/{job_id}")
async def get_transcription(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job non trouvé")
    job = jobs[job_id]
    trans_path = job.get("transcription_path")
    if not trans_path or not os.path.exists(trans_path):
        raise HTTPException(400, "Transcription pas encore disponible")
    with open(trans_path, "r", encoding="utf-8") as f:
        return {"transcription": f.read()}


@app.get("/api/download/{job_id}")
async def download_markdown(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job non trouvé")
    job = jobs[job_id]
    synth_path = job.get("synthesis_path")
    if not synth_path or not os.path.exists(synth_path):
        raise HTTPException(400, "Synthèse pas encore disponible")
    prefix = get_program(job.get("program")).short
    return FileResponse(synth_path, filename=f"{prefix}_{job['month']}_{job['year']}.md")


@app.get("/api/download-transcription/{job_id}")
async def download_transcription_file(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job non trouvé")
    job = jobs[job_id]
    trans_path = job.get("transcription_path")
    if not trans_path or not os.path.exists(trans_path):
        raise HTTPException(400, "Transcription pas encore disponible")
    prefix = get_program(job.get("program")).short
    return FileResponse(
        path=trans_path,
        filename=f"{prefix}_{job['month']}_{job['year']}_transcription.txt",
        media_type="text/plain; charset=utf-8",
    )


@app.get("/api/jobs")
async def list_jobs(program: str = ""):
    """Liste les jobs, optionnellement filtrés par programme (?program=cpc)."""
    values = list(jobs.values())
    if program:
        values = [j for j in values if j.get("program") == program]
    return values


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """Retire un job de la mémoire et supprime ses fichiers de sortie."""
    if job_id not in jobs:
        raise HTTPException(404, "Job non trouvé")
    job = jobs.pop(job_id)
    for key in ("synthesis_path", "transcription_path"):
        p = job.get(key)
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    return {"deleted": job_id}


# --- Pipeline asynchrone ---

async def run_pipeline(job_id: str):
    """Pipeline complet : extraction → transcription → synthèse."""
    job = jobs[job_id]
    program = get_program(job.get("program"))
    out_dir = program_output_dir(program.id)

    try:
        # === ÉTAPE 1 : Extraction audio ===
        job["status"] = "processing"
        job["step"] = "extraction"
        job["progress"] = 10

        from pipeline.audio import extract_audio, get_audio_duration

        audio_path = await asyncio.to_thread(extract_audio, job["video_path"], str(UPLOADS_DIR))
        duration = await asyncio.to_thread(get_audio_duration, audio_path)

        job["audio_path"] = audio_path
        job["audio_duration_min"] = round(duration, 1)
        job["progress"] = 25

        # === ÉTAPE 2 : Transcription ===
        job["step"] = "transcription"
        job["progress"] = 30
        job["transcription_percent"] = 0
        job["elapsed_seconds"] = 0
        job["eta_seconds"] = 0

        from pipeline.transcriber import transcribe_audio, save_transcription

        def on_transcription_progress(percent, elapsed, eta):
            job["transcription_percent"] = percent
            job["elapsed_seconds"] = elapsed
            job["eta_seconds"] = eta
            job["progress"] = 30 + int(percent * 0.3)

        whisper_model = os.getenv("WHISPER_MODEL", "small")
        transcription = await asyncio.to_thread(
            transcribe_audio, audio_path, whisper_model, on_transcription_progress
        )

        trans_path = out_dir / f"{job_id}_transcription.txt"
        await asyncio.to_thread(save_transcription, transcription, str(trans_path))

        job["transcription_path"] = str(trans_path)
        job["transcription_preview"] = transcription["full_text"][:2000]
        job["progress"] = 60
        job["processing_times"] = {
            "transcription_seconds": transcription["processing_time_seconds"]
        }

        # === ÉTAPE 3 : Synthèse IA ===
        job["step"] = "synthesis"
        job["progress"] = 65

        from pipeline.synthesizer import synthesize, save_synthesis

        synthesis_data = await asyncio.to_thread(
            synthesize, transcription["full_text"], job["month"], job["year"], program
        )

        synth_path = out_dir / f"{job_id}_synthese.md"
        await asyncio.to_thread(save_synthesis, synthesis_data, str(synth_path))

        job["synthesis"] = synthesis_data["synthesis"]
        job["synthesis_path"] = str(synth_path)
        job["usage"] = synthesis_data["usage"]
        job["cost_usd"] = round(synthesis_data["usage"].get("estimated_cost_usd", 0), 4)
        job["processing_times"]["synthesis_seconds"] = synthesis_data["processing_time_seconds"]

        # === TERMINÉ ===
        job["step"] = "completed"
        job["status"] = "completed"
        job["progress"] = 100
        job["completed_at"] = datetime.now().isoformat()
        logger.info(f"[JOB {job_id}] {program.id} — terminé avec succès")

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        logger.error(f"[JOB {job_id}] ERREUR : {e}")
        logger.error(traceback.format_exc())

    finally:
        # Nettoyer audio + vidéo temporaires (les synthèses, elles, persistent)
        for path in (job.get("audio_path"), job.get("video_path")):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


# --- Lancement ---
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    print(f"\n🚀 Dossier Synthesizer démarré sur http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)

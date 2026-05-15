"""Module 1 : Extraction audio depuis les replays StreamYard."""
import subprocess
import os
from pathlib import Path


def extract_audio(video_path: str, output_dir: str = "uploads") -> str:
    """
    Extrait la piste audio d'une vidéo en WAV 16kHz mono (optimal pour Whisper).

    Args:
        video_path: Chemin vers le fichier vidéo (MP4, WebM)
        output_dir: Dossier de sortie pour le fichier audio

    Returns:
        Chemin vers le fichier WAV extrait
    """
    video_name = Path(video_path).stem
    audio_path = os.path.join(output_dir, f"{video_name}.wav")

    cmd = [
        "/opt/homebrew/bin/ffmpeg", "-i", video_path,
        "-vn",                    # Pas de vidéo
        "-acodec", "pcm_s16le",   # PCM 16-bit
        "-ar", "16000",           # 16kHz (optimal Whisper)
        "-ac", "1",               # Mono
        "-y",                     # Écraser si existe
        audio_path
    ]

    print(f"[AUDIO] Extraction en cours : {video_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Erreur FFmpeg : {result.stderr}")

    size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"[AUDIO] Extraction terminée : {audio_path} ({size_mb:.0f} MB)")
    return audio_path


def get_audio_duration(audio_path: str) -> float:
    """Retourne la durée en minutes d'un fichier audio."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", audio_path
    ]
    import json
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"]) / 60

#!/usr/bin/env python3
"""
Dossier Synthesizer — Lancement rapide.

Usage:
    python run.py

L'application démarre sur http://localhost:$PORT (8000 par défaut).
"""
import subprocess
import sys
import os


def main():
    try:
        import fastapi  # noqa: F401
        import anthropic  # noqa: F401
        import faster_whisper  # noqa: F401
    except ImportError:
        print("📦 Installation des dépendances...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    if subprocess.run(["ffmpeg", "-version"], capture_output=True).returncode != 0:
        print("❌ FFmpeg n'est pas installé.")
        print("   macOS : brew install ffmpeg")
        print("   Ubuntu : sudo apt install ffmpeg")
        sys.exit(1)

    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("⚠️  Fichier .env manquant. Copiez .env.example vers .env et ajoutez votre clé API.")
            print("   cp .env.example .env")
            sys.exit(1)

    from dotenv import load_dotenv
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-ant-xxx"):
        print("⚠️  Clé API Anthropic manquante ou invalide dans .env")
        sys.exit(1)

    port = os.getenv("PORT", "8000")
    print("\n🚀 Dossier Synthesizer")
    print("=" * 40)
    print(f"   URL : http://localhost:{port}")
    print(f"   Modèle Whisper : {os.getenv('WHISPER_MODEL', 'small')}")
    print(f"   Modèle Claude  : {os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-6')}")
    print("=" * 40)
    print()

    os.chdir(os.path.join(os.path.dirname(__file__), "app"))
    subprocess.run([
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0", "--port", str(port), "--reload",
    ])


if __name__ == "__main__":
    main()

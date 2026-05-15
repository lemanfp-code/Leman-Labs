"""Module 2 : Transcription audio via faster-whisper (local, gratuit)."""
import time
from pathlib import Path


# Glossaire crypto pour post-correction
CRYPTO_GLOSSARY = {
    "bit coin": "Bitcoin",
    "bit coins": "Bitcoin",
    "bite coin": "Bitcoin",
    "etherium": "Ethereum",
    "éthérium": "Ethereum",
    "ethereum": "Ethereum",
    "de fi": "DeFi",
    "défi": "DeFi",
    "d fi": "DeFi",
    "block chain": "blockchain",
    "bloc chain": "blockchain",
    "staking": "staking",
    "stéking": "staking",
    "all coin": "altcoin",
    "alt coin": "altcoin",
    "halving": "halving",
    "having": "halving",
    "holding": "holding",
    "hodl": "HODL",
    "nft": "NFT",
    "n f t": "NFT",
    "solana": "Solana",
    "cardano": "Cardano",
    "polkadot": "Polkadot",
    "avalanche": "Avalanche",
    "chain link": "Chainlink",
    "uniswap": "Uniswap",
    "aave": "Aave",
    "binance": "Binance",
    "coinbase": "Coinbase",
    "etf": "ETF",
    "e t f": "ETF",
    "bull run": "bull run",
    "bear market": "bear market",
    "market cap": "market cap",
    "deep seek": "DeepSeek",
    "open ai": "OpenAI",
    "layer 2": "Layer 2",
    "layer 1": "Layer 1",
    "proof of stake": "Proof of Stake",
    "proof of work": "Proof of Work",
    "yield farming": "yield farming",
    "liquidity pool": "liquidity pool",
    "token omics": "tokenomics",
    "tokenomique": "tokenomics",
    "white paper": "whitepaper",
    "smart contract": "smart contract",
}


def correct_crypto_terms(text: str) -> str:
    """Corrige les termes crypto mal reconnus par Whisper."""
    corrected = text
    for wrong, right in CRYPTO_GLOSSARY.items():
        # Remplacement insensible à la casse
        import re
        pattern = re.compile(re.escape(wrong), re.IGNORECASE)
        corrected = pattern.sub(right, corrected)
    return corrected


def transcribe_audio(audio_path: str, model_size: str = "small", progress_callback=None) -> dict:
    """
    Transcrit un fichier audio en texte avec horodatage.

    Args:
        audio_path: Chemin vers le fichier WAV
        model_size: Taille du modèle Whisper (base, small, medium, large-v3)
        progress_callback: Fonction(percent, elapsed, eta_seconds) appelée pendant la transcription

    Returns:
        Dict avec 'full_text', 'segments', 'duration', 'processing_time'
    """
    from faster_whisper import WhisperModel

    print(f"[TRANSCRIPTION] Chargement du modèle '{model_size}'...")
    start = time.time()

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    load_time = time.time() - start
    print(f"[TRANSCRIPTION] Modèle chargé en {load_time:.1f}s")

    print(f"[TRANSCRIPTION] Transcription en cours : {audio_path}")
    segments_gen, info = model.transcribe(
        audio_path,
        language="fr",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            speech_pad_ms=300
        )
    )

    total_duration = info.duration
    segments = []
    full_text_parts = []

    for segment in segments_gen:
        text = correct_crypto_terms(segment.text.strip())
        segments.append({
            "start": round(segment.start, 1),
            "end": round(segment.end, 1),
            "text": text
        })
        full_text_parts.append(text)

        # Mise à jour de la progression
        if progress_callback and total_duration > 0:
            percent = min(99, (segment.end / total_duration) * 100)
            elapsed = time.time() - start
            if percent > 0:
                eta = elapsed * (100 - percent) / percent
            else:
                eta = 0
            progress_callback(round(percent, 1), round(elapsed), round(eta))

    processing_time = time.time() - start
    full_text = " ".join(full_text_parts)

    if progress_callback:
        progress_callback(100, round(processing_time), 0)

    print(f"[TRANSCRIPTION] Terminée en {processing_time:.0f}s")
    print(f"[TRANSCRIPTION] {len(segments)} segments, {len(full_text)} caractères")

    return {
        "full_text": full_text,
        "segments": segments,
        "duration_minutes": info.duration / 60,
        "processing_time_seconds": processing_time,
        "language": info.language,
        "language_probability": info.language_probability
    }


def save_transcription(transcription: dict, output_path: str):
    """Sauvegarde la transcription en fichier texte."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Transcription\n")
        f.write(f"# Durée : {transcription['duration_minutes']:.0f} min\n")
        f.write(f"# Langue : {transcription['language']} ({transcription['language_probability']:.0%})\n")
        f.write(f"# Temps de traitement : {transcription['processing_time_seconds']:.0f}s\n\n")

        for seg in transcription["segments"]:
            minutes = int(seg["start"] // 60)
            seconds = int(seg["start"] % 60)
            f.write(f"[{minutes:02d}:{seconds:02d}] {seg['text']}\n")

    print(f"[TRANSCRIPTION] Sauvegardée : {output_path}")

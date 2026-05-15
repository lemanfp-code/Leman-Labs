"""Module 3 : Synthèse via API Anthropic Claude — le cœur de l'outil.

Le prompt système et le nom du webinaire proviennent du *programme*
choisi (voir app/programs). Le transcript est envoyé en message
utilisateur. Calcule le coût estimé en USD selon le modèle utilisé.
"""

import os
import time
from pathlib import Path

from anthropic import Anthropic

from programs import Program, get_program

# Tarifs par 1M tokens (USD) — source console.anthropic.com
PRICING = {
    "claude-opus-4-6":      {"input": 15.00, "output": 75.00},
    "claude-opus-4-5":      {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6":    {"input": 3.00,  "output": 15.00},
    "claude-sonnet-4-5":    {"input": 3.00,  "output": 15.00},
    "claude-haiku-4-5":     {"input": 1.00,  "output": 5.00},
    # Fallback raisonnable
    "_default":             {"input": 3.00,  "output": 15.00},
}


def load_system_prompt(program: Program) -> str:
    path = program.prompt_path
    if not path.exists():
        raise RuntimeError(f"Prompt système introuvable : {path}")
    return path.read_text(encoding="utf-8")


def synthesize(
    transcription_text: str,
    month: str = "",
    year: str = "",
    program: Program | str | None = None,
) -> dict:
    if not isinstance(program, Program):
        program = get_program(program)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY manquant dans .env")

    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "16000"))

    system_prompt = load_system_prompt(program)
    speakers = " / ".join(program.speakers) if program.speakers else "tels que prononcés"

    user_message = f"""Voici la transcription complète du webinaire {program.webinar_name} de {month} {year}.

Transformez cette transcription en un dossier {program.short} complet en suivant rigoureusement les instructions du prompt système.

Règles de fidélité strictes :
- N'invente JAMAIS un chiffre, un ticker, un nom propre, une date, un niveau de prix qui ne soit pas dans le transcript.
- Si une information attendue est absente, écris "Non évoqué dans ce webinaire" plutôt que d'extrapoler.
- Garde les noms exacts des intervenants tels que prononcés ({speakers}).
- Tickers + ISIN obligatoires pour toute action recommandée.
- Zones d'achat exactes (en gras) pour toute crypto/action recommandée.
- Plateformes : Saxo / Degiro pour actions ; SwissBorg / Kraken pour cryptos.

---
TRANSCRIPTION :

{transcription_text}

---
Produisez maintenant le dossier {program.short} complet au format Markdown."""

    print(f"[SYNTHÈSE] Programme : {program.name} ({program.id})")
    print(f"[SYNTHÈSE] Modèle : {model}")
    print(f"[SYNTHÈSE] Transcription : {len(transcription_text)} caractères")

    client = Anthropic(api_key=api_key)
    start = time.time()
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    elapsed = time.time() - start

    synthesis = "".join(block.text for block in msg.content if hasattr(block, "text"))

    pricing = PRICING.get(model, PRICING["_default"])
    cost = (
        msg.usage.input_tokens * pricing["input"] / 1_000_000
        + msg.usage.output_tokens * pricing["output"] / 1_000_000
    )

    print(f"[SYNTHÈSE] Terminée en {elapsed:.0f}s — coût ≈ ${cost:.4f}")
    return {
        "synthesis": synthesis.strip(),
        "usage": {
            "input_tokens": msg.usage.input_tokens,
            "output_tokens": msg.usage.output_tokens,
            "estimated_cost_usd": cost,
        },
        "processing_time_seconds": elapsed,
        "model": model,
        "program": program.id,
    }


def save_synthesis(data: dict, output_path: str):
    Path(output_path).write_text(data["synthesis"], encoding="utf-8")
    print(f"[SYNTHÈSE] Sauvegardée : {output_path}")

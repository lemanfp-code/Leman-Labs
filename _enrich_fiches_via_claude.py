"""Enrichit le cache clement.json en passant par le CLI Claude Code (abonnement),
PAS par l'API Anthropic métered. Aucune clé ANTHROPIC_API_KEY requise — c'est ton
abonnement Claude Code qui couvre les appels.

Trade-off : ~5 s/société (vs ~1 s en API directe). Pour 542 sociétés ≈ 45 min.

Usage:
  python3 _enrich_fiches_via_claude.py --limit 5   # test sur 5 sociétés
  python3 _enrich_fiches_via_claude.py             # toutes les manquantes
  python3 _enrich_fiches_via_claude.py --redo      # régénère même si déjà présent
"""

import argparse
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CACHE = Path("outputs/_cache/clement.json")

SYSTEM = """Tu génères des fiches d'analyse boursière en français pour le « Screener de Clément », outil de Clément Brilland (clementbrilland.com).
Style : sobre, financier, factuel. Phrases courtes et denses. Aucune speculation, aucun chiffre inventé.
Tu réponds UNIQUEMENT par un JSON valide avec ces 5 clés exactes (chacune = 1 paragraphe de 2-3 phrases, 250-400 caractères) :
- "activite" : ce que fait concrètement la société (produits/services, marchés clés, positionnement)
- "contexte" : situation actuelle (croissance, marges, transition stratégique éventuelle)
- "chiffres_decodes" : ce que disent les ratios clés (P/E vs croissance, marge vs secteur, dette vs cash-flow)
- "catalyseurs" : 2-3 leviers positifs identifiables à 12-24 mois (M&A, nouveau produit, cycle sectoriel…)
- "particulier" : angle d'investissement pour un particulier (verdict synthétique en 3-4 lignes)

Pas de markdown. Pas de bullet points dans les valeurs. Pas de « selon Yahoo », « selon les données » — sois assertif.
Cite uniquement les chiffres réels présents dans les données ; n'invente jamais."""

SCHEMA = {
    "type": "object",
    "properties": {
        "activite":         {"type": "string"},
        "contexte":         {"type": "string"},
        "chiffres_decodes": {"type": "string"},
        "catalyseurs":      {"type": "string"},
        "particulier":      {"type": "string"},
    },
    "required": ["activite", "contexte", "chiffres_decodes", "catalyseurs", "particulier"],
    "additionalProperties": False,
}


def build_user(c):
    parts = [
        f"Société : {c['name']}",
        f"Pays : {c['ctry']} · Secteur : {c['sec']}" + (f" / {c['industry']}" if c.get('industry') else ""),
        f"Capitalisation : {c['mcap']} Md€" if c.get('mcap') else "",
    ]
    if c.get('descr'):
        parts.append(f"Description (Yahoo) : {c['descr']}")
    fin = c.get("is_financial")
    fy = c.get('fy')
    fy_str = f" ({fy[0]}→{fy[1]})" if fy else ""
    parts.append(f"Chiffre d'affaires{fy_str} : {c['rev'][0]} → {c['rev'][1]} Md€")
    if not fin and c['eb'][1] is not None:
        parts.append(f"EBITDA : {c['eb'][0]} → {c['eb'][1]} Md€" + (f" (marge {c['eb_margin']}%)" if c.get('eb_margin') else ""))
    parts.append(f"Résultat net : {c['ni'][0]} → {c['ni'][1]} Md€")
    parts.append(f"Dividende/action : {c['div'][0]} → {c['div'][1]} (rendement {c.get('yield', 0)}%)")
    if c.get('pe'):
        parts.append(f"P/E : {c['pe']}×")
    if c.get('roe') is not None:
        parts.append(f"ROE : {c['roe']}%")
    if not fin and c.get('nd') is not None:
        parts.append(f"Dette nette/EBITDA : {c['nd']}×" if c['nd'] > 0 else f"Trésorerie nette positive ({c['nd']}× EBITDA)")
    parts.append(f"Cours (~5 ans) : {c['p'][0]} → {c['p'][1]}")
    return "\n".join(p for p in parts if p)


def enrich_one(c):
    """Appelle `claude -p` avec un schéma JSON pour générer la fiche."""
    user = build_user(c)
    full_prompt = SYSTEM + "\n\n---\n\n" + user
    env = dict(os.environ)
    # Force l'utilisation de l'abonnement, pas de l'API
    env.pop("ANTHROPIC_API_KEY", None)
    try:
        proc = subprocess.run(
            [
                "claude", "-p", full_prompt,
                "--output-format", "json",
                "--json-schema", json.dumps(SCHEMA),
                "--no-session-persistence",
            ],
            env=env,
            capture_output=True, text=True, timeout=120,
        )
        if proc.returncode != 0:
            return None, f"claude exit {proc.returncode}: {proc.stderr.strip()[:160]}"
        if not proc.stdout.strip():
            return None, f"stdout vide (stderr: {proc.stderr.strip()[:160]})"
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            return None, f"envelope non-JSON: {proc.stdout[:160]!r}"
        if envelope.get("is_error"):
            return None, envelope.get("result", "unknown error")[:160]
        result_str = envelope.get("result", "")
        # Le résultat peut être encadré de ```json ... ```
        if "```" in result_str:
            result_str = result_str.split("```")[1]
            if result_str.lower().startswith("json"):
                result_str = result_str[4:]
            result_str = result_str.strip().rstrip("`").strip()
        fiche = json.loads(result_str)
        keys = ["activite", "contexte", "chiffres_decodes", "catalyseurs", "particulier"]
        return {f"fiche_{k}": fiche.get(k) for k in keys}, None
    except subprocess.TimeoutExpired:
        return None, "timeout 120s"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:160]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3,
                    help="Parallélisme — garder bas (claude CLI consomme du quota)")
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()

    if subprocess.run(["which", "claude"], capture_output=True).returncode != 0:
        print("ERREUR : `claude` CLI introuvable. Installe Claude Code d'abord.")
        return

    cache = json.loads(CACHE.read_text())
    cos = cache["companies"]
    todo = [c for c in cos if args.redo or not c.get("fiche_activite")]
    if args.limit:
        todo = todo[:args.limit]
    print(f"À enrichir : {len(todo)} / {len(cos)} sociétés via abonnement Claude Code ({args.workers} workers)")

    t0 = time.time()
    ok = ko = 0
    key_to_co = {(c["tk"], c["ctry"]): c for c in cos}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(enrich_one, c): c for c in todo}
        for i, f in enumerate(as_completed(futs)):
            c = futs[f]
            out, err = f.result()
            if out is None:
                ko += 1
                if ko <= 5:
                    print(f"  ✗ {c['name']:24s} : {err}")
                continue
            key_to_co[(c["tk"], c["ctry"])].update(out)
            ok += 1
            if (i + 1) % 10 == 0:
                CACHE.write_text(json.dumps(cache, ensure_ascii=False, allow_nan=False))
                print(f"  · {i+1}/{len(todo)} traitées ({ok} ok, {ko} ko)")

    CACHE.write_text(json.dumps(cache, ensure_ascii=False, allow_nan=False))
    elapsed = time.time() - t0
    print(f"\nFiches : {ok} ok · {ko} ko · en {elapsed:.0f}s")
    print("Aucun débit API — passé via ton abonnement Claude Code.")


if __name__ == "__main__":
    main()

"""Enrichit le cache clement.json avec 5 sections « fiche société » en français
générées par Claude Haiku (style LDT) : activité, contexte, chiffres décodés,
catalyseurs, particulier. Skip si déjà présent (idempotent).

Usage:
  python3 _enrich_fiches.py --limit 10       # test sur 10 sociétés
  python3 _enrich_fiches.py                  # toutes
"""

import argparse
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()
CACHE = Path("outputs/_cache/clement.json")
MODEL = "claude-haiku-4-5-20251001"

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


def build_user(c):
    parts = [
        f"Société : {c['name']}",
        f"Pays : {c['ctry']} · Secteur : {c['sec']}" + (f" / {c['industry']}" if c.get('industry') else ""),
        f"Capitalisation : {c['mcap']} Md€" if c.get('mcap') else "",
    ]
    if c.get('descr'):
        parts.append(f"Description (Yahoo) : {c['descr']}")
    # Données financières
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


def enrich_one(client, c):
    user = build_user(c)
    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=900,
            system=SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        txt = resp.content[0].text.strip()
        # Nettoie un éventuel ```json … ```
        if txt.startswith("```"):
            txt = txt.split("```")[1]
            if txt.lower().startswith("json"):
                txt = txt[4:]
            txt = txt.strip().rstrip("`").strip()
        fiche = json.loads(txt)
        # Garde uniquement les clés attendues
        keys = ["activite", "contexte", "chiffres_decodes", "catalyseurs", "particulier"]
        return {f"fiche_{k}": fiche.get(k) for k in keys}, None, resp.usage
    except Exception as e:
        return None, str(e)[:120], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Nb société max (0 = toutes)")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--redo", action="store_true", help="Régénère même si déjà présent")
    args = ap.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERREUR : ANTHROPIC_API_KEY absent dans l'environnement.")
        return
    client = anthropic.Anthropic()

    cache = json.loads(CACHE.read_text())
    cos = cache["companies"]
    todo = [c for c in cos if args.redo or not c.get("fiche_activite")]
    if args.limit:
        todo = todo[:args.limit]
    print(f"À enrichir : {len(todo)} / {len(cos)} sociétés (model {MODEL}, {args.workers} workers)")

    t0 = time.time()
    in_tok = out_tok = ok = ko = 0
    # Clé unique : ticker + pays (les tickers courts comme SAN/BOL/UNI
    # entrent en collision entre plusieurs places européennes)
    key_to_co = {(c["tk"], c["ctry"]): c for c in cos}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(enrich_one, client, c): c for c in todo}
        for i, f in enumerate(as_completed(futs)):
            c = futs[f]
            out, err, usage = f.result()
            if out is None:
                ko += 1
                if ko <= 5:
                    print(f"  ✗ {c['name']:20s} : {err}")
                continue
            key_to_co[(c["tk"], c["ctry"])].update(out)
            if usage:
                in_tok += usage.input_tokens
                out_tok += usage.output_tokens
            ok += 1
            if (i + 1) % 20 == 0:
                # Sauvegarde intermédiaire
                CACHE.write_text(json.dumps(cache, ensure_ascii=False))

    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    elapsed = time.time() - t0
    # Coût Haiku 4.5 : $1/M input, $5/M output
    cost = in_tok / 1e6 * 1.0 + out_tok / 1e6 * 5.0
    print(f"\nFiches : {ok} ok · {ko} ko · en {elapsed:.0f}s")
    print(f"Tokens : {in_tok:,} in + {out_tok:,} out · coût estimé : ${cost:.3f}")


if __name__ == "__main__":
    main()

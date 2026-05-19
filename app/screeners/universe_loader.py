"""Univers réel & complet : constituants du Stoxx Europe 600 récupérés
depuis les holdings publics de l'ETF iShares STOXX Europe 600, mappés en
tickers Yahoo Finance, en union avec la liste curatée (filet de sécurité,
notamment pour les tickers Yahoo « délicats » du SMI).

- Source : iShares (CSV holdings publics, ~603 actions).
- Repli : la liste curatée `clement_universe.TICKERS` si la source est
  indisponible.
- Cache disque (7 j) pour ne pas re-télécharger à chaque build.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

from .clement_universe import TICKERS as CURATED

logger = logging.getLogger("dossier-synthesizer")

CACHE = Path(__file__).resolve().parent.parent.parent / "outputs" / "_cache" / "universe.json"
TTL_SECONDS = 7 * 24 * 3600

# iShares STOXX Europe 600 UCITS ETF (DE) — holdings CSV publics.
ISHARES_URLS = [
    "https://www.ishares.com/ch/individual/en/products/251931/ishares-stoxx-europe-600-ucits-etf-de-fund/1495092304805.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
    "https://www.ishares.com/uk/individual/en/products/251931/ishares-stoxx-europe-600-ucits-etf-de-fund/1506575576011.ajax?fileType=csv&fileName=EXSA_holdings&dataType=fund",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Place de cotation → suffixe Yahoo (recherche par sous-chaîne, minuscules)
_EXCH = [
    ("london", ".L"), ("euronext paris", ".PA"), ("paris", ".PA"),
    ("xetra", ".DE"), ("deutsche börse", ".DE"), ("frankfurt", ".DE"),
    ("six swiss", ".SW"), ("swiss exchange", ".SW"),
    ("borsa italiana", ".MI"), ("italiana", ".MI"),
    ("amsterdam", ".AS"), ("madrid", ".MC"),
    ("copenhagen", ".CO"), ("oslo", ".OL"), ("helsinki", ".HE"),
    ("brussels", ".BR"), ("warsaw", ".WA"), ("wiener", ".VI"),
    ("vienna", ".VI"), ("irish", ".IR"), ("lisbon", ".LS"),
    ("stockholm", ".ST"),
]
# Nordic « Nasdaq Omx Nordic » générique → désambiguïsé par le pays
_LOC_SUFFIX = {
    "sweden": ".ST", "finland": ".HE", "denmark": ".CO", "norway": ".OL",
    "united kingdom": ".L", "france": ".PA", "germany": ".DE",
    "switzerland": ".SW", "netherlands": ".AS", "italy": ".MI",
    "spain": ".MC", "belgium": ".BR", "poland": ".WA", "austria": ".VI",
    "ireland": ".IR", "portugal": ".LS",
}
_LOC_CODE = {
    "united kingdom": "GB", "france": "FR", "germany": "DE",
    "switzerland": "CH", "netherlands": "NL", "italy": "IT", "spain": "ES",
    "sweden": "SE", "denmark": "DK", "norway": "NO", "finland": "FI",
    "belgium": "BE", "poland": "PL", "austria": "AT", "ireland": "IE",
    "portugal": "PT", "luxembourg": "LU",
}
# Secteur ICB STOXX (anglais) → libellé court FR
_SECT = [
    ("health", "Santé"), ("pharma", "Santé"),
    ("bank", "Finance"), ("financial serv", "Finance"),
    ("financial", "Finance"), ("invest", "Finance"),
    ("insurance", "Assurance"),
    ("technolog", "Tech"), ("software", "Tech"),
    ("telecom", "Télécom"), ("communication", "Télécom"),
    ("food", "Conso. déf."), ("beverage", "Conso. déf."),
    ("personal care", "Conso. déf."), ("tobacco", "Conso. déf."),
    ("household", "Conso. déf."), ("grocery", "Conso. déf."),
    ("consumer staples", "Conso. déf."), ("consumer discretionary", "Conso. cycl."),
    ("retail", "Conso. cycl."), ("travel", "Conso. cycl."),
    ("leisure", "Conso. cycl."), ("automobil", "Conso. cycl."),
    ("consumer products", "Conso. cycl."), ("media", "Conso. cycl."),
    ("energy", "Énergie"), ("oil", "Énergie"),
    ("basic resource", "Matériaux"), ("chemical", "Matériaux"),
    ("construction", "Matériaux"), ("material", "Matériaux"),
    ("industrial", "Industrie"), ("aerospace", "Industrie"),
    ("utilit", "Utilities"), ("real estate", "Immobilier"),
]


def _suffix(exchange: str, location: str) -> str | None:
    e = (exchange or "").lower()
    for key, suf in _EXCH:
        if key in e:
            return suf
    return _LOC_SUFFIX.get((location or "").lower())


def _sector_fr(s: str) -> str:
    t = (s or "").lower()
    for key, fr in _SECT:
        if key in t:
            return fr
    return (s or "Divers").title()


def _yahoo_ticker(raw: str, suffix: str) -> str | None:
    t = (raw or "").strip().upper().rstrip(".")
    if not t or t in ("CASH", "USD", "EUR", "GBP"):
        return None
    t = t.replace(" ", "-").replace(".", "-").replace("/", "-")
    return t + suffix


def _parse_csv(text: str):
    lines = text.splitlines()
    hi = next((i for i, l in enumerate(lines)
               if "Ticker" in l and "Name" in l and "Exchange" in l), None)
    if hi is None:
        return []
    rdr = csv.reader(lines[hi:])
    hdr = [h.strip() for h in next(rdr)]
    col = {name: hdr.index(name) for name in hdr}
    out = []
    for r in rdr:
        if not r or len(r) < len(hdr):
            continue
        if "Asset Class" in col and not r[col["Asset Class"]].strip().lower().startswith("equity"):
            continue
        raw_tk = r[col["Ticker"]].strip()
        name = r[col["Name"]].strip().title()
        loc = r[col.get("Location", -1)].strip() if "Location" in col else ""
        exch = r[col.get("Exchange", -1)].strip() if "Exchange" in col else ""
        sect = r[col.get("Sector", -1)].strip() if "Sector" in col else ""
        suf = _suffix(exch, loc)
        if not suf:
            continue
        sym = _yahoo_ticker(raw_tk, suf)
        if not sym:
            continue
        out.append((sym, name, _LOC_CODE.get(loc.lower(), loc[:2].upper()), _sector_fr(sect)))
    return out


def _fetch_remote():
    import requests
    for u in ISHARES_URLS:
        try:
            r = requests.get(u, headers=HEADERS, timeout=30)
            if r.status_code == 200 and len(r.text) > 5000:
                rows = _parse_csv(r.text)
                if len(rows) >= 300:
                    return rows
        except Exception as e:
            logger.warning(f"[UNIVERSE] source KO ({u[:50]}…): {e}")
    return []


def load_universe(force: bool = False):
    """Liste (ticker, nom, pays, secteur) — Stoxx 600 réel ∪ liste curatée.
    Cache 7 j ; repli sur la liste curatée si la source échoue."""
    if not force and CACHE.exists():
        try:
            data = json.loads(CACHE.read_text(encoding="utf-8"))
            age = (datetime.now() - datetime.fromisoformat(data["as_of"])).total_seconds()
            if age < TTL_SECONDS and data.get("tickers"):
                return [tuple(x) for x in data["tickers"]]
        except (OSError, ValueError):
            pass

    remote = _fetch_remote()
    merged, seen = [], set()
    for row in list(CURATED) + remote:   # curatée d'abord (tickers SMI fiables)
        sym = row[0]
        if sym in seen:
            continue
        seen.add(sym)
        merged.append(tuple(row))

    if remote:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(
            {"as_of": datetime.now().isoformat(timespec="seconds"),
             "count": len(merged), "from_index": len(remote),
             "tickers": merged}, ensure_ascii=False), encoding="utf-8")
        logger.info(f"[UNIVERSE] {len(merged)} valeurs ({len(remote)} via Stoxx 600 + {len(merged)-len(remote)} curatées/uniques)")
    else:
        logger.warning(f"[UNIVERSE] source indisponible — repli liste curatée ({len(merged)})")
    return merged

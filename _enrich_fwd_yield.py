"""Ajoute le rendement forward Yahoo (dividendYield = dividendRate/price)
au cache existant et audite toutes les valeurs des 488 sociétés."""
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yfinance as yf

CACHE = Path("outputs/_cache/clement.json")
SNAP = Path("app/static/screener-clement/clement-data.json")
SUFFIX = {"CH": ".SW", "FR": ".PA", "DE": ".DE", "GB": ".L", "IT": ".MI", "NL": ".AS",
          "ES": ".MC", "DK": ".CO", "NO": ".OL", "FI": ".HE", "BE": ".BR", "SE": ".ST",
          "PL": ".WA", "AT": ".VI", "IE": ".IR", "PT": ".LS"}


def fetch(co):
    sym = co["tk"] + SUFFIX.get(co["ctry"], "")
    try:
        info = yf.Ticker(sym).info
        out = {}
        # Yield forward (Yahoo l'expose en % directement)
        dy = info.get("dividendYield")
        if dy is not None:
            try:
                f = float(dy)
                if f == f and 0 < f < 30:
                    out["fwd_yield"] = round(f, 2)
            except Exception:
                pass
        return co["tk"], co["ctry"], out
    except Exception:
        return co["tk"], co["ctry"], {}


def audit(cos):
    """Audit : repère les sociétés avec des données suspectes."""
    issues = []
    for c in cos:
        name = c["name"]
        # Yield aberrant
        if c.get("yield") and c["yield"] > 15:
            issues.append((name, f"rendement {c['yield']}% suspect (>15%)"))
        # P/E aberrant
        if c.get("pe") and c["pe"] > 100:
            issues.append((name, f"P/E {c['pe']}× très élevé"))
        if c.get("fwd_pe") and c["fwd_pe"] > 80:
            issues.append((name, f"P/E forward {c['fwd_pe']}× très élevé"))
        # CA négatif
        if c.get("rev") and c["rev"][1] is not None and c["rev"][1] < 0:
            issues.append((name, "CA dernier exercice négatif"))
        # ROE > 80% (probable mauvaise donnée)
        if c.get("roe") and abs(c["roe"]) > 80:
            issues.append((name, f"ROE {c['roe']}% extrême"))
        # Marge EBITDA aberrante
        if c.get("eb_margin") and (c["eb_margin"] > 80 or c["eb_margin"] < -20):
            issues.append((name, f"marge EBITDA {c['eb_margin']}% inhabituelle"))
        # Capi manquante
        if c.get("mcap") is None:
            issues.append((name, "capitalisation manquante"))
    return issues


def main():
    d = json.loads(CACHE.read_text())
    cos = d["companies"]
    print(f"Enrichissement rendement forward Yahoo sur {len(cos)} sociétés…")
    t0 = time.time()
    key_to_co = {(c["tk"], c["ctry"]): c for c in cos}
    ok = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(fetch, c) for c in cos]
        for f in as_completed(futs):
            tk, ctry, out = f.result()
            co = key_to_co.get((tk, ctry))
            if co is None:
                continue
            if "fwd_yield" in out:
                co["fwd_yield"] = out["fwd_yield"]
                ok += 1
    print(f"  · {ok}/{len(cos)} ont un rendement forward Yahoo")
    print(f"  · durée : {time.time()-t0:.0f}s")

    # Purge NaN/Inf
    for c in cos:
        for k, v in list(c.items()):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                c[k] = None

    # Audit
    issues = audit(cos)
    if issues:
        print(f"\n=== Audit : {len(issues)} anomalies détectées ===")
        for name, msg in issues[:30]:
            print(f"  ⚠️  {name:30s} · {msg}")
        if len(issues) > 30:
            print(f"  … et {len(issues)-30} autres")
    else:
        print("\n✓ Audit OK — aucune valeur aberrante détectée.")

    CACHE.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    SNAP.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    print("\nCache + snapshot sauvegardés.")


if __name__ == "__main__":
    main()

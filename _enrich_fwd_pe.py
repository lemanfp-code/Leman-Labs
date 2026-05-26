"""Ajoute le P/E forward (estimations analystes) au cache existant.
Pas de coût LLM, juste appel Yahoo info pour chaque ticker."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yfinance as yf

CACHE = Path("outputs/_cache/clement.json")
SNAP = Path("app/static/screener-clement/clement-data.json")

# Suffixes Yahoo par pays (déduit du screener)
SUFFIX = {"CH": ".SW", "FR": ".PA", "DE": ".DE", "GB": ".L", "IT": ".MI",
          "NL": ".AS", "ES": ".MC", "DK": ".CO", "NO": ".OL", "FI": ".HE",
          "BE": ".BR", "SE": ".ST", "PL": ".WA", "AT": ".VI", "IE": ".IR",
          "PT": ".LS"}


def fetch_fwd_pe(co):
    sym = co["tk"] + SUFFIX.get(co["ctry"], "")
    try:
        info = yf.Ticker(sym).info
        fpe = info.get("forwardPE")
        if fpe is None:
            return co["tk"], co["ctry"], None
        f = float(fpe)
        if f != f or f <= 0 or f > 200:  # NaN ou aberrant
            return co["tk"], co["ctry"], None
        return co["tk"], co["ctry"], round(f, 1)
    except Exception:
        return co["tk"], co["ctry"], None


def main():
    d = json.loads(CACHE.read_text())
    cos = d["companies"]
    print(f"Enrichissement P/E forward sur {len(cos)} sociétés…")
    t0 = time.time()
    ok = ko = 0
    key_to_co = {(c["tk"], c["ctry"]): c for c in cos}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(fetch_fwd_pe, c) for c in cos]
        for f in as_completed(futs):
            tk, ctry, fpe = f.result()
            co = key_to_co.get((tk, ctry))
            if co is None:
                continue
            co["fwd_pe"] = fpe
            if fpe is not None:
                ok += 1
            else:
                ko += 1
    elapsed = time.time() - t0
    print(f"OK : {ok} avec forward P/E · {ko} sans · en {elapsed:.0f}s")
    # Purge Infinity/NaN par sécurité
    import math
    for c in cos:
        for k, v in list(c.items()):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                c[k] = None
    CACHE.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    SNAP.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    print("Cache + snapshot mis à jour.")


if __name__ == "__main__":
    main()

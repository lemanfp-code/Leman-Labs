"""Re-fetch EBITDA en priorisant Normalized EBITDA (hors exceptionnels)
pour s'aligner avec la pratique analyste (Zonebourse / FactSet)."""
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

# Currencies à convertir en EUR si le rapport est en devise locale
# (yfinance renvoie en devise du rapport ; pour Yahoo les European DRs sont déjà en EUR)
FX_TO_EUR = {"USD": 0.92, "GBP": 1.17, "CHF": 1.03, "SEK": 0.087, "NOK": 0.085,
             "DKK": 0.134, "PLN": 0.23, "GBp": 0.0117}


def series_first_last(ist, *names):
    """Retourne [valeur la plus ancienne, valeur la plus récente] en Md€."""
    for nm in names:
        if nm in ist.index:
            s = ist.loc[nm].dropna()
            if len(s) >= 2:
                vals = list(s.values)
                # ist.columns est trié décroissant chez yfinance (récent → vieux)
                return float(vals[-1]) / 1e9, float(vals[0]) / 1e9
            if len(s) == 1:
                return None, float(s.iloc[0]) / 1e9
    return None, None


def fetch(co):
    sym = co["tk"] + SUFFIX.get(co["ctry"], "")
    try:
        t = yf.Ticker(sym)
        ist = t.income_stmt
        if ist is None or ist.empty:
            return co, None, "no income statement"
        first, last = series_first_last(ist, "Normalized EBITDA", "EBITDA")
        if last is None:
            return co, None, "no EBITDA / Normalized EBITDA"
        # Vérif cohérence devise via le revenue (déjà en cache)
        cur_rev = co["rev"][1]
        rev_first, rev_last = series_first_last(ist, "Total Revenue")
        if rev_last and cur_rev and abs(rev_last - cur_rev) / abs(cur_rev) > 0.15:
            # devise probablement différente → on skip pour ne pas mélanger
            return co, None, f"mismatch revenue cache {cur_rev:.1f} vs yahoo {rev_last:.1f}"
        return co, (round(first, 2) if first else None, round(last, 2)), None
    except Exception as e:
        return co, None, str(e)[:80]


def main():
    d = json.loads(CACHE.read_text())
    cos = [c for c in d["companies"] if not c.get("is_financial")]
    print(f"Refresh EBITDA (Normalized prioritaire) sur {len(cos)} non-financières…")
    t0 = time.time()
    key_to_co = {(c["tk"], c["ctry"]): c for c in cos}
    ok = ko = unchanged = upgraded = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(fetch, c) for c in cos]
        for f in as_completed(futs):
            co, vals, err = f.result()
            if vals is None:
                ko += 1
                continue
            old = co.get("eb")
            new_first, new_last = vals
            if old and old[1] is not None and new_last is not None:
                delta = abs(new_last - old[1])
                if delta > 0.02:  # > 20 M€ d'écart
                    upgraded += 1
                else:
                    unchanged += 1
            co["eb"] = [new_first, new_last]
            co["eb_raw"] = [new_first, new_last]
            # Recalcule marge EBITDA
            if new_last and co.get("rev") and co["rev"][1]:
                co["eb_margin"] = round(new_last / co["rev"][1] * 100, 1)
            ok += 1
    print(f"  · OK : {ok}/{len(cos)}  · KO : {ko}")
    print(f"  · EBITDA upgraded (delta > 20 M€) : {upgraded}")
    print(f"  · EBITDA inchanged : {unchanged}")
    print(f"  · durée : {time.time()-t0:.0f}s")

    # Purge Inf/NaN
    for c in d["companies"]:
        for k, v in list(c.items()):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                c[k] = None

    CACHE.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    SNAP.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    print("Cache + snapshot sauvegardés.")


if __name__ == "__main__":
    main()

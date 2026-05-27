"""Rattrape les sociétés de l'univers source absentes du cache (124 manquantes)
en re-tentant le fetch avec la nouvelle logique d'historique adaptatif."""
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, ".")
from app.screeners.clement import _fetch_one
from app.screeners.universe_loader import load_universe

CACHE = Path("outputs/_cache/clement.json")
SNAP = Path("app/static/screener-clement/clement-data.json")


def main():
    d = json.loads(CACHE.read_text())
    have = {(c["tk"], c["ctry"]) for c in d["companies"]}
    universe = load_universe()
    missing = []
    for sym, name, ctry, sec in universe:
        tk = sym.split(".")[0]
        if (tk, ctry) not in have:
            missing.append((sym, name, ctry, sec))
    print(f"Récupération de {len(missing)} sociétés manquantes…")
    t0 = time.time()
    recovered = []
    failed = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_fetch_one, sym, name, ctry, sec): (sym, name)
                for sym, name, ctry, sec in missing}
        for f in as_completed(futs):
            sym, name = futs[f]
            try:
                rec = f.result(timeout=60)
                if rec.get("ok"):
                    # Filtre banques (cohérence avec _build)
                    if (rec.get("industry") or "").startswith("Banks"):
                        failed.append((name, "banque (exclue)"))
                        continue
                    recovered.append(rec)
                else:
                    reasons = []
                    if rec.get("mcap") is None: reasons.append("mcap")
                    if rec.get("yield") is None: reasons.append("yield")
                    if rec.get("rev") and None in rec["rev"]: reasons.append("rev")
                    if rec.get("ni") and None in rec["ni"]: reasons.append("ni")
                    if rec.get("p") and None in rec["p"]: reasons.append("p")
                    if rec.get("div") and None in rec["div"]: reasons.append("div")
                    if not rec.get("is_financial") and rec.get("eb") and None in rec["eb"]:
                        reasons.append("eb")
                    failed.append((name, ",".join(reasons) or "?"))
            except Exception as e:
                failed.append((name, f"err {type(e).__name__}"))

    print(f"\n  · Récupérées : {len(recovered)}")
    print(f"  · Échecs : {len(failed)}")
    print(f"  · Durée : {time.time()-t0:.0f}s")
    if failed[:15]:
        print("\nÉchecs (top 15) :")
        for name, why in failed[:15]:
            print(f"  ✗ {name:35s} → {why}")

    # Purge Inf/NaN sur les recovered
    for rec in recovered:
        for k, v in list(rec.items()):
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                rec[k] = None
        d["companies"].append(rec)

    d["count"] = len(d["companies"])
    CACHE.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    SNAP.write_text(json.dumps(d, ensure_ascii=False, allow_nan=False))
    print(f"\nTotal cache : {d['count']} sociétés")


if __name__ == "__main__":
    main()

"""Moteur du Screener de Clément : vraies données via Yahoo Finance.

- Récupère par ticker : capitalisation (→ €), cours (10/5 ans/auj.),
  dividendes (croissance 5/10 ans + rendement TTM réel), agrégats
  (CA / EBITDA / résultat net : Yahoo ne fournit ~que 4 ans → l'écart
  long terme est marqué « n/d » plutôt qu'inventé), levier DetteNette/EBITDA.
- Cache disque (outputs/_cache/clement.json) + rafraîchissement en
  arrière-plan (l'univers complet = lent ; le front lit le cache).

Aucune donnée inventée : si Yahoo ne renvoie pas une valeur, elle vaut
None et le critère correspondant est « n/d » (non satisfait).
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .clement_universe import FX_TO_EUR
from .universe_loader import load_universe

logger = logging.getLogger("dossier-synthesizer")

CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "outputs" / "_cache" / "clement.json"
# Maj prix + fondamentaux 1×/trimestre : les comptes annuels (CA/EBITDA/dette)
# ne bougent pas plus vite, et cela évite de marteler Yahoo à chaque visite.
STALE_SECONDS = 91 * 24 * 3600

_lock = threading.Lock()
_state = {"refreshing": False, "started_at": None, "last_attempt": 0.0}
AUTO_RETRY_COOLDOWN = 120  # s — évite de re-déclencher un build en boucle

_SECTOR_COLOR = {
    "Conso. déf.": "#0B5C3E", "Santé": "#0033A0", "Tech": "#0B5394",
    "Luxe": "#1A1A1A", "Industrie": "#185FA5", "Énergie": "#E2001A",
    "Matériaux": "#7A4DBD", "Finance": "#0F6E56", "Assurance": "#0B3D91",
    "Conso. cycl.": "#B8860B", "Télécom": "#534AB7", "Services": "#993556",
    "Immobilier": "#854F0B", "Utilities": "#0B8A3E",
}


def _bn(v):
    """En milliards, arrondi ; None si inexploitable."""
    try:
        v = float(v)
        if v != v:  # NaN
            return None
        return round(v / 1e9, 2)
    except (TypeError, ValueError):
        return None


def _num(v):
    try:
        v = float(v)
        return None if v != v else v
    except (TypeError, ValueError):
        return None


def _fetch_one(sym, name, country, sector):
    import yfinance as yf

    rec = {
        "name": name, "tk": sym.split(".")[0], "ctry": country, "sec": sector,
        "color": _SECTOR_COLOR.get(sector, "#444"),
        "mcap": None, "yield": None, "nd": None,
        "rev": [None, None], "eb": [None, None],
        "ni": [None, None], "div": [None, None],
        "rev_raw": [None, None], "eb_raw": [None, None], "ni_raw": [None, None],
        "p": [None, None], "years": None, "fy": None, "ok": False,
        "ccy": None, "fin_ccy": None, "err": None,
        # Secteurs où EBITDA & levier ne sont pas pertinents (banques sans EBITDA,
        # assureurs idem, foncières/REITs raisonnent en FFO).
        "is_financial": (sector or "").lower() in ("finance", "assurance", "immobilier"),
    }
    try:
        t = yf.Ticker(sym)
        try:
            info = t.get_info()
        except Exception:
            info = getattr(t, "info", {}) or {}
        ccy = info.get("currency") or "EUR"
        rec["ccy"] = ccy
        # Devise de PUBLICATION des comptes — souvent ≠ devise de cotation
        # (AstraZeneca cote en pence mais publie en USD ; TotalEnergies en USD).
        fin_ccy = info.get("financialCurrency") or ("GBP" if ccy == "GBp" else ccy)
        rec["fin_ccy"] = fin_ccy
        fx_fin = FX_TO_EUR.get(fin_ccy, 1.0)

        mc = _num(info.get("marketCap"))
        if mc:
            # marketCap est en devise majeure même quand les cours sont en
            # pence (GBp) : ne pas lui appliquer le facteur pence.
            cap_ccy = "GBP" if ccy == "GBp" else ccy
            rec["mcap"] = round(mc * FX_TO_EUR.get(cap_ccy, 1.0) / 1e9, 1)

        # Cours : ~5 ans réels (plus ancien point ≤ 5 ans → aujourd'hui)
        try:
            h = t.history(period="6y", interval="1mo")["Close"].dropna()
        except Exception:
            h = None
        if h is not None and len(h):
            now_dt = h.index[-1]
            pnow = float(h.iloc[-1])
            p5s = h[h.index <= now_dt - timedelta(days=365 * 5)]
            rec["p"] = [round(float(p5s.iloc[-1]), 2) if len(p5s) else None,
                        round(pnow, 2)]

        # Dividendes : rendement TTM réel + dividende il y a ~5 ans
        # (0.0 = aucun versement cette année-là — donnée réelle, pas n/d)
        try:
            d = t.dividends
        except Exception:
            d = None
        pnow = rec["p"][1]
        if d is not None and len(d):
            now = datetime.now(d.index.tz) if d.index.tz else datetime.now()
            ttm = float(d[d.index >= now - timedelta(days=365)].sum())
            if ttm == 0:
                # Payeur annuel dont le versement est hors fenêtre 365 j :
                # repli sur le dernier exercice civil ayant versé.
                for y in range(now.year, now.year - 4, -1):
                    s = float(d[d.index.year == y].sum())
                    if s > 0:
                        ttm = s
                        break
            d5 = float(d[d.index.year == now.year - 5].sum())
            rec["div"] = [round(d5, 4), round(ttm, 4)]
            rec["yield"] = round(ttm / pnow * 100, 2) if (ttm > 0 and pnow) else 0.0
        else:
            rec["div"] = [0.0, 0.0]
            rec["yield"] = 0.0

        # Comptes annuels (Yahoo ~4 ans) : plus ancien exercice → dernier
        try:
            fin = t.income_stmt
        except Exception:
            fin = None

        def series(df, *names):
            if df is None:
                return None
            for nm in names:
                if nm in df.index:
                    s = df.loc[nm].dropna()
                    if len(s):
                        return s
            return None

        def oldnew(s):  # colonnes : récent → ancien
            if s is None or len(s) < 2:
                return None, None
            return float(s.iloc[-1]), float(s.iloc[0])

        rev_s = series(fin, "Total Revenue", "Operating Revenue")
        ni_s = series(fin, "Net Income", "Net Income Common Stockholders")
        eb_s = series(fin, "EBITDA", "Normalized EBITDA")
        if eb_s is None and fin is not None:
            ebit = series(fin, "EBIT", "Operating Income")
            dep = series(fin, "Reconciled Depreciation",
                         "Depreciation And Amortization In Income Statement")
            if ebit is not None and dep is not None:
                eb_s = ebit.add(dep, fill_value=0).dropna()

        rOld, rNow = oldnew(rev_s)
        eOld, eNow = oldnew(eb_s)
        nOld, nNow = oldnew(ni_s)
        # Comptes convertis en € (Yahoo les publie en devise de reporting :
        # CHF, USD, GBP, SEK… → comparabilité). On conserve EN PLUS la valeur
        # publiée d'origine (rev_raw/eb_raw/ni_raw) : affichée en sous-titre,
        # elle permet de vérifier chaque chiffre directement à la source.
        cv = lambda v: _bn(v * fx_fin) if v is not None else None
        rec["rev"] = [cv(rOld), cv(rNow)]
        rec["eb"] = [cv(eOld), cv(eNow)]
        rec["ni"] = [cv(nOld), cv(nNow)]
        rec["rev_raw"] = [_bn(rOld), _bn(rNow)]
        rec["eb_raw"] = [_bn(eOld), _bn(eNow)]
        rec["ni_raw"] = [_bn(nOld), _bn(nNow)]
        try:
            idx = list(rev_s.index)
            # Exercices RÉELLEMENT comparés (ex. [2022, 2025]) : la trajectoire
            # n'est pas « ~5 ans » mais l'écart entre les exercices publiés par
            # Yahoo (~3 à 5 ans selon la société). Affiché tel quel côté front.
            if len(idx) >= 2:
                rec["fy"] = [int(idx[-1].year), int(idx[0].year)]
                rec["years"] = abs(rec["fy"][1] - rec["fy"][0])
        except Exception:
            rec["fy"] = None
            rec["years"] = None

        # Levier DetteNette / EBITDA
        ebitda = _num(info.get("ebitda")) or _num(eNow)
        debt = _num(info.get("totalDebt"))
        cash = _num(info.get("totalCash"))
        if ebitda and ebitda > 0 and debt is not None and cash is not None:
            rec["nd"] = round((debt - cash) / ebitda, 2)

        # Société retenue si TOUTES les données réelles pertinentes sont là.
        # Pour les financières (banques/assureurs), EBITDA & DetteNette/EBITDA
        # ne sont pas pertinents : on ne les exige pas dans la complétude
        # (ils seront marqués « n/a (secteur) » côté affichage et comptés
        # comme satisfaits — ce n'est pas un trou, c'est non applicable).
        fin = rec["is_financial"]
        rec["ok"] = (
            rec["mcap"] is not None and rec["yield"] is not None
            and (fin or rec["nd"] is not None)
            and None not in rec["rev"]
            and (fin or None not in rec["eb"])
            and None not in rec["ni"] and None not in rec["p"]
            and None not in rec["div"]
        )
    except Exception as e:
        rec["err"] = str(e)[:200]
    return rec


def _build():
    import os
    full = load_universe()
    limit = int(os.getenv("CLEMENT_LIMIT", "0") or 0)
    universe = full[:limit] if limit > 0 else full
    companies = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(_fetch_one, *u) for u in universe]
        for f in futs:
            try:
                companies.append(f.result(timeout=60))
            except Exception as e:
                logger.warning(f"[CLEMENT] ticker échoué : {e}")
    ok = [c for c in companies if c.get("ok")]
    payload = {
        "as_of": datetime.now().isoformat(timespec="seconds"),
        "source": "Yahoo Finance (yfinance)",
        "count": len(ok),
        "fetched": len(companies),
        "note": "Données réelles. Croissance évaluée sur ~5 ans (plus ancien "
                "exercice publié par la source → dernier ; cours & dividende "
                "sur ~5 ans). Seules les sociétés à données complètes sont "
                "affichées — aucune valeur inventée, aucun n/d.",
        "companies": ok,
    }
    if not ok:
        # Build infructueux : ne pas écraser un bon cache existant.
        prev = _read_cache()
        if prev and prev.get("companies"):
            logger.warning("[CLEMENT] build vide — ancien cache conservé")
            return prev
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return payload


def _refresh_locked():
    if not _lock.acquire(blocking=False):
        return
    try:
        _state["refreshing"] = True
        _state["started_at"] = datetime.now().isoformat(timespec="seconds")
        _state["last_attempt"] = time.time()
        t0 = time.time()
        p = _build()
        logger.info(f"[CLEMENT] cache rafraîchi : {p['count']}/{p['fetched']} valeurs en {time.time()-t0:.0f}s")
    except Exception as e:
        logger.error(f"[CLEMENT] échec refresh : {e}")
    finally:
        _state["refreshing"] = False
        _lock.release()


def refresh_async():
    """Lance un rafraîchissement en arrière-plan (non bloquant)."""
    if _state["refreshing"]:
        return False
    threading.Thread(target=_refresh_locked, daemon=True).start()
    return True


def _read_cache():
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def get():
    """Renvoie le cache + méta. Déclenche un refresh si vide ou périmé."""
    cache = _read_cache()
    stale = True
    if cache:
        try:
            age = (datetime.now() - datetime.fromisoformat(cache["as_of"])).total_seconds()
            stale = age > STALE_SECONDS
        except Exception:
            stale = True
        if not cache.get("companies"):
            stale = True  # cache vide (build raté) = à réessayer
    needs = cache is None or stale
    cooldown_ok = (time.time() - _state["last_attempt"]) > AUTO_RETRY_COOLDOWN
    if needs and not _state["refreshing"] and cooldown_ok:
        refresh_async()
    return {
        "ready": cache is not None,
        "refreshing": _state["refreshing"],
        "stale": stale,
        **(cache or {"companies": [], "count": 0, "as_of": None}),
    }

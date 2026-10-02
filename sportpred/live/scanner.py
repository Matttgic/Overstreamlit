"""Scanner quotidien de value bets (football) — 100 % gratuit, sans clé API.

Sources :
- https://www.football-data.co.uk/fixtures.csv : matchs à venir des 22 championnats
  principaux avec cotes bet365, bwin (agréés ANJ), Betfair Exchange, max, moyenne…
- https://www.football-data.co.uk/new_league_fixtures.csv : 16 championnats « extra ».
- résultats de la saison en cours (mmz4281/<saison>/<code>.csv) pour mettre à jour le
  modèle Dixon-Coles et pour régler les paris passés.

Les noms d'équipes sont identiques entre fichiers football-data : aucune correspondance
floue n'est nécessaire (ce qui corrige le bug de l'ancien app.py, qui associait par
exemple « Sunderland » à « Salernitana »).

Stratégie appliquée (voir docs/strategies/) : probabilité « juste » issue du marché
sharp (Betfair Exchange, sans marge, méthode power), éventuellement mélangée au modèle
Dixon-Coles, comparée aux cotes des bookmakers agréés ANJ disponibles dans le fichier.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import requests

from ..betting.kelly import kelly_fraction
from ..betting.odds import devig
from ..data.football_data import BASE, MAIN_LEAGUES, _parse_dates, _read_csv_bytes
from ..features import country_of
from ..models.dixon_coles import DixonColes

OUT = ["H", "D", "A"]


@dataclass
class ScanConfig:
    sharp: str = "BFE"                    # référence sharp : Betfair Exchange
    soft_books: list = field(default_factory=lambda: ["B365", "BW"])  # agréés ANJ
    min_ev: float = 0.03                  # EV minimale contre la proba sharp
    max_ev: float = 0.30                  # au-delà : probable erreur de cote
    max_odds: float = 10.0
    model_weight: float = 0.0             # 0 = marché seul ; 0.2 = 20 % Dixon-Coles
    kelly_frac: float = 0.25
    kelly_cap: float = 0.02               # mise max 2 % de la bankroll
    bankroll: float = 1000.0


def current_season_code(today: pd.Timestamp | None = None) -> str:
    t = today or pd.Timestamp.today()
    y = t.year if t.month >= 7 else t.year - 1
    return f"{y % 100:02d}{(y + 1) % 100:02d}"


def fetch_csv(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return _read_csv_bytes(r.content)


def load_fixtures() -> pd.DataFrame:
    fx = fetch_csv(f"{BASE}/fixtures.csv")
    fx = fx.rename(columns=lambda c: str(c).strip())
    fx = fx.dropna(subset=["HomeTeam", "AwayTeam"])
    fx["Date"] = _parse_dates(fx["Date"])
    fx["League"] = fx["Div"]
    fx["Country"] = fx["League"].map(country_of)
    for c in fx.columns:
        if c not in ("Div", "Date", "Time", "HomeTeam", "AwayTeam", "Referee", "League", "Country"):
            fx[c] = pd.to_numeric(fx[c], errors="coerce")
    return fx


def load_recent_results(seasons: list[str], leagues=None) -> pd.DataFrame:
    leagues = leagues or list(MAIN_LEAGUES)
    frames = []
    for s in seasons:
        for lg in leagues:
            try:
                d = fetch_csv(f"{BASE}/mmz4281/{s}/{lg}.csv")
            except Exception:  # noqa: BLE001
                continue
            d = d.rename(columns=lambda c: str(c).strip()).dropna(subset=["HomeTeam", "FTHG"])
            keep = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"] + [
                c for c in ("BFECH", "BFECD", "BFECA", "PSCH", "PSCD", "PSCA") if c in d]
            d = d[keep].copy()
            d["Date"] = _parse_dates(d["Date"])
            d["League"] = lg
            frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df["Country"] = df["League"].map(country_of)
    return df


def dixon_coles_today(results: pd.DataFrame, fixtures: pd.DataFrame,
                      window_days: int = 3 * 365) -> pd.DataFrame:
    today = pd.Timestamp.today().normalize()
    preds = []
    for c, fx in fixtures.groupby("Country"):
        tr = results[(results["Country"] == c) &
                     (results["Date"] >= today - pd.Timedelta(days=window_days))]
        if len(tr) < 200:
            continue
        m = DixonColes().fit(tr["HomeTeam"].values, tr["AwayTeam"].values, tr["FTHG"].values,
                             tr["FTAG"].values, (today - tr["Date"]).dt.days.values)
        p = m.predict(fx["HomeTeam"].values, fx["AwayTeam"].values)
        p.index = fx.index
        known = set(m.teams)
        p["dc_known"] = [h in known and a in known for h, a in zip(fx["HomeTeam"], fx["AwayTeam"])]
        preds.append(p)
    return pd.concat(preds) if preds else pd.DataFrame()


def find_value(fx: pd.DataFrame, cfg: ScanConfig) -> pd.DataFrame:
    """Retourne les paris recommandés (une ligne par match au plus)."""
    sharp_cols = [f"{cfg.sharp}{o}" for o in OUT]
    fx = fx.dropna(subset=sharp_cols).copy()
    p_sharp = devig(fx[sharp_cols].values, "power")
    p = p_sharp
    if cfg.model_weight > 0 and "dc_ph" in fx:
        pm = fx[["dc_ph", "dc_pd", "dc_pa"]].values
        known = fx["dc_known"].fillna(False).astype(bool).values if "dc_known" in fx else True
        ok = ~np.isnan(pm).any(axis=1) & known
        lp = np.where(ok[:, None],
                      cfg.model_weight * np.log(np.clip(pm, 1e-9, 1))
                      + (1 - cfg.model_weight) * np.log(p_sharp), np.log(p_sharp))
        p = np.exp(lp)
        p /= p.sum(axis=1, keepdims=True)
    rows = []
    for i, (ix, r) in enumerate(fx.iterrows()):
        best = None
        for j, o in enumerate(OUT):
            for bk in cfg.soft_books:
                odd = r.get(f"{bk}{o}")
                if odd is None or np.isnan(odd) or odd > cfg.max_odds:
                    continue
                ev = p[i, j] * odd - 1
                if cfg.min_ev <= ev <= cfg.max_ev and (best is None or ev > best["ev"]):
                    best = {"date": r["Date"].date(), "heure": r.get("Time"), "league": r["League"],
                            "match": f"{r['HomeTeam']} - {r['AwayTeam']}", "selection": o,
                            "bookmaker": bk, "cote": odd, "p_juste": round(p[i, j], 4),
                            "cote_juste": round(1 / p[i, j], 3), "ev": round(ev, 4)}
        if best:
            f = kelly_fraction(best["p_juste"], best["cote"]) * cfg.kelly_frac
            best["mise_%"] = round(100 * min(f, cfg.kelly_cap), 2)
            best["mise_€"] = round(cfg.bankroll * min(f, cfg.kelly_cap), 2)
            rows.append(best)
    return pd.DataFrame(rows)


def settle(history: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    """Règle les paris en attente à partir des résultats officiels football-data."""
    if history.empty:
        return history
    res = results.assign(match=results["HomeTeam"] + " - " + results["AwayTeam"],
                         d=results["Date"].dt.date.astype(str))
    res["res"] = np.where(res["FTHG"] > res["FTAG"], "H",
                          np.where(res["FTHG"] == res["FTAG"], "D", "A"))
    # cote juste de clôture (Betfair Exchange sans marge) pour calculer la CLV
    close = {}
    if all(c in res for c in ("BFECH", "BFECD", "BFECA")):
        o = res[["BFECH", "BFECD", "BFECA"]].apply(pd.to_numeric, errors="coerce").values
        ok = ~np.isnan(o).any(axis=1)
        fair = np.full(o.shape, np.nan)
        fair[ok] = 1 / devig(o[ok], "power")
        close = {k: dict(zip(OUT, f)) for k, f in zip(zip(res["d"], res["match"]), fair)}
    key = dict(zip(zip(res["d"], res["match"]), res["res"]))
    h = history.copy()
    if "clv" not in h:
        h["clv"] = np.nan
    for ix, r in h[h["statut"] == "en attente"].iterrows():
        k = (str(r["date"]), r["match"])
        out = key.get(k)
        if out:
            won = out == r["selection"]
            h.loc[ix, "statut"] = "gagné" if won else "perdu"
            h.loc[ix, "profit_€"] = round(r["mise_€"] * (r["cote"] - 1) if won else -r["mise_€"], 2)
            fc = close.get(k, {}).get(r["selection"])
            if fc is not None and not np.isnan(fc):
                h.loc[ix, "clv"] = round(r["cote"] / fc - 1, 4)
    return h


def read_history_csv(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text))

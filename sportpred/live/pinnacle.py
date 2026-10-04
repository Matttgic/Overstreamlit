"""Cotes Pinnacle en direct via l'API publique « guest » (sans clé, sans compte).

Pinnacle est le bookmaker « sharp » de référence : ses cotes sans marge sont la
meilleure estimation disponible de la probabilité réelle (voir docs/07, docs/08).

Endpoints (vérifiés le 02/10/2026) :
- /sports, /sports/{id}/leagues?all=false
- /leagues/{id}/matchups        (matchs + « specials » : props de match et de joueurs)
- /leagues/{id}/markets/straight (prix américains par marché : moneyline, spread,
                                   total, team_total ; et prix des specials)

Toutes les fonctions renvoient des DataFrame « longs » : une ligne par issue, avec la cote
décimale Pinnacle et la probabilité juste (marge retirée par la méthode power, issue par
issue au sein de chaque marché).
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
import requests

from ..betting.odds import devig

BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
HEADERS = {"User-Agent": "Mozilla/5.0 (Overstreamlit research)", "Accept": "application/json"}

# Compétitions suivies (sous-ensemble de la liste ANJ), découvertes dynamiquement parmi les
# ligues Pinnacle ayant des matchs ouverts : sport_id -> (nom, expression régulière)
SPORTS = {
    29: ("football", r"^(?:France - Ligue [12]|England - Premier League|Spain - La Liga|Italy - Serie A|"
                     r"Germany - Bundesliga|Netherlands - Eredivisie|Portugal - Primeira Liga|"
                     r"UEFA - (?:Champions|Europa|Conference) League|UEFA - Nations League [ABC]|"
                     r"FIFA - World Cup|UEFA - European Championship)$"),
    33: ("tennis", r"^(?:ATP|WTA) (?!Challenger|125K)(?!.*Doubles)"),
    4: ("basket", r"^(?:NBA|Europe - Euroleague|France - Championnat Pro A|Spain - ACB)$"),
    19: ("hockey", r"^(?:NHL|France - Ligue Magnus|Russia - Kontinental Hockey League|Sweden - SHL|"
                   r"Finland - SM Liiga|Switzerland - Nationalliga A|Germany - DEL|"
                   r"Czech Republic - Extraliga|Europe - Champions Hockey League)$"),
    15: ("football_americain", r"^NFL$"),
    3: ("baseball", r"^(?:MLB|Korea Professional Baseball|Nippon Professional Baseball)$"),
    18: ("handball", r"^(?:France - Division 1|Germany - Bundesliga|Spain - Liga Asobal|"
                     r"Denmark - Haandboldligaen|Europe - Champions League)$"),
    27: ("rugby", r"(?:Top 14|Pro D2|Champions Cup|Six Nations|Gallagher Premiership|"
                  r"United Rugby Championship|Rugby World Cup|Rugby Championship)"),
    22: ("mma", r"^(?:UFC|PFL)$"),
    34: ("volley", r"^(?:France|Italy|Poland|Turkey|Europe - CEV Champions)"),
}


def _get(path: str, retries: int = 3):
    for i in range(retries):
        try:
            r = requests.get(BASE + path, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(1.5 * (i + 1))
    return None


def american_to_decimal(p: float) -> float:
    p = float(p)
    return 1 + p / 100.0 if p > 0 else 1 + 100.0 / abs(p)


def active_leagues(sport_id: int, min_matchups: int = 1) -> pd.DataFrame:
    """Ligues ayant des matchs ouverts pour un sport (ex. 33 = tennis)."""
    L = _get(f"/sports/{sport_id}/leagues?all=false") or []
    return pd.DataFrame([{"league_id": x["id"], "league": x["name"], "n": x.get("matchupCount", 0)}
                         for x in L if x.get("matchupCount", 0) >= min_matchups])


def league_odds(league_id: int, sport: str = "", league_name: str = "",
                include_props: bool = True) -> pd.DataFrame:
    """Toutes les cotes d'avant-match d'une ligue, format long, avec probabilités justes."""
    matchups = _get(f"/leagues/{league_id}/matchups") or []
    markets = _get(f"/leagues/{league_id}/markets/straight") or []
    if not matchups or not markets:
        return pd.DataFrame()
    by_id = {m["id"]: m for m in matchups}
    rows = []
    for mk in markets:
        if mk.get("status", "open") != "open":
            continue
        mu = by_id.get(mk.get("matchupId"))
        if mu is None or mu.get("isLive"):
            continue
        # lignes alternatives ignorées pour les matchs ; les props joueurs sont souvent
        # marquées « alternate » chez Pinnacle, on les garde
        if mk.get("isAlternate") and mu.get("type") != "special":
            continue
        prices = mk.get("prices") or []
        if len(prices) < 2:
            continue
        if mu.get("type") == "matchup":
            parts = {p["alignment"]: p["name"] for p in mu.get("participants", [])}
            home, away = parts.get("home"), parts.get("away")
            # marchés dérivés (« Belgium (Corners) », « (Bookings) »…) : cartons et corners ne sont
            # PAS autorisés par l'ANJ en pari à cote classique -> exclus ; on garde « (Games) » (tennis)
            if home and "(" in str(home) and not str(home).endswith(" (Games)"):
                continue
            games = bool(home and str(home).endswith(" (Games)"))   # tennis : marchés en jeux
            if games:
                home, away = home.replace(" (Games)", ""), str(away).replace(" (Games)", "")
            event = f"{home} - {away}"
            start = mu.get("startTime")
            mtype = mk["type"]
            if mk.get("period", 0) != 0 or mtype not in ("moneyline", "spread", "total"):
                continue
            for p in prices:
                d = p.get("designation")
                sel = {"home": home, "away": away, "draw": "Nul", "over": "Plus", "under": "Moins"}.get(d, d)
                rows.append({"event_id": mu["id"], "start": start, "event": event, "home": home,
                             "away": away, "market": mtype, "selection": sel, "side": d,
                             "line": p.get("points"), "pin_odds": american_to_decimal(p["price"]),
                             "market_key": f'{mu["id"]}|{mk["key"]}', "is_prop": False,
                             "unit": "jeux" if games else None})
        elif include_props and mu.get("type") == "special" and mu.get("parentId"):
            parent = by_id.get(mu["parentId"])
            if parent is None:
                continue
            parts = {p["alignment"]: p["name"] for p in parent.get("participants", [])}
            home, away = parts.get("home"), parts.get("away")
            pname = {p["id"]: p["name"] for p in mu.get("participants", [])}
            sp = mu.get("special") or {}
            for p in prices:
                rows.append({"event_id": parent["id"], "start": parent.get("startTime"),
                             "event": f"{home} - {away}", "home": home, "away": away,
                             "market": f'{sp.get("category", "")}: {sp.get("description", "")}',
                             "selection": pname.get(p.get("participantId"), "?"), "side": None,
                             "line": p.get("points"), "pin_odds": american_to_decimal(p["price"]),
                             "market_key": f'{mu["id"]}|{mk["key"]}', "is_prop": True})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["sport"] = sport
    df["league"] = league_name
    df["start"] = pd.to_datetime(df["start"], utc=True)
    # probabilité juste : marge retirée au sein de chaque marché (même clé)
    df["fair_prob"] = np.nan
    for _, idx in df.groupby("market_key").groups.items():
        o = df.loc[idx, "pin_odds"].values
        if len(o) >= 2:
            df.loc[idx, "fair_prob"] = devig(o[None, :], "power")[0]
    df["fair_odds"] = 1 / df["fair_prob"]
    df["pin_margin"] = df.groupby("market_key")["pin_odds"].transform(lambda s: (1 / s).sum() - 1)
    return df


def all_odds(sports: dict | None = None, max_leagues_per_sport: int = 30) -> pd.DataFrame:
    """Cotes de toutes les compétitions suivies, avec probabilités justes."""
    sports = sports or SPORTS
    frames = []
    for sid, (sname, pattern) in sports.items():
        L = active_leagues(sid)
        if L.empty:
            continue
        L = L[L["league"].str.contains(pattern, regex=True)]
        for r in L.head(max_leagues_per_sport).itertuples():
            f = league_odds(r.league_id, sname, r.league, include_props=sname in ("hockey", "basket", "football"))
            if not f.empty:
                frames.append(f)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

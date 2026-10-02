"""Règlement automatique des paris proposés à partir des scores ESPN (API publique, sans clé).

Couverture : football (22 championnats football-data + compétitions Pinnacle suivies),
NBA, NHL, NFL, MLB, tennis ATP/WTA, UFC. Les autres compétitions (handball, KHL…) restent
suivies par la CLV uniquement.
Appariement : même règle stricte que pour les cotes (heure ± 6 h, deux noms similaires,
correspondance unique). Un pari introuvable 3 jours après le match est marqué « non réglé ».
"""
from __future__ import annotations

import pandas as pd
import requests

from .matching import match_events, sim

ESPN = "https://site.api.espn.com/apis/site/v2/sports"
LEAGUES = {
    "France - Ligue 1": "soccer/fra.1", "France - Ligue 2": "soccer/fra.2",
    "England - Premier League": "soccer/eng.1", "Spain - La Liga": "soccer/esp.1",
    "Italy - Serie A": "soccer/ita.1", "Germany - Bundesliga": "soccer/ger.1",
    "Netherlands - Eredivisie": "soccer/ned.1", "Portugal - Primeira Liga": "soccer/por.1",
    "UEFA - Champions League": "soccer/uefa.champions", "UEFA - Europa League": "soccer/uefa.europa",
    "UEFA - Conference League": "soccer/uefa.europa.conf", "UEFA - Nations League A": "soccer/uefa.nations",
    "NBA": "basketball/nba", "NHL": "hockey/nhl", "NFL": "football/nfl", "MLB": "baseball/mlb",
    "UFC": "mma/ufc",
    # codes football-data.co.uk
    "E0": "soccer/eng.1", "E1": "soccer/eng.2", "E2": "soccer/eng.3", "E3": "soccer/eng.4",
    "EC": "soccer/eng.5", "SC0": "soccer/sco.1", "SC1": "soccer/sco.2", "SC2": "soccer/sco.3",
    "SC3": "soccer/sco.4", "D1": "soccer/ger.1", "D2": "soccer/ger.2", "I1": "soccer/ita.1",
    "I2": "soccer/ita.2", "SP1": "soccer/esp.1", "SP2": "soccer/esp.2", "F1": "soccer/fra.1",
    "F2": "soccer/fra.2", "N1": "soccer/ned.1", "B1": "soccer/bel.1", "P1": "soccer/por.1",
    "T1": "soccer/tur.1", "G1": "soccer/gre.1",
}


def league_path(league: str) -> str | None:
    if league in LEAGUES:
        return LEAGUES[league]
    if str(league).startswith("ATP"):
        return "tennis/atp"
    if str(league).startswith("WTA"):
        return "tennis/wta"
    return None


def _name(c: dict) -> str:
    t = c.get("team") or c.get("athlete") or {}
    return t.get("displayName") or t.get("shortDisplayName") or ""


def scoreboard(path: str, day: pd.Timestamp) -> list[dict]:
    try:
        r = requests.get(f"{ESPN}/{path}/scoreboard", params={"dates": day.strftime("%Y%m%d"), "limit": 500},
                         timeout=30)
        if not r.ok:
            return []
        events = r.json().get("events", [])
    except (requests.RequestException, ValueError):
        return []
    out = []
    for ev in events:
        comps = list(ev.get("competitions", []))
        for g in ev.get("groupings", []) or []:
            comps += g.get("competitions", [])
        for c in comps:
            cs = c.get("competitors", [])
            if len(cs) != 2:
                continue
            st = (c.get("status") or ev.get("status") or {}).get("type", {})
            home = next((x for x in cs if x.get("homeAway") == "home"), cs[0])
            away = next((x for x in cs if x is not home), cs[1])
            win = "home" if home.get("winner") else "away" if away.get("winner") else None
            out.append({"event_id": c.get("id") or ev.get("id"),
                        "start": pd.Timestamp(c.get("date") or ev.get("date")).tz_convert("UTC")
                        if pd.Timestamp(c.get("date") or ev.get("date")).tzinfo else
                        pd.Timestamp(c.get("date") or ev.get("date"), tz="UTC"),
                        "home": _name(home), "away": _name(away), "completed": bool(st.get("completed")),
                        "winner": win, "home_score": home.get("score"), "away_score": away.get("score")})
    return out


def _pick_side(h: dict, home: str, away: str) -> str | None:
    s = str(h["selection"])
    if s.startswith("domicile"):
        return "home"
    if s.startswith("extérieur"):
        return "away"
    if s.startswith("Nul"):
        return "draw"
    a, b = sim(s, home), sim(s, away)
    if max(a, b) < 0.8 or abs(a - b) < 0.1:
        return None
    return "home" if a > b else "away"


def settle(hist: list[dict], now: pd.Timestamp, cache: dict | None = None) -> list[dict]:
    cache = {} if cache is None else cache
    for h in hist:
        if h.get("result") or h.get("status") == "en attente":
            continue
        start = pd.Timestamp(h["start"])
        if now < start + pd.Timedelta(hours=3):
            continue
        path = league_path(h.get("league", ""))
        if path is None:
            h["result"] = "non couvert (CLV seulement)"
            continue
        rows = []
        for dd in (-1, 0, 1):
            day = (start + pd.Timedelta(days=dd)).normalize()
            key = (path, day.strftime("%Y%m%d"))
            if key not in cache:
                cache[key] = scoreboard(path, day)
            rows += cache[key]
        res = pd.DataFrame(rows).drop_duplicates("event_id") if rows else pd.DataFrame()
        parts = str(h["event"]).split(" - ")
        if res.empty or len(parts) != 2:
            if now > start + pd.Timedelta(days=3):
                h["result"] = "non réglé (résultat introuvable)"
            continue
        left = pd.DataFrame({"event_id": ["p"], "start": [start], "home": [parts[0]], "away": [parts[1]]})
        m = match_events(left, res, max_hours=6, swap_ok=h.get("sport") in ("tennis", "mma"))
        if m.empty:
            if now > start + pd.Timedelta(days=3):
                h["result"] = "non réglé (résultat introuvable)"
            continue
        r = res[res["event_id"] == m.iloc[0]["right_id"]].iloc[0]
        if not r["completed"]:
            continue
        side = _pick_side(h, parts[0], parts[1])
        if side is None:
            h["result"] = "non réglé (sélection ambiguë)"
            continue
        if bool(m.iloc[0]["swapped"]) and side in ("home", "away"):
            side = "away" if side == "home" else "home"
        outcome = r["winner"] or "draw"
        won = outcome == side
        h["result"] = "gagné" if won else "perdu"
        h["score"] = f"{r['home_score']}-{r['away_score']}"
        h["profit_units"] = round(h["odds"] - 1, 3) if won else -1.0
        h["status"] = "réglé"
    return hist

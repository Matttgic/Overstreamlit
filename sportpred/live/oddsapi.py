"""Cotes des bookmakers français via The Odds API (offre gratuite : 500 crédits/mois).

Région « fr » : betclic_fr, netbet_fr, pmu_fr, unibet_fr, winamax_fr (vérifié sur
https://the-odds-api.com/sports-odds-data/bookmaker-apis.html le 02/10/2026).
Clé gratuite : https://the-odds-api.com (inscription par e-mail), à mettre dans la
variable d'environnement / le secret GitHub `THE_ODDS_API_KEY`.

Coût : un appel /odds = nb_marchés × nb_régions crédits. Les appels /sports et /events
sont gratuits : on s'en sert pour n'interroger que les sports qui ont des matchs bientôt.
Sans clé, toutes les fonctions renvoient un DataFrame vide (le site fonctionne quand même
avec Pinnacle + football-data).
"""
from __future__ import annotations

import os

import pandas as pd
import requests

BASE = "https://api.the-odds-api.com/v4"
FR_BOOKS = {"betclic_fr": "Betclic", "netbet_fr": "NetBet", "pmu_fr": "PMU",
            "unibet_fr": "Unibet", "winamax_fr": "Winamax"}

# préfixes de clés sportives suivies (alignées sur pinnacle.SPORTS)
SPORT_PREFIXES = {
    "soccer_france_ligue_one": "football", "soccer_france_ligue_two": "football",
    "soccer_epl": "football", "soccer_spain_la_liga": "football", "soccer_italy_serie_a": "football",
    "soccer_germany_bundesliga": "football", "soccer_netherlands_eredivisie": "football",
    "soccer_portugal_primeira_liga": "football", "soccer_uefa_champs_league": "football",
    "soccer_uefa_europa_league": "football", "soccer_uefa_europa_conference_league": "football",
    "soccer_uefa_nations_league": "football",
    "basketball_nba": "basket", "basketball_euroleague": "basket",
    "icehockey_nhl": "hockey", "americanfootball_nfl": "football_americain",
    "baseball_mlb": "baseball", "mma_mixed_martial_arts": "mma",
    "tennis_atp": "tennis", "tennis_wta": "tennis",
    "rugbyunion": "rugby", "handball": "handball",
}


class Budget:
    def __init__(self):
        self.remaining = None
        self.used = 0


def _key():
    return os.environ.get("THE_ODDS_API_KEY", "").strip()


def active_sports() -> list[str]:
    k = _key()
    if not k:
        return []
    r = requests.get(f"{BASE}/sports", params={"apiKey": k}, timeout=30)
    if r.status_code != 200:
        return []
    keys = [s["key"] for s in r.json() if s.get("active")]
    return [s for s in keys if any(s.startswith(p) for p in SPORT_PREFIXES)]


def events_soon(sport_key: str, hours: float = 36) -> int:
    """Nombre d'événements dans les `hours` prochaines heures (appel gratuit)."""
    k = _key()
    r = requests.get(f"{BASE}/sports/{sport_key}/events", params={"apiKey": k}, timeout=30)
    if r.status_code != 200:
        return 0
    now = pd.Timestamp.now(tz="UTC")
    st = pd.to_datetime([e["commence_time"] for e in r.json()], utc=True)
    return int(((st > now) & (st < now + pd.Timedelta(hours=hours))).sum())


def fr_odds(max_calls: int = 8, markets: str = "h2h", hours: float = 36,
            budget: Budget | None = None) -> pd.DataFrame:
    """Cotes 1N2 / vainqueur des bookmakers français, format long."""
    k = _key()
    if not k:
        return pd.DataFrame()
    budget = budget or Budget()
    rows, calls = [], 0
    for sk in active_sports():
        if calls >= max_calls:
            break
        if events_soon(sk, hours) == 0:
            continue
        r = requests.get(f"{BASE}/sports/{sk}/odds", timeout=30,
                         params={"apiKey": k, "regions": "fr", "markets": markets, "oddsFormat": "decimal"})
        calls += 1
        budget.remaining = r.headers.get("x-requests-remaining", budget.remaining)
        budget.used = r.headers.get("x-requests-used", budget.used)
        if r.status_code != 200:
            continue
        rows += parse_odds(r.json(), sk)
    return pd.DataFrame(rows)


def parse_odds(payload: list, sport_key: str) -> list[dict]:
    sport = next((v for p, v in SPORT_PREFIXES.items() if sport_key.startswith(p)), sport_key)
    rows = []
    for ev in payload:
        for bk in ev.get("bookmakers", []):
            if bk["key"] not in FR_BOOKS:
                continue
            for mk in bk.get("markets", []):
                for o in mk.get("outcomes", []):
                    name = o["name"]
                    sel = ("Nul" if name == "Draw" else name)
                    rows.append({"event_id": ev["id"], "sport": sport, "sport_key": sport_key,
                                 "start": pd.Timestamp(ev["commence_time"]), "home": ev["home_team"],
                                 "away": ev["away_team"], "market": {"h2h": "moneyline", "totals": "total"}
                                 .get(mk["key"], mk["key"]), "selection": sel, "line": o.get("point"),
                                 "book": FR_BOOKS[bk["key"]], "odds": float(o["price"])})
    return rows

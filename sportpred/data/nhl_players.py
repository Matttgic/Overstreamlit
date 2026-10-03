"""Statistiques NHL joueur par match (API publique de la NHL, sans clé).

Source : https://api.nhle.com/stats/rest/en/skater/{summary,timeonice}
(`isGame=true` -> une ligne par joueur et par match). L'API renvoie au plus 10 000
lignes par requête : on découpe chaque saison par mois (~7 000 lignes).

Colonnes produites (une ligne par joueur de champ et par match) :
    game_id, date, season, team, opp, home (bool), player_id, name, pos (C/L/R/D),
    goals, assists, pp_goals, ot_goals, shots, toi, pp_toi, sh_toi   (temps en minutes)
Les buts en tirs au but ne sont crédités à aucun joueur : ils ne comptent pas pour
le pari « buteur », comme chez les bookmakers.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

STATS = "https://api.nhle.com/stats/rest/en/skater"
SORT = '[{"property":"gameId","direction":"ASC"},{"property":"playerId","direction":"ASC"}]'


def _get(report: str, season: int, start: str, end: str, game_type: int) -> list[dict]:
    exp = (f"seasonId={season} and gameTypeId={game_type} "
           f'and gameDate>="{start}" and gameDate<"{end}"')
    for attempt in range(4):
        try:
            r = requests.get(f"{STATS}/{report}", timeout=120,
                             params={"isAggregate": "false", "isGame": "true", "start": 0,
                                     "limit": -1, "sort": SORT, "cayenneExp": exp})
            r.raise_for_status()
            d = r.json()
            if d.get("total", 0) >= 10000:
                raise RuntimeError(f"fenêtre trop large ({start} -> {end}) : découper davantage")
            return d["data"]
        except (requests.RequestException, ValueError):
            time.sleep(2 ** attempt)
    raise RuntimeError(f"API NHL injoignable pour {report} {season} {start}")


def season_games(season: int, game_type: int = 2) -> pd.DataFrame:
    """Saison `season` au format 20242025 (saison 2024-25)."""
    y = season // 10000
    months = pd.date_range(f"{y}-09-01", f"{y + 1}-08-01", freq="MS")
    summ, toi = [], []
    for a, b in zip(months[:-1], months[1:]):
        s, e = a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")
        summ += _get("summary", season, s, e, game_type)
        toi += _get("timeonice", season, s, e, game_type)
    if not summ:
        return pd.DataFrame()
    a = pd.DataFrame(summ)
    t = pd.DataFrame(toi)[["gameId", "playerId", "timeOnIce", "ppTimeOnIce", "shTimeOnIce"]]
    df = a.merge(t, on=["gameId", "playerId"], how="left")
    out = pd.DataFrame({
        "game_id": df["gameId"].astype(int), "date": pd.to_datetime(df["gameDate"]),
        "season": season, "team": df["teamAbbrev"], "opp": df["opponentTeamAbbrev"],
        "home": df["homeRoad"] == "H", "player_id": df["playerId"].astype(int),
        "name": df["skaterFullName"], "pos": df["positionCode"],
        "goals": df["goals"].fillna(0).astype(int), "assists": df["assists"].fillna(0).astype(int),
        "pp_goals": df["ppGoals"].fillna(0).astype(int),
        "ot_goals": df["otGoals"].fillna(0).astype(int), "shots": df["shots"].fillna(0).astype(int),
        "toi": df["timeOnIce"].fillna(df["timeOnIcePerGame"]).astype(float) / 60,
        "pp_toi": df["ppTimeOnIce"].fillna(0).astype(float) / 60,
        "sh_toi": df["shTimeOnIce"].fillna(0).astype(float) / 60,
    })
    return out.drop_duplicates(["game_id", "player_id"]).sort_values(["date", "game_id", "team"])


def load(raw: Path, seasons: list[int], refresh_current: bool = False) -> pd.DataFrame:
    """Charge (et met en cache dans raw/nhl_players/) les saisons demandées."""
    d = raw / "nhl_players"
    d.mkdir(parents=True, exist_ok=True)
    frames = []
    for s in seasons:
        f = d / f"skaters_{s}.parquet"
        if not f.exists() or (refresh_current and s == max(seasons)):
            g = season_games(s)
            if g.empty:
                continue
            g.to_parquet(f, index=False)
        frames.append(pd.read_parquet(f))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

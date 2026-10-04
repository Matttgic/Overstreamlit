"""Statistiques football joueur par match (Understat, gratuit, sans clé).

Source : https://understat.com — 5 grands championnats européens depuis 2014-15.
- `getLeagueData/{ligue}/{saison}` : calendrier (identifiants des matchs), équipes, joueurs ;
- `getMatchData/{match}` : compositions (minutes, buts, tirs, xG, poste, entrées/sorties)
  et liste des tirs (dont les penaltys).
Saison = année de début (2025 = 2025-26).

Une ligne par joueur et par match :
    match_id, date, league, season, team_id, team, opp, home, team_goals, opp_goals,
    player_id, player, position (poste du jour, « Sub » pour un remplaçant), pos_order,
    time (minutes), goals (hors c.s.c.), own_goals, shots, xg, npxg, pen_att, pen_goals,
    pen_xg, assists, xa, key_passes, starter (bool)
Les buts contre son camp ne sont crédités à aucun buteur : ils ne comptent pas pour le pari
« buteur », comme chez les bookmakers.
"""
from __future__ import annotations

import gzip
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

BASE = "https://understat.com"
LEAGUES = {"EPL": "Premier League", "La_liga": "La Liga", "Bundesliga": "Bundesliga",
           "Serie_A": "Serie A", "Ligue_1": "Ligue 1"}
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/126.0 Safari/537.36",
           "X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*"}


def _get(path: str, referer: str, attempts: int = 5) -> dict:
    for k in range(attempts):
        try:
            r = requests.get(f"{BASE}/{path}", headers={**HEADERS, "Referer": f"{BASE}/{referer}"}, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return {}
        except (requests.RequestException, ValueError):
            pass
        time.sleep(min(2 ** k, 20))
    raise RuntimeError(f"Understat injoignable : {path}")


def league_season(league: str, season: int) -> dict:
    return _get(f"getLeagueData/{league}/{season}", f"league/{league}/{season}")


def fixtures(data: dict, league: str, season: int) -> pd.DataFrame:
    """Calendrier d'une saison (matchs joués et à venir)."""
    rows = []
    for d in data.get("dates") or []:
        rows.append({"match_id": int(d["id"]), "date": pd.Timestamp(d["datetime"]), "league": league,
                     "season": season, "played": bool(d.get("isResult")),
                     "home_id": int(d["h"]["id"]), "home": d["h"]["title"],
                     "away_id": int(d["a"]["id"]), "away": d["a"]["title"],
                     "home_goals": pd.to_numeric((d.get("goals") or {}).get("h"), errors="coerce"),
                     "away_goals": pd.to_numeric((d.get("goals") or {}).get("a"), errors="coerce")})
    return pd.DataFrame(rows)


def match_rows(fx: dict, data: dict) -> list[dict]:
    """Lignes joueur-match d'un match (`fx` : ligne du calendrier, `data` : getMatchData)."""
    pens: dict[str, list[float]] = {}
    for side in ("h", "a"):
        for s in (data.get("shots") or {}).get(side) or []:
            if s.get("situation") == "Penalty":
                p = pens.setdefault(str(s["player_id"]), [0, 0, 0.0])
                p[0] += 1
                p[1] += s.get("result") == "Goal"
                p[2] += float(s.get("xG") or 0)
    out = []
    for side in ("h", "a"):
        home = side == "h"
        team, opp = (fx["home"], fx["away"]) if home else (fx["away"], fx["home"])
        tg, og = (fx["home_goals"], fx["away_goals"]) if home else (fx["away_goals"], fx["home_goals"])
        for r in ((data.get("rosters") or {}).get(side) or {}).values():
            pid = str(r["player_id"])
            pa, pg, px = pens.get(pid, [0, 0, 0.0])
            xg = float(r.get("xG") or 0)
            out.append({
                "match_id": fx["match_id"], "date": fx["date"], "league": fx["league"], "season": fx["season"],
                "team_id": int(r["team_id"]), "team": team, "opp": opp, "home": home,
                "team_goals": tg, "opp_goals": og, "player_id": int(pid), "player": r.get("player"),
                "position": r.get("position"), "pos_order": int(r.get("positionOrder") or 0),
                "time": int(r.get("time") or 0), "goals": int(r.get("goals") or 0),
                "own_goals": int(r.get("own_goals") or 0), "shots": int(r.get("shots") or 0),
                "xg": xg, "npxg": max(xg - px, 0.0), "pen_att": pa, "pen_goals": pg, "pen_xg": px,
                "assists": int(r.get("assists") or 0), "xa": float(r.get("xA") or 0),
                "key_passes": int(r.get("key_passes") or 0), "starter": r.get("position") != "Sub",
            })
    return out


def _fetch_match(fx: dict) -> list[dict]:
    d = _get(f"getMatchData/{fx['match_id']}", f"match/{fx['match_id']}")
    return match_rows(fx, d) if d else []


def load(raw: Path, leagues: list[str] | None = None, seasons: list[int] | None = None,
         refresh_current: bool = True, workers: int = 4, verbose: bool = False) -> pd.DataFrame:
    """Charge (et met en cache dans raw/understat/) les lignes joueur-match des saisons demandées.
    Saison la plus récente : seuls les nouveaux matchs joués sont téléchargés."""
    leagues = leagues or list(LEAGUES)
    seasons = seasons or [2024, 2025]
    d = raw / "understat"
    d.mkdir(parents=True, exist_ok=True)
    frames = []
    for lg in leagues:
        for s in seasons:
            f = d / f"{lg}_{s}.parquet"
            cur = pd.read_parquet(f) if f.exists() else pd.DataFrame()
            if f.exists() and not (refresh_current and s == max(seasons)):
                frames.append(cur)
                continue
            fxs = fixtures(league_season(lg, s), lg, s)
            if fxs.empty:
                continue
            done = set(cur["match_id"]) if not cur.empty else set()
            todo = fxs[fxs["played"] & ~fxs["match_id"].isin(done)].to_dict("records")
            if todo:
                with ThreadPoolExecutor(workers) as ex:
                    rows = [r for rs in ex.map(_fetch_match, todo) for r in rs]
                new = pd.DataFrame(rows)
                cur = pd.concat([cur, new], ignore_index=True) if not cur.empty else new
                cur.to_parquet(f, index=False)
            if verbose:
                print(f"{lg} {s} : {len(todo)} nouveaux matchs, {len(cur)} lignes")
            frames.append(cur)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["date", "match_id", "home", "pos_order"]).reset_index(drop=True)


def save_fixtures(raw: Path, leagues: list[str], season: int) -> pd.DataFrame:
    """Calendrier de la saison en cours (matchs à venir compris), pour les prédictions."""
    fx = pd.concat([fixtures(league_season(lg, season), lg, season) for lg in leagues], ignore_index=True)
    (raw / "understat").mkdir(parents=True, exist_ok=True)
    fx.to_parquet(raw / "understat" / f"fixtures_{season}.parquet", index=False)
    return fx


def _gz_json(path: Path) -> dict:
    return json.loads(gzip.decompress(path.read_bytes()))

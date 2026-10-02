"""
live_helpers.py — helpers TESTES (2026-10-02, depuis un conteneur datacenter) pour
cotes live/pré-match et stats joueurs gratuites.

Dépendances : requests, pandas (pip install requests pandas).
Aucune clé requise sauf mention contraire (The Odds API : clé gratuite 500 crédits/mois).

Sources couvertes :
  - Pinnacle "guest" API (arcadia)    : pinnacle_sports, pinnacle_leagues, pinnacle_markets, pinnacle_tennis
  - ESPN (site + core API)            : espn_scoreboard, espn_odds, espn_injuries, espn_prop_bets
  - NHL api-web.nhle.com              : nhl_schedule, nhl_boxscore_players, nhl_player_gamelog, ...
  - MoneyPuck CSV                     : moneypuck_skaters
  - The Odds API (clé gratuite)       : oddsapi_odds, oddsapi_event_props
  - Kambi (Unibet FR / ParionsSport)  : kambi_events
  - Understat                         : understat_league_players
Les fonctions renvoient des pandas.DataFrame "tidy" (1 ligne = 1 sélection/cote).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import time
from typing import Iterable

import pandas as pd
import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_S = requests.Session()
_S.headers.update({"User-Agent": UA, "Accept": "application/json"})


def _get(url: str, params: dict | None = None, headers: dict | None = None,
         timeout: int = 30, retries: int = 2):
    """GET JSON avec petits retries (les APIs publiques renvoient parfois 5xx/timeout)."""
    last = None
    for i in range(retries + 1):
        try:
            r = _S.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code} for {r.url}: {r.text[:200]}")
            if r.status_code in (400, 401, 403, 404):
                break
        except requests.RequestException as e:  # timeout, reset...
            last = e
        time.sleep(1.5 * (i + 1))
    raise last


def american_to_decimal(price) -> float | None:
    """Cote américaine -> décimale (ex. -150 -> 1.667 ; +130 -> 2.30)."""
    if price is None or (isinstance(price, float) and pd.isna(price)):
        return None
    p = float(price)
    if p >= 100:
        return round(1 + p / 100.0, 4)
    if p <= -100:
        return round(1 + 100.0 / abs(p), 4)
    return None


# =============================================================================
# 1. PINNACLE guest API (https://guest.api.arcadia.pinnacle.com/0.1)
#    - Pas d'auth nécessaire au 2026-10-02 (200 sans header).
#    - Clé publique du front pinnacle.com (dans https://www.pinnacle.com/config/app.json,
#      champ api.haywire.apiKey) : envoyée par prudence.
#    - Prix renvoyés en format AMERICAIN -> converti en décimal.
# =============================================================================
PINNACLE_BASE = "https://guest.api.arcadia.pinnacle.com/0.1"
PINNACLE_HEADERS = {"X-API-Key": "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R",
                    "Referer": "https://www.pinnacle.com/", "Origin": "https://www.pinnacle.com"}

# ids vérifiés le 2026-10-02 (sportId, leagueId)
PINNACLE_SPORTS = {"baseball": 3, "basketball": 4, "football": 15, "hockey": 19,
                   "soccer": 29, "tennis": 33}
PINNACLE_LEAGUES = {
    "NBA": 487, "WNBA": 578, "EUROLEAGUE": 382, "FRA_PROA": 414, "FRA_PROB": 415,
    "NHL": 1456, "AHL": 1264, "KHL": 1484,
    "NFL": 889, "NCAAF": 880,
    "MLB": 246,
    "EPL": 1980, "LIGUE1": 2036, "LALIGA": 2196, "SERIEA": 2436, "BUNDESLIGA": 1842,
    "UCL": 2627, "UEL": 2630, "UECL": 214101,
}

# périodes : 0 = match (OT inclus en NHL/NBA/NFL ; 90' en foot), 1 = 1re mi-temps / 1re période
# (hockey: 1,2,3 = périodes ; 6 = temps réglementaire 60' (ML 3 voies)) ; foot/NFL: 3 = 1er quart (NFL)
PINNACLE_PERIODS = {0: "match", 1: "1st_half_or_P1", 2: "2nd_half_or_P2", 3: "Q1_or_P3", 6: "regulation"}


def pinnacle_sports() -> pd.DataFrame:
    d = _get(f"{PINNACLE_BASE}/sports", headers=PINNACLE_HEADERS)
    return pd.DataFrame([{k: s.get(k) for k in ("id", "name", "matchupCount", "primaryMarketType")}
                         for s in d])


def pinnacle_leagues(sport_id: int) -> pd.DataFrame:
    d = _get(f"{PINNACLE_BASE}/sports/{sport_id}/leagues", params={"all": "false"},
             headers=PINNACLE_HEADERS)
    df = pd.DataFrame([{k: l.get(k) for k in ("id", "name", "group", "matchupCount")} for l in d])
    return df.sort_values("matchupCount", ascending=False).reset_index(drop=True)


def _player_from_description(desc: str | None) -> str | None:
    """'Bhayshul Tuten Total Receiving Yards' -> 'Bhayshul Tuten' ;
    'Connor McDavid (Goals)' -> 'Connor McDavid'."""
    if not desc:
        return None
    m = re.match(r"^(.*?)\s+Total\s+", desc)
    if m:
        return m.group(1).strip()
    m = re.match(r"^(.*?)\s*\(", desc)
    if m:
        return m.group(1).strip()
    return None


def pinnacle_markets(league: int | str, include_alternates: bool = False,
                     include_specials: bool = True, periods: Iterable[int] | None = (0,)) -> pd.DataFrame:
    """Cotes Pinnacle d'une ligue -> DataFrame tidy.

    league : id numérique ou clé de PINNACLE_LEAGUES ('NBA', 'NHL', 'EPL', 'LIGUE1', ...)
    include_specials : inclut les 'special' (Player Props, Game Props, Futures, Goalscorer...)
    periods : périodes à garder pour les marchés de match (None = toutes)

    Colonnes : league_id, matchup_id, parent_id, start_time, home, away, kind, category,
    description, player, units, market, period, is_alt, side, selection, line,
    price_american, price_decimal, max_stake, status, is_live, fetched_at
    """
    lid = PINNACLE_LEAGUES.get(str(league).upper(), league) if isinstance(league, str) else league
    matchups = _get(f"{PINNACLE_BASE}/leagues/{lid}/matchups", headers=PINNACLE_HEADERS)
    markets = _get(f"{PINNACLE_BASE}/leagues/{lid}/markets/straight", headers=PINNACLE_HEADERS)
    fetched = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    mu = {m["id"]: m for m in matchups}

    def teams(m):
        # pour un special, l'équipe est dans m['parent']['participants']
        src = m.get("parent") or m
        home = next((p["name"] for p in src.get("participants", []) if p.get("alignment") == "home"), None)
        away = next((p["name"] for p in src.get("participants", []) if p.get("alignment") == "away"), None)
        if home is None and m.get("parentId") in mu:  # enfant tennis "Games"
            return teams(mu[m["parentId"]])
        return home, away

    rows = []
    for mk in markets:
        m = mu.get(mk["matchupId"])
        if m is None:
            continue
        is_special = m.get("type") == "special"
        if is_special and not include_specials:
            continue
        if not include_alternates and mk.get("isAlternate"):
            continue
        if (not is_special) and periods is not None and mk.get("period") not in periods:
            continue
        home, away = teams(m)
        part = {p.get("id"): p.get("name") for p in m.get("participants", [])}
        sp = m.get("special") or {}
        lim = next((l["amount"] for l in mk.get("limits", []) if l.get("type") == "maxRiskStake"), None)
        for pr in mk.get("prices", []):
            sel = pr.get("designation") or part.get(pr.get("participantId"))
            rows.append({
                "league_id": lid,
                "league": (m.get("league") or {}).get("name"),
                "matchup_id": m["id"],
                "parent_id": m.get("parentId"),
                "start_time": m.get("startTime"),
                "home": home, "away": away,
                "kind": "special" if is_special else ("child" if m.get("parentId") else "game"),
                "category": sp.get("category"),
                "description": sp.get("description"),
                "player": _player_from_description(sp.get("description")) if sp.get("category") == "Player Props" else None,
                "units": m.get("units"),
                "market": mk.get("type"),            # moneyline / spread / total / team_total
                "period": mk.get("period"),
                "is_alt": bool(mk.get("isAlternate")),
                "side": mk.get("side"),               # home/away pour team_total
                "selection": sel,                     # home/away/draw/over/under ou nom participant
                "line": pr.get("points"),
                "price_american": pr.get("price"),
                "price_decimal": american_to_decimal(pr.get("price")),
                "max_stake": lim,
                "status": mk.get("status", "open"),
                "is_live": bool(m.get("isLive")),
                "fetched_at": fetched,
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
        df = df.sort_values(["start_time", "matchup_id", "market", "period"]).reset_index(drop=True)
    return df


def pinnacle_player_props(league: int | str) -> pd.DataFrame:
    """Uniquement les 'Player Props' (Over/Under joueur) en format large :
    1 ligne = joueur x stat x ligne, avec cote Over / Under décimale et proba sans marge."""
    df = pinnacle_markets(league, include_alternates=True, include_specials=True, periods=None)
    if df.empty:
        return df
    pp = df[df["category"] == "Player Props"].copy()
    if pp.empty:
        return pp
    wide = pp.pivot_table(index=["start_time", "home", "away", "matchup_id", "player", "units", "line"],
                          columns="selection", values="price_decimal", aggfunc="first").reset_index()
    if {"Over", "Under"} <= set(wide.columns):
        inv = 1 / wide["Over"] + 1 / wide["Under"]
        wide["p_over_novig"] = (1 / wide["Over"]) / inv
        wide["overround"] = inv
    return wide


def pinnacle_tennis(tours: tuple = ("ATP", "WTA"), exclude_challenger_itf: bool = True,
                    include_alternates: bool = False) -> pd.DataFrame:
    """Cotes tennis ATP/WTA (moneyline, handicap jeux/sets, total jeux)."""
    lg = pinnacle_leagues(33)
    mask = lg["name"].str.split().str[0].isin(tours)
    if exclude_challenger_itf:
        mask &= ~lg["name"].str.contains("Challenger|ITF|125K", case=False)
    frames = []
    for lid in lg.loc[mask, "id"]:
        try:
            frames.append(pinnacle_markets(int(lid), include_alternates=include_alternates,
                                           include_specials=False, periods=None))
        except Exception as e:  # ligue vidée entre-temps
            print("skip", lid, e)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def devig_two_way(df: pd.DataFrame, group_cols=("matchup_id", "market", "period", "line", "side")) -> pd.DataFrame:
    """Ajoute p_novig (méthode multiplicative) par groupe de sélections."""
    d = df.copy()
    d["_inv"] = 1 / d["price_decimal"]
    g = [c for c in group_cols if c in d.columns]
    d["_sum"] = d.groupby(g, dropna=False)["_inv"].transform("sum")
    d["p_novig"] = d["_inv"] / d["_sum"]
    return d.drop(columns=["_inv", "_sum"])


# =============================================================================
# 2. ESPN (non documenté, gratuit, sans clé) — cotes DraftKings (+ Bet365 en foot)
#    site API : https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/...
#    core API : https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/...
# =============================================================================
ESPN_LEAGUES = {  # alias -> (sport, league)
    "NBA": ("basketball", "nba"), "WNBA": ("basketball", "wnba"),
    "NHL": ("hockey", "nhl"), "NFL": ("football", "nfl"), "MLB": ("baseball", "mlb"),
    "EPL": ("soccer", "eng.1"), "LIGUE1": ("soccer", "fra.1"), "LALIGA": ("soccer", "esp.1"),
    "SERIEA": ("soccer", "ita.1"), "BUNDESLIGA": ("soccer", "ger.1"), "UCL": ("soccer", "uefa.champions"),
    "ATP": ("tennis", "atp"), "WTA": ("tennis", "wta"),
}
ESPN_SITE = "https://site.api.espn.com/apis/site/v2/sports"
ESPN_CORE = "https://sports.core.api.espn.com/v2/sports"


def _espn_sl(league: str):
    return ESPN_LEAGUES.get(league.upper(), tuple(league.split("/")))


def _odds_num(x):
    try:
        return float(str(x).replace("+", "")) if x not in (None, "", "OFF", "EVEN") else (100.0 if x == "EVEN" else None)
    except ValueError:
        return None


def espn_scoreboard(league: str, date: str | None = None) -> pd.DataFrame:
    """Matchs d'un jour (date 'YYYYMMDD', None = aujourd'hui) + cotes DraftKings open/close.
    1 ligne = 1 match. Les cotes américaines sont converties en décimal."""
    sport, lg = _espn_sl(league)
    params = {"dates": date} if date else None
    d = _get(f"{ESPN_SITE}/{sport}/{lg}/scoreboard", params=params)
    rows = []
    for e in d.get("events", []):
        c = e["competitions"][0]
        comp = {x.get("homeAway"): x for x in c.get("competitors", [])}
        h, a = comp.get("home", {}), comp.get("away", {})
        row = {"event_id": e["id"], "date": e["date"], "name": e.get("name"),
               "status": e["status"]["type"]["name"],
               "home": (h.get("team") or {}).get("displayName"), "away": (a.get("team") or {}).get("displayName"),
               "home_score": h.get("score"), "away_score": a.get("score")}
        odds = (c.get("odds") or [None])[0]
        if odds:
            row["provider"] = odds.get("provider", {}).get("name")
            ml, ps, tot = odds.get("moneyline") or {}, odds.get("pointSpread") or {}, odds.get("total") or {}
            for side in ("home", "away"):
                for when in ("open", "close"):
                    row[f"ml_{side}_{when}"] = american_to_decimal(_odds_num((ml.get(side) or {}).get(when, {}).get("odds")))
                    row[f"spread_{side}_{when}"] = _odds_num((ps.get(side) or {}).get(when, {}).get("line"))
                    row[f"spread_{side}_{when}_odds"] = american_to_decimal(_odds_num((ps.get(side) or {}).get(when, {}).get("odds")))
            for side in ("over", "under"):
                for when in ("open", "close"):
                    t = (tot.get(side) or {}).get(when, {})
                    row[f"total_{when}"] = _odds_num(str(t.get("line", "")).lstrip("ou")) if t.get("line") else row.get(f"total_{when}")
                    row[f"{side}_{when}_odds"] = american_to_decimal(_odds_num(t.get("odds")))
            if odds.get("drawOdds"):
                row["draw_close"] = american_to_decimal(_odds_num(odds["drawOdds"].get("moneyLine")))
        rows.append(row)
    return pd.DataFrame(rows)


def espn_odds(league: str, event_id: str | int) -> pd.DataFrame:
    """Cotes d'un match via la core API (tous providers : DraftKings id 100, Bet365 id 2000 en foot...).
    Fonctionne aussi pour les matchs TERMINÉS (open/close conservés) -> utile pour backtest closing line
    des marchés principaux."""
    sport, lg = _espn_sl(league)
    d = _get(f"{ESPN_CORE}/{sport}/leagues/{lg}/events/{event_id}/competitions/{event_id}/odds")
    rows = []
    for it in d.get("items", []):
        prov = it.get("provider", {})
        base = {"event_id": str(event_id), "provider_id": prov.get("id"), "provider": prov.get("name"),
                "details": it.get("details"), "spread": it.get("spread"), "total": it.get("overUnder"),
                "over_odds": american_to_decimal(it.get("overOdds")), "under_odds": american_to_decimal(it.get("underOdds"))}
        for side in ("home", "away"):
            t = it.get(f"{side}TeamOdds") or {}
            ml = t.get("moneyLine")
            if ml is None and isinstance(t.get("odds"), dict):     # format Bet365 (décimal direct)
                base[f"ml_{side}"] = t["odds"].get("value")
            else:
                base[f"ml_{side}"] = american_to_decimal(ml)
            for when in ("open", "close"):
                w = t.get(when) or {}
                base[f"ml_{side}_{when}"] = (w.get("moneyLine") or {}).get("decimal")
                base[f"spread_{side}_{when}"] = _odds_num((w.get("pointSpread") or {}).get("american"))
        dr = it.get("drawOdds") or {}
        base["ml_draw"] = american_to_decimal(dr.get("moneyLine")) if "moneyLine" in dr else dr.get("value")
        rows.append(base)
    return pd.DataFrame(rows)


_ATHLETE_CACHE: dict = {}


def _espn_athlete_name(ref: str) -> str | None:
    aid = ref.split("/athletes/")[1].split("?")[0]
    if aid not in _ATHLETE_CACHE:
        try:
            j = _get(ref.replace("http://", "https://"), retries=1, timeout=20)
            _ATHLETE_CACHE[aid] = j.get("fullName") or j.get("displayName")
        except Exception:
            _ATHLETE_CACHE[aid] = None
    return _ATHLETE_CACHE[aid]


def espn_prop_bets(league: str, event_id: str | int, provider_id: int = 100,
                   resolve_names: bool = True, max_workers: int = 8) -> pd.DataFrame:
    """Props joueurs/match DraftKings via ESPN core API :
    .../events/{id}/competitions/{id}/odds/{provider}/propBets?limit=1000
    - Les paires Over/Under ne sont PAS étiquetées : l'item n°1 = Over, n°2 = Under (ordre vérifié
      contre Pinnacle sur 10 joueurs WNBA le 2026-10-02) -> colonne 'side_guess'.
    - Milestones ('Points Milestones' 20+, 25+...) et Anytime Goalscorer = une seule cote ('Yes').
    - Après le match les cotes sont retirées (lignes seules) puis l'endpoint passe en 404 -> archiver soi-même.
    """
    sport, lg = _espn_sl(league)
    d = _get(f"{ESPN_CORE}/{sport}/leagues/{lg}/events/{event_id}/competitions/{event_id}/odds/{provider_id}/propBets",
             params={"limit": 1000})
    items = d.get("items", [])
    rows, seen = [], {}
    for it in items:
        aref = (it.get("athlete") or {}).get("$ref")
        aid = aref.split("/athletes/")[1].split("?")[0] if aref else None
        o = it.get("odds") or {}
        tname = (it.get("type") or {}).get("name")
        line = (o.get("total") or {}).get("value")
        key = (aid, tname, line)
        seen[key] = seen.get(key, 0) + 1
        is_ou = tname is not None and tname.startswith(("Total", "1st", "2nd", "3rd", "4th")) and line not in (None, "")
        side = ("Over" if seen[key] == 1 else "Under") if is_ou else "Yes"
        rows.append({"event_id": str(event_id), "athlete_id": aid, "athlete_ref": aref,
                     "team_ref": (it.get("team") or {}).get("$ref"),
                     "market": tname, "market_type_id": (it.get("type") or {}).get("id"),
                     "line": line, "line_open": (o.get("total") or {}).get("open"),
                     "side_guess": side,
                     "price_decimal": float((o.get("decimal") or {}).get("value")) if (o.get("decimal") or {}).get("value") else None,
                     "price_decimal_open": float((o.get("decimal") or {}).get("open")) if (o.get("decimal") or {}).get("open") else None,
                     "price_american": (o.get("american") or {}).get("value"),
                     "last_updated": it.get("lastUpdated")})
    df = pd.DataFrame(rows)
    if resolve_names and not df.empty:
        from concurrent.futures import ThreadPoolExecutor
        refs = df["athlete_ref"].dropna().unique().tolist()
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            names = dict(zip(refs, ex.map(_espn_athlete_name, refs)))
        df["athlete"] = df["athlete_ref"].map(names)
    return df


def espn_injuries(league: str) -> pd.DataFrame:
    """Blessures (NBA/NHL/NFL/MLB...) : site API /injuries."""
    sport, lg = _espn_sl(league)
    d = _get(f"{ESPN_SITE}/{sport}/{lg}/injuries")
    rows = []
    for team in d.get("injuries", []):
        for inj in team.get("injuries", []):
            a = inj.get("athlete") or {}
            rows.append({"team": team.get("displayName"), "athlete": a.get("displayName"),
                         "position": (a.get("position") or {}).get("abbreviation"),
                         "status": inj.get("status"), "date": inj.get("date"),
                         "type": (inj.get("type") or {}).get("description"),
                         "short_comment": inj.get("shortComment")})
    return pd.DataFrame(rows)


def espn_summary(league: str, event_id: str | int) -> dict:
    """Résumé brut d'un match (boxscore joueurs, compositions 'rosters' en foot, pickcenter, odds...)."""
    sport, lg = _espn_sl(league)
    return _get(f"{ESPN_SITE}/{sport}/{lg}/summary", params={"event": event_id})


# =============================================================================
# 3. NHL — api-web.nhle.com (officiel, non documenté, sans clé) + api.nhle.com/stats/rest
#    + MoneyPuck (CSV, non commercial avec crédit) + DailyFaceoff (gardiens partants)
# =============================================================================
NHL_WEB = "https://api-web.nhle.com/v1"
NHL_STATS = "https://api.nhle.com/stats/rest/en"


def nhl_schedule(date: str) -> pd.DataFrame:
    """Matchs de la SEMAINE commençant à `date` (YYYY-MM-DD). gameType 1=pré-saison, 2=saison, 3=playoffs."""
    d = _get(f"{NHL_WEB}/schedule/{date}")
    rows = []
    for day in d.get("gameWeek", []):
        for g in day.get("games", []):
            rows.append({"date": day["date"], "game_id": g["id"], "game_type": g["gameType"],
                         "start_utc": g["startTimeUTC"], "state": g.get("gameState"),
                         "away": g["awayTeam"]["abbrev"], "home": g["homeTeam"]["abbrev"],
                         "away_score": g["awayTeam"].get("score"), "home_score": g["homeTeam"].get("score")})
    return pd.DataFrame(rows)


def nhl_boxscore_players(game_id: int) -> pd.DataFrame:
    """Stats joueurs d'un match (buts, passes, tirs cadrés 'sog', TOI, PP goals, hits, blocks ; gardiens : saves...)."""
    d = _get(f"{NHL_WEB}/gamecenter/{game_id}/boxscore")
    rows = []
    for side in ("awayTeam", "homeTeam"):
        team = d[side]["abbrev"]
        for grp, players in d.get("playerByGameStats", {}).get(side, {}).items():
            for p in players:
                r = {k: v for k, v in p.items() if not isinstance(v, dict)}
                r.update({"name": (p.get("name") or {}).get("default"), "team": team, "group": grp,
                          "home_away": "home" if side == "homeTeam" else "away",
                          "game_id": game_id, "game_date": d.get("gameDate")})
                rows.append(r)
    return pd.DataFrame(rows)


def nhl_player_gamelog(player_id: int, season: int | str = 20252026, game_type: int = 2) -> pd.DataFrame:
    """Game log d'un joueur : /v1/player/{id}/game-log/{season}/{gameType} (season au format 20252026)."""
    d = _get(f"{NHL_WEB}/player/{player_id}/game-log/{season}/{game_type}")
    df = pd.json_normalize(d.get("gameLog", []))
    df["player_id"] = player_id
    return df


def nhl_roster(team: str, season: int | str = 20262027) -> pd.DataFrame:
    d = _get(f"{NHL_WEB}/roster/{team}/{season}")
    rows = []
    for grp in ("forwards", "defensemen", "goalies"):
        for p in d.get(grp, []):
            rows.append({"player_id": p["id"], "first": p["firstName"]["default"], "last": p["lastName"]["default"],
                         "pos": p.get("positionCode"), "number": p.get("sweaterNumber"), "group": grp, "team": team})
    return pd.DataFrame(rows)


def nhl_skater_stats(season: int | str = 20252026, game_type: int = 2, report: str = "summary",
                     limit: int = -1, sort: str = "playerId") -> pd.DataFrame:
    """Stats saison skaters (api.nhle.com/stats/rest). report: summary, realtime (hits, blocks...),
    powerplay, timeonice, shottype... limit=-1 => tout."""
    d = _get(f"{NHL_STATS}/skater/{report}",
             params={"limit": limit, "start": 0, "sort": sort,
                     "cayenneExp": f"seasonId={season} and gameTypeId={game_type}"})
    return pd.DataFrame(d.get("data", []))


def moneypuck_skaters(season: int = 2025, kind: str = "regular", who: str = "skaters") -> pd.DataFrame:
    """MoneyPuck season summary (season = année de début : 2025 = 2025-26). who: skaters/goalies/lines/teams.
    154 colonnes : xGoals, shotsOnGoal, icetime par situation (all, 5on5, 5on4, 4on5, other)."""
    return pd.read_csv(f"https://moneypuck.com/moneypuck/playerData/seasonSummary/{season}/{kind}/{who}.csv",
                       storage_options={"User-Agent": UA})


def moneypuck_player_games(player_id: int, kind: str = "regular") -> pd.DataFrame:
    """Toutes les saisons, match par match, d'un skater (157 colonnes, par situation). Mis à jour quotidiennement."""
    return pd.read_csv(f"https://moneypuck.com/moneypuck/playerData/careers/gameByGame/{kind}/skaters/{player_id}.csv",
                       storage_options={"User-Agent": UA})


def dailyfaceoff_starting_goalies(date: str | None = None) -> pd.DataFrame:
    """Gardiens partants projetés/confirmés (DailyFaceoff, JSON __NEXT_DATA__ de la page).
    date 'YYYY-MM-DD' ou None (aujourd'hui). Statut dans *NewsStrengthName (Confirmed/Likely/Unconfirmed)."""
    url = "https://www.dailyfaceoff.com/starting-goalies/" + (date or "")
    r = _S.get(url, headers={"Accept": "text/html"}, timeout=30)
    r.raise_for_status()
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.S)
    data = json.loads(m.group(1))["props"]["pageProps"]["data"]
    keep = ["homeTeamName", "homeGoalieName", "homeNewsStrengthName", "homeNewsDetails",
            "awayTeamName", "awayGoalieName", "awayNewsStrengthName", "awayNewsDetails"]
    df = pd.DataFrame(data)
    extra = [c for c in ("date", "dateGmt", "time") if c in df.columns]
    return df[[c for c in extra + keep if c in df.columns]]


# =============================================================================
# 4. NBA — cdn.nba.com = 403 depuis IP datacenter, MAIS le bucket S3 d'origine répond (200) :
#    https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/{liveData|staticData}/...
#    stats.nba.com = timeout (bloqué). ESPN gamelog = OK. PDF injury report officiel = OK avec Referer.
# =============================================================================
NBA_S3 = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA"


def nba_schedule(current_season: bool = True) -> pd.DataFrame:
    """Calendrier complet de la saison (scheduleLeagueV2_1.json = saison en cours 2026-27, ~5 Mo).
    gameId : 001=pré-saison, 002=saison régulière, 004=playoffs."""
    d = _get(f"{NBA_S3}/staticData/scheduleLeagueV2_1.json" if current_season
             else f"{NBA_S3}/staticData/scheduleLeagueV2.json", timeout=60)
    rows = []
    for gd in d["leagueSchedule"]["gameDates"]:
        for g in gd["games"]:
            rows.append({"game_id": g["gameId"], "start_utc": g.get("gameDateTimeUTC"),
                         "status": g.get("gameStatusText"),
                         "home": g["homeTeam"].get("teamTricode"), "away": g["awayTeam"].get("teamTricode"),
                         "home_score": g["homeTeam"].get("score"), "away_score": g["awayTeam"].get("score")})
    return pd.DataFrame(rows)


def nba_boxscore_players(game_id: str) -> pd.DataFrame:
    """Boxscore joueurs (points, rebonds, passes, 3PM, minutes, starter...) d'un match NBA (gameId 10 chiffres,
    ex. '0022500900'). Fonctionne pour les saisons passées (testé 2025-26 saison + playoffs)."""
    d = _get(f"{NBA_S3}/liveData/boxscore/boxscore_{game_id}.json")["game"]
    rows = []
    for side in ("homeTeam", "awayTeam"):
        t = d[side]
        for p in t.get("players", []):
            r = {"game_id": d["gameId"], "game_time_utc": d.get("gameTimeUTC"), "team": t["teamTricode"],
                 "opp": d["awayTeam" if side == "homeTeam" else "homeTeam"]["teamTricode"],
                 "home_away": side[:4], "person_id": p["personId"], "player": p.get("name"),
                 "starter": p.get("starter"), "played": p.get("played"), "status": p.get("status"),
                 "not_playing_reason": p.get("notPlayingReason")}
            r.update(p.get("statistics", {}))
            rows.append(r)
    df = pd.DataFrame(rows)
    if "minutes" in df:
        mm = df["minutes"].str.extract(r"PT(\d+)M([\d.]+)S").astype(float)
        df["min"] = mm[0] + mm[1] / 60
    return df


def nba_season_player_logs(season_prefix: str = "00225", n_games: int = 1230, max_workers: int = 8,
                           start: int = 1) -> pd.DataFrame:
    """Construit les game logs de TOUS les joueurs d'une saison régulière en itérant les boxscores S3.
    season_prefix '00225' = saison régulière 2025-26 ; '00226' = 2026-27. ~1230 requêtes (~50 Mo)."""
    from concurrent.futures import ThreadPoolExecutor
    ids = [f"{season_prefix}{i:05d}" for i in range(start, start + n_games)]

    def one(gid):
        try:
            return nba_boxscore_players(gid)
        except Exception:
            return None
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        frames = [f for f in ex.map(one, ids) if f is not None]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def nba_odds_today() -> pd.DataFrame:
    """Cotes du jour publiées par NBA.com (Sportradar : FanDuel, Novibet, ... 2way/spread/total, décimal + ouverture)."""
    d = _get(f"{NBA_S3}/liveData/odds/odds_todaysGames.json")
    rows = []
    for g in d.get("games", []):
        for m in g.get("markets", []):
            for b in m.get("books", []):
                for o in b.get("outcomes", []):
                    rows.append({"game_id": g["gameId"], "market": m.get("name"), "book": b.get("name"),
                                 "country": b.get("countryCode"), "type": o.get("type"),
                                 "line": o.get("spread") or o.get("opening_spread"),
                                 "odds": float(o["odds"]) if o.get("odds") else None,
                                 "opening_odds": float(o["opening_odds"]) if o.get("opening_odds") else None})
    return pd.DataFrame(rows).drop_duplicates()


def nba_injury_report_pdf(stamp: str, out_path: str | None = None) -> bytes:
    """PDF officiel NBA. stamp ex. '2026-03-01_05_00PM' (format 2025-26+, quarts d'heure) ou
    '2025-03-01_05PM' (format jusqu'à 2024-25). Header Referer obligatoire (sinon 403).
    Liste des PDF : https://official.nba.com/nba-injury-report-2025-26-season/ . Parsing : pdfplumber (texte)."""
    r = _S.get(f"https://ak-static.cms.nba.com/referee/injury/Injury-Report_{stamp}.pdf",
               headers={"Referer": "https://official.nba.com/", "Accept": "application/pdf"}, timeout=30)
    r.raise_for_status()
    if out_path:
        open(out_path, "wb").write(r.content)
    return r.content


def espn_athlete_gamelog(league: str, athlete_id: int | str, season: int | None = None) -> pd.DataFrame:
    """Game log ESPN d'un joueur (NBA, NHL, NFL, foot...) :
    https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{league}/athletes/{id}/gamelog?season=YYYY
    (season = année de FIN, ex. 2026 pour 2025-26)."""
    sport, lg = _espn_sl(league)
    d = _get(f"https://site.web.api.espn.com/apis/common/v3/sports/{sport}/{lg}/athletes/{athlete_id}/gamelog",
             params={"season": season} if season else None)
    names = d.get("names", [])
    rows = []
    for st in d.get("seasonTypes", []):
        for cat in st.get("categories", []):
            for ev in cat.get("events", []) or []:
                meta = d.get("events", {}).get(ev["eventId"], {})
                r = {"season_type": st.get("displayName"), "event_id": ev["eventId"],
                     "date": meta.get("gameDate"), "opp": (meta.get("opponent") or {}).get("abbreviation"),
                     "at_vs": meta.get("atVs"), "result": meta.get("gameResult")}
                r.update(dict(zip(names, ev.get("stats", []))))
                rows.append(r)
    return pd.DataFrame(rows)


# =============================================================================
# 5. KALSHI (marché de prédiction US, API publique SANS clé pour les données de marché)
#    -> SEULE source gratuite trouvée de PRIX HISTORIQUES de props joueurs (NHL buteur, NBA points,
#       EPL/Ligue 1 buteur...). Prix = probabilité (0-1) ; cote décimale ~ 1/prix (hors frais).
#    Rate limit agressif (429) : backoff intégré.
# =============================================================================
KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
KALSHI_PROP_SERIES = {
    "NHL_GOAL": "KXNHLGOAL",      # "X: 1+ goals" (=buteur), 2+, 3+
    "NHL_PTS": "KXNHLPTS", "NHL_AST": "KXNHLAST", "NHL_SAVES": "KXNHLSAVE", "NHL_FIRSTGOAL": "KXNHLFIRSTGOAL",
    "NBA_PTS": "KXNBAPTS", "NBA_REB": "KXNBAREB", "NBA_AST": "KXNBAAST", "NBA_3PT": "KXNBA3PT", "NBA_PRA": "KXNBAPRA",
    "EPL_GOAL": "KXEPLGOAL", "EPL_FIRSTGOAL": "KXEPLFIRSTGOAL", "LIGUE1_GOAL": "KXLIGUE1GOAL",
    "LALIGA_GOAL": "KXLALIGAGOAL", "SERIEA_GOAL": "KXSERIEAGOAL", "BUNDESLIGA_GOAL": "KXBUNDESLIGAGOAL",
    "UCL_GOAL": "KXUCLGOAL",
}


def _kalshi_get(path: str, params: dict | None = None, tries: int = 6):
    for i in range(tries):
        r = _S.get(f"{KALSHI}{path}", params=params, timeout=30)
        if r.status_code == 429:
            time.sleep(3 * (i + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"Kalshi 429 persistant sur {path}")


def kalshi_markets(series: str, historical: bool = False, status: str | None = None,
                   max_pages: int = 5, **params) -> pd.DataFrame:
    """Marchés d'une série (ex. 'KXNHLGOAL'). historical=True -> archive (/historical/markets, marchés anciens).
    Colonnes clés : ticker, event_ticker, title ('Tomas Hertl: 1+ goals'), result (yes/no),
    last_price_dollars, yes_bid_dollars, yes_ask_dollars, volume_fp, open_time, close_time."""
    s = KALSHI_PROP_SERIES.get(series, series)
    path = "/historical/markets" if historical else "/markets"
    q = {"series_ticker": s, "limit": 1000, **params}
    if status:
        q["status"] = status
    rows, cursor = [], None
    for _ in range(max_pages):
        if cursor:
            q["cursor"] = cursor
        d = _kalshi_get(path, q)
        rows += d.get("markets", [])
        cursor = d.get("cursor")
        if not cursor or not d.get("markets"):
            break
        time.sleep(1)
    df = pd.DataFrame(rows)
    if not df.empty and "title" in df:
        ext = df["title"].str.extract(r"^(?P<player>.+?):\s*(?P<threshold>\d+)\+\s*(?P<stat>.+)$")
        df = pd.concat([df, ext], axis=1)
    return df


def kalshi_candles(ticker: str, start: str, end: str, period_minutes: int = 60,
                   historical: bool = True, series: str | None = None) -> pd.DataFrame:
    """Historique de prix (bid/ask/trade) d'un marché. start/end ISO ('2026-06-14T04:00:00Z').
    historical=True : /historical/markets/{ticker}/candlesticks (marchés archivés) ;
    sinon /series/{series}/markets/{ticker}/candlesticks (marchés récents)."""
    st = int(pd.Timestamp(start).timestamp()); en = int(pd.Timestamp(end).timestamp())
    path = (f"/historical/markets/{ticker}/candlesticks" if historical
            else f"/series/{series or ticker.split('-')[0]}/markets/{ticker}/candlesticks")
    d = _kalshi_get(path, {"start_ts": st, "end_ts": en, "period_interval": period_minutes})
    rows = []
    for c in d.get("candlesticks", []):
        rows.append({"ts": pd.Timestamp(c["end_period_ts"], unit="s", tz="UTC"),
                     "yes_bid_close": c.get("yes_bid", {}).get("close"), "yes_ask_close": c.get("yes_ask", {}).get("close"),
                     "price_close": (c.get("price") or {}).get("close"), "price_mean": (c.get("price") or {}).get("mean"),
                     "volume": c.get("volume"), "open_interest": c.get("open_interest")})
    df = pd.DataFrame(rows)
    for col in ("yes_bid_close", "yes_ask_close", "price_close", "price_mean", "volume", "open_interest"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if not df.empty:
        df["mid"] = (df["yes_bid_close"] + df["yes_ask_close"]) / 2
        df["decimal_odds_mid"] = 1 / df["mid"]
    return df


# =============================================================================
# 6. FOOT — Understat (endpoints AJAX JSON, header X-Requested-With requis) + compos ESPN
#    Ligues : EPL, La_liga, Bundesliga, Serie_A, Ligue_1, RFPL ; saison = année de début (2026 = 2026-27)
# =============================================================================
UNDERSTAT_H = {"X-Requested-With": "XMLHttpRequest", "Referer": "https://understat.com/"}


def understat_league(league: str = "Ligue_1", season: int = 2026) -> dict:
    """Retourne {'players': DF stats saison joueurs (goals, xG, shots, time, npxG, xA...),
                 'dates': DF matchs (h, a, goals, xG, datetime, forecast), 'teams': dict (historique par match)}."""
    d = _get(f"https://understat.com/getLeagueData/{league}/{season}", headers=UNDERSTAT_H)
    players = pd.DataFrame(d["players"])
    for c in ("games", "time", "goals", "assists", "shots", "key_passes", "npg"):
        players[c] = pd.to_numeric(players[c], errors="coerce")
    for c in ("xG", "xA", "npxG", "xGChain", "xGBuildup"):
        players[c] = pd.to_numeric(players[c], errors="coerce")
    dates = pd.json_normalize(d["dates"])
    return {"players": players, "dates": dates, "teams": d["teams"]}


def understat_player_matches(player_id: int) -> pd.DataFrame:
    """Log match par match d'un joueur (toutes saisons) : goals, shots, xG, time (minutes), npxG, xA, position."""
    d = _get(f"https://understat.com/getPlayerData/{player_id}", headers=UNDERSTAT_H)
    df = pd.DataFrame(d["matches"])
    for c in ("goals", "shots", "time", "assists", "key_passes", "npg", "xG", "xA", "npxG"):
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["player_id"] = player_id
    return df


def understat_match(match_id: int) -> dict:
    """Compositions (rosters h/a : minutes, goals, shots, xG par joueur) + tous les tirs d'un match."""
    d = _get(f"https://understat.com/getMatchData/{match_id}", headers=UNDERSTAT_H)
    ro = pd.concat([pd.DataFrame(d["rosters"][s]).T.assign(side=s) for s in ("h", "a")], ignore_index=True)
    sh = pd.concat([pd.DataFrame(d["shots"][s]).assign(side=s) for s in ("h", "a")], ignore_index=True)
    return {"rosters": ro, "shots": sh}


def espn_soccer_lineups(league: str, event_id: int | str) -> pd.DataFrame:
    """Compos (titulaires/remplaçants) d'un match de foot ESPN via summary -> rosters (dispo ~1h avant)."""
    d = espn_summary(league, event_id)
    rows = []
    for t in d.get("rosters", []) or []:
        for p in t.get("roster", []) or []:
            a = p.get("athlete") or {}
            rows.append({"team": (t.get("team") or {}).get("displayName"), "home_away": t.get("homeAway"),
                         "athlete_id": a.get("id"), "athlete": a.get("displayName"), "starter": p.get("starter"),
                         "position": (p.get("position") or {}).get("abbreviation"), "jersey": p.get("jersey"),
                         "subbed_in": p.get("subbedIn"), "subbed_out": p.get("subbedOut")})
    return pd.DataFrame(rows)


# =============================================================================
# 7. KAMBI (moteur de cotes de Unibet, LeoVegas, 888...) — API publique sans clé
#    https://eu-offering-api.kambicdn.com/offering/v2018/{operator}/...
#    operator 'ub' (Unibet international) et 'kambi' = 200 ; 'ubfr' / 'pafr' = 400
#    ("Unable to resolve customer") -> Unibet FR / ParionsSport non servis par ce CDN.
#    Cotes en millièmes (2250 = 2.25). Libellés FR avec lang=fr_FR.
# =============================================================================
KAMBI = "https://eu-offering-api.kambicdn.com/offering/v2018"


def kambi_events(path: str = "ice_hockey/nhl", operator: str = "ub", lang: str = "fr_FR",
                 market: str = "FR") -> pd.DataFrame:
    """Matchs d'une compétition + offres principales. path ex. 'ice_hockey/nhl', 'basketball/nba',
    'football/france/ligue_1', 'football/england/premier_league', 'tennis/atp'."""
    parts = path.strip("/").split("/")
    parts += ["all"] * (4 - len(parts))  # sport/region/league/all
    d = _get(f"{KAMBI}/{operator}/listView/{'/'.join(parts)}/matches.json",
             params={"lang": lang, "market": market, "useCombined": "true"})
    rows = []
    for ev in d.get("events", []):
        e = ev["event"]
        for b in ev.get("betOffers", []):
            for o in b.get("outcomes", []):
                rows.append({"event_id": e["id"], "event": e["name"], "start": e["start"], "state": e.get("state"),
                             "criterion": b["criterion"].get("label"), "criterion_en": b["criterion"].get("englishLabel"),
                             "outcome": o.get("label"), "line": (o.get("line") / 1000) if o.get("line") is not None else None,
                             "odds": (o.get("odds") / 1000) if o.get("odds") else None})
    return pd.DataFrame(rows)


def kambi_event_offers(event_id: int, operator: str = "ub", lang: str = "fr_FR", market: str = "FR") -> pd.DataFrame:
    """TOUTES les offres d'un match (dont props joueurs : NHL 'Marque - Prolongations incluses' = buteur,
    'Tirs cadrés du joueur', 'Le joueur marque au moins N point(s)' ; foot 'Buteur'... ; NBA 'Points marqués par le joueur')."""
    d = _get(f"{KAMBI}/{operator}/betoffer/event/{event_id}.json",
             params={"lang": lang, "market": market, "includeParticipants": "true"})
    rows = []
    for b in d.get("betOffers", []):
        for o in b.get("outcomes", []):
            rows.append({"event_id": event_id, "criterion": b["criterion"].get("label"),
                         "criterion_en": b["criterion"].get("englishLabel"), "bet_offer_type": (b.get("betOfferType") or {}).get("englishName"),
                         "participant": o.get("participant"), "outcome": o.get("label"), "outcome_en": o.get("englishLabel"),
                         "line": (o.get("line") / 1000) if o.get("line") is not None else None,
                         "odds": (o.get("odds") / 1000) if o.get("odds") else None, "status": o.get("status")})
    return pd.DataFrame(rows)


# =============================================================================
# 8. THE ODDS API (clé gratuite : 500 crédits/mois ; coût = nb marchés x nb régions par appel)
#    Région 'fr' = betclic_fr, netbet_fr, pmu_fr, unibet_fr, winamax_fr. Props = books US uniquement.
#    Testé sans clé valide : 401 (INVALID_KEY / MISSING_KEY).
# =============================================================================
ODDSAPI = "https://api.the-odds-api.com/v4"


def oddsapi_events(sport: str, api_key: str) -> pd.DataFrame:
    """Liste des matchs (GRATUIT, ne consomme pas de crédit)."""
    return pd.DataFrame(_get(f"{ODDSAPI}/sports/{sport}/events", params={"apiKey": api_key}))


def _flatten_oddsapi(events: list) -> pd.DataFrame:
    rows = []
    for e in events:
        for b in e.get("bookmakers", []):
            for m in b.get("markets", []):
                for o in m.get("outcomes", []):
                    rows.append({"event_id": e["id"], "commence_time": e["commence_time"], "home": e["home_team"],
                                 "away": e["away_team"], "bookmaker": b["key"], "market": m["key"],
                                 "last_update": m.get("last_update"), "name": o.get("name"),
                                 "description": o.get("description"), "point": o.get("point"), "price": o.get("price")})
    return pd.DataFrame(rows)


def oddsapi_odds(sport: str, api_key: str, regions: str = "fr", markets: str = "h2h,totals",
                 bookmakers: str | None = None) -> pd.DataFrame:
    """Cotes décimales (ex. sport='icehockey_nhl', 'soccer_france_ligue_one', 'basketball_nba').
    Coût : len(markets) x len(regions) crédits. Imprime les crédits restants."""
    p = {"apiKey": api_key, "markets": markets, "oddsFormat": "decimal"}
    p.update({"bookmakers": bookmakers} if bookmakers else {"regions": regions})
    r = _S.get(f"{ODDSAPI}/sports/{sport}/odds", params=p, timeout=30)
    r.raise_for_status()
    print("credits remaining:", r.headers.get("x-requests-remaining"), "| last cost:", r.headers.get("x-requests-last"))
    return _flatten_oddsapi(r.json())


def oddsapi_event_props(sport: str, event_id: str, api_key: str,
                        markets: str = "player_points", regions: str = "us") -> pd.DataFrame:
    """Props d'UN match (ex. NBA 'player_points,player_rebounds' ; NHL 'player_goal_scorer_anytime,player_shots_on_goal' ;
    foot 'player_goal_scorer_anytime'). Coût = marchés renvoyés x régions."""
    r = _S.get(f"{ODDSAPI}/sports/{sport}/events/{event_id}/odds",
               params={"apiKey": api_key, "regions": regions, "markets": markets, "oddsFormat": "decimal"}, timeout=30)
    r.raise_for_status()
    print("credits remaining:", r.headers.get("x-requests-remaining"), "| last cost:", r.headers.get("x-requests-last"))
    return _flatten_oddsapi([r.json()])


# =============================================================================
# SELF-TEST : python3 live_helpers.py
# =============================================================================
if __name__ == "__main__":
    import traceback
    today = _dt.date.today()
    tests = {
        "pinnacle_markets(NHL)": lambda: pinnacle_markets("NHL"),
        "pinnacle_player_props(NFL)": lambda: pinnacle_player_props("NFL"),
        "pinnacle_tennis()": lambda: pinnacle_tennis(),
        "espn_scoreboard(NHL)": lambda: espn_scoreboard("NHL", today.strftime("%Y%m%d")),
        "espn_injuries(NBA)": lambda: espn_injuries("NBA"),
        "nhl_schedule": lambda: nhl_schedule(today.isoformat()),
        "nhl_player_gamelog(McDavid)": lambda: nhl_player_gamelog(8478402, 20252026),
        "nhl_skater_stats": lambda: nhl_skater_stats(20252026),
        "moneypuck_skaters(2025)": lambda: moneypuck_skaters(2025),
        "dailyfaceoff_starting_goalies": lambda: dailyfaceoff_starting_goalies(),
        "nba_schedule": lambda: nba_schedule(),
        "nba_boxscore_players": lambda: nba_boxscore_players("0022500900"),
        "espn_athlete_gamelog(NBA)": lambda: espn_athlete_gamelog("NBA", 3112335, 2026),
        "understat_league(Ligue_1)": lambda: understat_league("Ligue_1", 2026)["players"],
        "kambi_events(NHL)": lambda: kambi_events("ice_hockey/nhl"),
        "kalshi_markets(NHL_GOAL live)": lambda: kalshi_markets("NHL_GOAL", max_pages=1),
    }
    for name, fn in tests.items():
        try:
            df = fn()
            print(f"OK   {name:40s} {df.shape}")
        except Exception as e:
            print(f"FAIL {name:40s} {type(e).__name__}: {str(e)[:120]}")
    try:
        oddsapi_odds("icehockey_nhl", "INVALID")
    except Exception as e:
        print("OK   oddsapi (sans clé valide -> erreur attendue):", str(e)[:80])

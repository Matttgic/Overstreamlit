"""Chargeurs normalisés pour les sports à deux issues (hors football).

Schéma commun renvoyé par chaque loader :
    date, season, sport, competition, home, away, home_win (bool),
    odds_home, odds_away            (cotes décimales de référence, en général clôture)
    [odds_home_open, odds_away_open, extra…] selon la source
Pour le tennis et le MMA, « home » / « away » = joueur 1 / joueur 2 (ordre neutre).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .tennis import load_dir, to_symmetric


def american_to_decimal(x) -> np.ndarray:
    x = pd.to_numeric(pd.Series(x), errors="coerce").values.astype(float)
    out = np.where(x > 0, 1 + x / 100.0, np.where(x < 0, 1 + 100.0 / np.abs(x), np.nan))
    out[(np.abs(x) < 100) | np.isnan(x)] = np.nan
    return out


def _finish(df: pd.DataFrame, sport: str, competition: str) -> pd.DataFrame:
    df["sport"] = sport
    df["competition"] = df.get("competition", competition)
    df = df.dropna(subset=["date", "home", "away", "home_win"])
    for c in ("odds_home", "odds_away", "odds_home_open", "odds_away_open"):
        if c in df:
            df.loc[(df[c] < 1.01) | (df[c] > 100), c] = np.nan
    return df.sort_values("date", kind="stable").reset_index(drop=True)


# ----------------------------------------------------------------- NBA
NBA_FIX = {"Philadelphia 76ers": "Seventysixers", "Portland Trail Blazers": "Trailblazers",
           "NewJersey": "Nets", "Golden State": "Warriors"}


def load_nba(raw: Path) -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(raw / "nba" / "nba_sbr.json")))
    s = s[s["season"] <= 2020].copy()
    s["home_team"] = s["home_team"].astype(str).replace(NBA_FIX)
    s["away_team"] = s["away_team"].astype(str).replace(NBA_FIX)
    s = s[(s["home_team"] != "0") & (s["away_team"] != "0")]
    a = pd.DataFrame({
        "date": pd.to_datetime(s["date"].astype(int).astype(str), format="%Y%m%d", errors="coerce"),
        "season": s["season"].astype(int), "home": s["home_team"], "away": s["away_team"],
        "home_win": pd.to_numeric(s["home_final"], errors="coerce") > pd.to_numeric(s["away_final"], errors="coerce"),
        "odds_home": american_to_decimal(s["home_close_ml"]),
        "odds_away": american_to_decimal(s["away_close_ml"]),
        "total_line": pd.to_numeric(s["close_over_under"], errors="coerce"),
        "points": pd.to_numeric(s["home_final"], errors="coerce") + pd.to_numeric(s["away_final"], errors="coerce"),
    })
    frames = [a]
    for f in sorted((raw / "nba").glob("nba_20*.csv")):
        w = pd.read_csv(f)
        allstar = w["is_allstar"].astype(bool) if "is_allstar" in w else False
        w = w[~w["round"].isin(["Pre-season", "All Stars"]) & ~allstar]
        w = w[~w["home_team"].astype(str).isin(["Team USA", "West", "East", "5"])]
        y = int(f.stem.split("_")[1])
        if y <= 2020:
            continue

        def nick(t):
            t = str(t)
            return NBA_FIX.get(t, t.split()[-1])
        frames.append(pd.DataFrame({
            "date": pd.to_datetime(w["date"]), "season": y,
            "home": w["home_team"].map(nick), "away": w["away_team"].map(nick),
            "home_win": w["home_win"].astype(bool), "odds_home": w["home_odds"],
            "odds_away": w["away_odds"], "points": w["total_points"]}))
    df = pd.concat(frames, ignore_index=True)
    return _finish(df, "basketball", "NBA")


# ----------------------------------------------------------------- NHL
NHL_FIX = {"Phoenix": "Coyotes", "Arizonas": "Coyotes", "SeattleKraken": "Kraken",
           "WinnipegJets": "Jets", "Tampa Bay": "Lightning", "Tampa": "Lightning",
           "NY Islanders": "Islanders"}


def load_nhl(raw: Path) -> pd.DataFrame:
    s = pd.DataFrame(json.load(open(raw / "nhl" / "nhl_sbr.json")))
    s["home_team"] = s["home_team"].astype(str).replace(NHL_FIX)
    s["away_team"] = s["away_team"].astype(str).replace(NHL_FIX)
    s = s[(s["home_team"] != "0") & (s["away_team"] != "0")]
    hf = pd.to_numeric(s["home_final"], errors="coerce")
    af = pd.to_numeric(s["away_final"], errors="coerce")
    df = pd.DataFrame({
        "date": pd.to_datetime(s["date"].astype(int).astype(str), format="%Y%m%d", errors="coerce"),
        "season": s["season"].astype(int), "home": s["home_team"], "away": s["away_team"],
        "home_win": hf > af,
        "odds_home": american_to_decimal(s["home_close_ml"]),
        "odds_away": american_to_decimal(s["away_close_ml"]),
        "odds_home_open": american_to_decimal(s["home_open_ml"]),
        "odds_away_open": american_to_decimal(s["away_open_ml"]),
    })
    df = df[hf != af]
    return _finish(df, "ice_hockey", "NHL")


# ----------------------------------------------------------------- MLB
def load_mlb(raw: Path) -> pd.DataFrame:
    m = pd.read_parquet(raw / "mlb" / "mlb_oddsportal.parquet")
    d = pd.to_datetime(m["game_date"])
    df = pd.DataFrame({"date": d, "season": d.dt.year, "home": m["home_team_abbr"],
                       "away": m["away_team_abbr"], "home_win": m["Home_Win"].astype(int) == 1,
                       "odds_home": american_to_decimal(m["home_odds"]),
                       "odds_away": american_to_decimal(m["away_odds"])})
    return _finish(df, "baseball", "MLB")


# ----------------------------------------------------------------- NFL
def load_nfl(raw: Path) -> pd.DataFrame:
    g = pd.read_csv(raw / "nfl" / "games.csv")
    g = g.dropna(subset=["home_score", "away_score"])
    g = g[g["home_score"] != g["away_score"]]
    df = pd.DataFrame({"date": pd.to_datetime(g["gameday"]), "season": g["season"],
                       "home": g["home_team"].replace({"OAK": "LV", "SD": "LAC", "STL": "LA"}),
                       "away": g["away_team"].replace({"OAK": "LV", "SD": "LAC", "STL": "LA"}),
                       "home_win": g["home_score"] > g["away_score"],
                       "odds_home": american_to_decimal(g["home_moneyline"]),
                       "odds_away": american_to_decimal(g["away_moneyline"]),
                       "spread_line": g["spread_line"], "margin": g["result"],
                       "neutral": (g["location"] == "Neutral").astype(int),
                       "competition": np.where(g["game_type"] == "REG", "NFL saison", "NFL playoffs")})
    return _finish(df, "american_football", "NFL")


# ----------------------------------------------------------------- MMA
def load_ufc(raw: Path) -> pd.DataFrame:
    u = pd.read_csv(raw / "mma" / "ufc-master.csv", low_memory=False)
    u = u[u["Winner"].isin(["Red", "Blue"])]
    swap = u["R_fighter"] > u["B_fighter"]       # ordre alphabétique neutre
    p1 = np.where(swap, u["B_fighter"], u["R_fighter"])
    p2 = np.where(swap, u["R_fighter"], u["B_fighter"])
    red_won = u["Winner"] == "Red"
    o1 = np.where(swap, american_to_decimal(u["B_odds"]), american_to_decimal(u["R_odds"]))
    o2 = np.where(swap, american_to_decimal(u["R_odds"]), american_to_decimal(u["B_odds"]))
    df = pd.DataFrame({"date": pd.to_datetime(u["date"]), "home": p1, "away": p2,
                       "home_win": np.where(swap, ~red_won, red_won), "odds_home": o1, "odds_away": o2,
                       "neutral": 1, "title_bout": u["title_bout"].astype(bool)})
    df["season"] = df["date"].dt.year
    return _finish(df, "mma", "UFC")


# ----------------------------------------------------------------- tennis
def load_tennis(raw: Path, tour: str = "atp", book: str = "PS") -> pd.DataFrame:
    t = load_dir(raw / "tennis" / tour, tour.upper())
    t = t[t["Comment"].astype(str).str.strip().str.lower().isin(["completed"])]
    s = to_symmetric(t)
    df = pd.DataFrame({"date": s["date"], "season": s["date"].dt.year, "home": s["p1"],
                       "away": s["p2"], "home_win": s["p1_won"], "neutral": 1,
                       "surface": s["surface"], "series": s.get("series"), "round": s["round"],
                       "best_of": s["best_of"], "rank_1": s["rank_1"], "rank_2": s["rank_2"],
                       "competition": s["tournament"]})
    for bk in ("PS", "B365", "Max", "Avg", "BFE"):
        if f"{bk}_1" in s:
            df[f"{bk}_home"] = s[f"{bk}_1"].values
            df[f"{bk}_away"] = s[f"{bk}_2"].values
    df["odds_home"] = df[f"{book}_home"]
    df["odds_away"] = df[f"{book}_away"]
    # référence sharp : Pinnacle, puis Betfair Exchange quand Pinnacle disparaît (02/2026)
    if "BFE_home" in df:
        df["sharp_home"] = df["PS_home"].fillna(df["BFE_home"])
        df["sharp_away"] = df["PS_away"].fillna(df["BFE_away"])
    return _finish(df, "tennis", tour.upper())


def load_international(raw: Path) -> pd.DataFrame:
    r = pd.read_csv(raw / "international" / "results.csv")
    r = r.dropna(subset=["home_score", "away_score"])
    r["date"] = pd.to_datetime(r["date"])
    return r

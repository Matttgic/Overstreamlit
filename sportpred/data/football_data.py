"""Téléchargement et normalisation des données football-data.co.uk.

Source : https://www.football-data.co.uk (Joseph Buchdahl) — résultats, statistiques
de match et cotes (ouverture + clôture) pour ~22 championnats européens depuis 1993,
et 16 championnats « extra » (cotes de clôture uniquement) depuis 2012.

Le fichier normalisé possède un schéma unique, quelle que soit l'époque :
- les colonnes BetBrain historiques (BbAvH, BbMxH, ...) sont renommées en AvgH, MaxH, ...
- toutes les colonnes de cotes sont converties en float, les dates en datetime.
"""
from __future__ import annotations

import io
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = "https://www.football-data.co.uk"

# Championnats « principaux » (cotes d'ouverture + clôture, stats de match)
MAIN_LEAGUES = {
    "E0": "Angleterre Premier League", "E1": "Angleterre Championship",
    "E2": "Angleterre League One", "E3": "Angleterre League Two",
    "EC": "Angleterre National League",
    "SC0": "Écosse Premiership", "SC1": "Écosse Championship",
    "SC2": "Écosse League One", "SC3": "Écosse League Two",
    "D1": "Allemagne Bundesliga", "D2": "Allemagne 2. Bundesliga",
    "I1": "Italie Serie A", "I2": "Italie Serie B",
    "SP1": "Espagne La Liga", "SP2": "Espagne Segunda",
    "F1": "France Ligue 1", "F2": "France Ligue 2",
    "N1": "Pays-Bas Eredivisie", "B1": "Belgique Pro League",
    "P1": "Portugal Liga", "T1": "Turquie Süper Lig", "G1": "Grèce Super League",
}

# Championnats « extra » (un fichier par pays, cotes de clôture uniquement)
EXTRA_LEAGUES = {
    "ARG": "Argentine", "AUT": "Autriche", "BRA": "Brésil", "CHN": "Chine",
    "DNK": "Danemark", "FIN": "Finlande", "IRL": "Irlande", "JPN": "Japon",
    "MEX": "Mexique", "NOR": "Norvège", "POL": "Pologne", "ROU": "Roumanie",
    "RUS": "Russie", "SWE": "Suède", "SWZ": "Suisse", "USA": "USA MLS",
}

# Renommage des anciennes colonnes BetBrain vers le format moderne (2019/20+)
BB_RENAME = {
    "BbAvH": "AvgH", "BbAvD": "AvgD", "BbAvA": "AvgA",
    "BbMxH": "MaxH", "BbMxD": "MaxD", "BbMxA": "MaxA",
    "BbAv>2.5": "Avg>2.5", "BbAv<2.5": "Avg<2.5",
    "BbMx>2.5": "Max>2.5", "BbMx<2.5": "Max<2.5",
    "BbAHh": "AHh", "BbAvAHH": "AvgAHH", "BbAvAHA": "AvgAHA",
    "BbMxAHH": "MaxAHH", "BbMxAHA": "MaxAHA",
    "BbOU": "NbBooksOU", "Bb1X2": "NbBooks1X2", "BbAH": "NbBooksAH",
    "GBH": "GBH",
}

KEEP_BASE = [
    "Div", "Date", "Time", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HTHG", "HTAG", "HTR", "Referee", "HS", "AS", "HST", "AST", "HF", "AF",
    "HC", "AC", "HY", "AY", "HR", "AR", "NbBooks1X2",
]
BOOKS_1X2 = ["B365", "BW", "IW", "LB", "PS", "WH", "VC", "1XB", "BF", "BFE", "Max", "Avg"]
ODDS_COLS = []
for b in BOOKS_1X2:
    for suf in ("H", "D", "A"):
        ODDS_COLS.append(f"{b}{suf}")           # ouverture (vendredi/mardi)
        ODDS_COLS.append(f"{b}C{suf}")          # clôture
for b in ("B365", "P", "Max", "Avg", "BFE"):
    for side in (">2.5", "<2.5"):
        ODDS_COLS.append(f"{b}{side}")
        ODDS_COLS.append(f"{b}C{side}")
for c in ("AHh", "AHCh", "B365AHH", "B365AHA", "PAHH", "PAHA", "MaxAHH", "MaxAHA",
          "AvgAHH", "AvgAHA", "B365CAHH", "B365CAHA", "PCAHH", "PCAHA",
          "MaxCAHH", "MaxCAHA", "AvgCAHH", "AvgCAHA", "PSCH", "PSCD", "PSCA"):
    if c not in ODDS_COLS:
        ODDS_COLS.append(c)


def season_codes(first: int = 2005, last: int = 2025) -> list[str]:
    """Codes de saison football-data : 2005 -> '0506', ..., 2025 -> '2526'."""
    return [f"{y % 100:02d}{(y + 1) % 100:02d}" for y in range(first, last + 1)]


def _get(url: str, retries: int = 4) -> bytes | None:
    for i in range(retries):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            time.sleep(2 ** (i + 1))
    return None


def download_main(raw_dir: Path, leagues=None, seasons=None, force=False) -> list[Path]:
    """Télécharge les CSV des championnats principaux dans raw_dir/main/<saison>/<code>.csv."""
    leagues = leagues or list(MAIN_LEAGUES)
    seasons = seasons or season_codes()
    out = []
    for s in seasons:
        for lg in leagues:
            p = raw_dir / "main" / s / f"{lg}.csv"
            if p.exists() and not force and p.stat().st_size > 0:
                out.append(p)
                continue
            content = _get(f"{BASE}/mmz4281/{s}/{lg}.csv")
            if content:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
                out.append(p)
    return out


def download_extra(raw_dir: Path, countries=None, force=False) -> list[Path]:
    countries = countries or list(EXTRA_LEAGUES)
    out = []
    for c in countries:
        p = raw_dir / "extra" / f"{c}.csv"
        if p.exists() and not force and p.stat().st_size > 0:
            out.append(p)
            continue
        content = _get(f"{BASE}/new/{c}.csv")
        if content:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content)
            out.append(p)
    return out


def _read_csv_bytes(b: bytes) -> pd.DataFrame:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(b), encoding=enc, on_bad_lines="skip", low_memory=False)
        except UnicodeDecodeError:
            continue
    raise ValueError("encodage illisible")


def _parse_dates(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    d = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    m = d.isna()
    if m.any():
        d[m] = pd.to_datetime(s[m], format="%d/%m/%y", errors="coerce")
    return d


def load_main_file(path: Path) -> pd.DataFrame:
    df = _read_csv_bytes(path.read_bytes())
    df = df.rename(columns=lambda c: str(c).strip())
    df = df.rename(columns=BB_RENAME)
    df = df.dropna(subset=["HomeTeam", "AwayTeam"]) if "HomeTeam" in df else df.iloc[0:0]
    if df.empty:
        return df
    keep = [c for c in KEEP_BASE + ODDS_COLS if c in df.columns]
    df = df[keep].copy()
    df["Date"] = _parse_dates(df["Date"])
    df["Season"] = path.parent.name
    df["League"] = path.stem
    for c in df.columns:
        if c in ODDS_COLS or c in ("FTHG", "FTAG", "HTHG", "HTAG", "HS", "AS", "HST", "AST",
                                    "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR", "NbBooks1X2"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    # cotes aberrantes (<1.01) -> NaN
    for c in ODDS_COLS:
        if c in df.columns and c not in ("AHh", "AHCh"):
            df.loc[df[c] < 1.01, c] = np.nan
    return df


def load_extra_file(path: Path) -> pd.DataFrame:
    df = _read_csv_bytes(path.read_bytes())
    df = df.rename(columns=lambda c: str(c).strip())
    df = df.rename(columns={"Home": "HomeTeam", "Away": "AwayTeam", "HG": "FTHG",
                            "AG": "FTAG", "Res": "FTR"})
    df["Date"] = _parse_dates(df["Date"])
    df["League"] = path.stem
    # saison : '2012/2013' ou '2012' -> on garde l'année de début
    df["Season"] = df["Season"].astype(str).str[:4]
    for c in df.columns:
        if c.startswith(("PSC", "MaxC", "AvgC", "B365C", "BFEC")) or c in ("FTHG", "FTAG"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    keep = [c for c in ["League", "Country", "Season", "Date", "Time", "HomeTeam", "AwayTeam",
                        "FTHG", "FTAG", "FTR", "PSCH", "PSCD", "PSCA", "MaxCH", "MaxCD", "MaxCA",
                        "AvgCH", "AvgCD", "AvgCA", "B365CH", "B365CD", "B365CA",
                        "BFECH", "BFECD", "BFECA"] if c in df.columns]
    return df[keep]


def build_dataset(raw_dir: Path, out_dir: Path) -> dict[str, Path]:
    """Assemble tous les fichiers bruts en deux parquet normalisés."""
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = [load_main_file(p) for p in sorted((raw_dir / "main").glob("*/*.csv"))]
    main = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    main = main.dropna(subset=["Date", "FTHG", "FTAG"])
    main["FTHG"] = main["FTHG"].astype(int)
    main["FTAG"] = main["FTAG"].astype(int)
    main = main.sort_values(["Date", "League"]).reset_index(drop=True)
    main["MatchId"] = (main["League"] + "_" + main["Date"].dt.strftime("%Y%m%d") + "_"
                       + main["HomeTeam"].str.replace(" ", "") + "_"
                       + main["AwayTeam"].str.replace(" ", ""))
    paths = {"main": out_dir / "football_main.parquet"}
    main.to_parquet(paths["main"], index=False)

    extra_files = sorted((raw_dir / "extra").glob("*.csv"))
    if extra_files:
        extra = pd.concat([load_extra_file(p) for p in extra_files], ignore_index=True)
        extra = extra.dropna(subset=["Date", "FTHG", "FTAG"])
        extra = extra.sort_values(["Date", "League"]).reset_index(drop=True)
        paths["extra"] = out_dir / "football_extra.parquet"
        extra.to_parquet(paths["extra"], index=False)
    return paths


def load(processed_dir: Path, which: str = "main") -> pd.DataFrame:
    return pd.read_parquet(processed_dir / f"football_{which}.parquet")

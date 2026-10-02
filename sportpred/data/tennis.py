"""Données tennis au format tennis-data.co.uk (ATP & WTA, résultats + cotes).

Colonnes d'origine : Date, Tournament, Series/Tier, Surface, Round, Best of, Winner,
Loser, WRank, LRank, WPts, LPts, Wsets, Lsets, Comment, B365W/L, PSW/L, MaxW/L, AvgW/L…

Le format « vainqueur / perdant » est dangereux : il encode le résultat. On le
convertit en format symétrique « joueur 1 / joueur 2 » (ordre alphabétique) pour que
les modèles et les stratégies ne puissent pas exploiter l'ordre des colonnes.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ODDS_BOOKS = ["B365", "PS", "Max", "Avg", "BFE", "EX", "LB", "SJ", "UB", "CB", "IW", "GB", "SB"]


def read_any(path: Path) -> pd.DataFrame:
    if path.suffix == ".csv":
        return pd.read_csv(path, low_memory=False)
    return pd.read_excel(path)


def load_dir(directory: Path, tour: str = "ATP") -> pd.DataFrame:
    frames = []
    for p in sorted(directory.glob("*")):
        if p.suffix not in (".xls", ".xlsx", ".csv"):
            continue
        try:
            d = read_any(p)
        except Exception as e:  # noqa: BLE001
            print("illisible", p, e)
            continue
        d["source_file"] = p.name
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"Tier": "Series"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Winner", "Loser"])
    df["tour"] = tour
    for c in ["WRank", "LRank", "WPts", "LPts", "Wsets", "Lsets", "Best of"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    for b in ODDS_BOOKS:
        for s in ("W", "L"):
            c = f"{b}{s}"
            if c in df:
                df[c] = pd.to_numeric(df[c], errors="coerce")
                df.loc[df[c] < 1.005, c] = np.nan
    df["Winner"] = df["Winner"].astype(str).str.strip()
    df["Loser"] = df["Loser"].astype(str).str.strip()
    return df.sort_values("Date", kind="stable").reset_index(drop=True)


def to_symmetric(df: pd.DataFrame) -> pd.DataFrame:
    """Format joueur 1 / joueur 2 (p1 = premier par ordre alphabétique)."""
    swap = df["Winner"] > df["Loser"]
    out = pd.DataFrame(index=df.index)
    out["date"] = df["Date"]
    for c in ["tour", "Tournament", "Series", "Surface", "Round", "Best of", "Court", "Comment"]:
        if c in df:
            out[c.lower().replace(" ", "_")] = df[c]
    out["p1"] = np.where(swap, df["Loser"], df["Winner"])
    out["p2"] = np.where(swap, df["Winner"], df["Loser"])
    out["p1_won"] = ~swap
    for a, b in (("WRank", "LRank"), ("WPts", "LPts")):
        if a in df:
            out[f"{a[1:].lower()}_1"] = np.where(swap, df[b], df[a])
            out[f"{a[1:].lower()}_2"] = np.where(swap, df[a], df[b])
    for bk in ODDS_BOOKS:
        if f"{bk}W" in df:
            out[f"{bk}_1"] = np.where(swap, df[f"{bk}L"], df[f"{bk}W"])
            out[f"{bk}_2"] = np.where(swap, df[f"{bk}W"], df[f"{bk}L"])
    return out

"""Construction des variables explicatives (sans fuite d'information).

Toutes les statistiques d'équipe sont calculées avec un décalage d'un match
(shift(1)) : la variable d'un match n'utilise que les matchs strictement antérieurs.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from .betting.odds import devig


def country_of(league: str) -> str:
    if league == "EC":
        return "E"
    return re.sub(r"\d+$", "", league)


def add_basics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Country"] = df["League"].map(country_of)
    gd = df["FTHG"] - df["FTAG"]
    df["y"] = np.where(gd > 0, 0, np.where(gd == 0, 1, 2))     # 0=H, 1=D, 2=A
    df["over25"] = (df["FTHG"] + df["FTAG"] > 2.5).astype(int)
    df["btts"] = ((df["FTHG"] > 0) & (df["FTAG"] > 0)).astype(int)
    df["won_H"] = df["y"] == 0
    df["won_D"] = df["y"] == 1
    df["won_A"] = df["y"] == 2
    df["won_O"] = df["over25"] == 1
    df["won_U"] = df["over25"] == 0
    return df


def add_market_probs(df: pd.DataFrame, method: str = "power") -> pd.DataFrame:
    """Probabilités implicites sans marge pour plusieurs jeux de cotes."""
    df = df.copy()
    sets = {
        "ps": ("PSH", "PSD", "PSA"), "psc": ("PSCH", "PSCD", "PSCA"),
        "avg": ("AvgH", "AvgD", "AvgA"), "avgc": ("AvgCH", "AvgCD", "AvgCA"),
        "b365": ("B365H", "B365D", "B365A"), "bw": ("BWH", "BWD", "BWA"),
        "max": ("MaxH", "MaxD", "MaxA"),
    }
    for name, cols in sets.items():
        if not all(c in df for c in cols):
            continue
        o = df[list(cols)].values
        ok = ~np.isnan(o).any(axis=1)
        p = np.full(o.shape, np.nan)
        if ok.any():
            p[ok] = devig(o[ok], method)
        df[[f"mk_{name}_ph", f"mk_{name}_pd", f"mk_{name}_pa"]] = p
        df[f"mk_{name}_margin"] = np.where(ok, np.nansum(1 / o, axis=1) - 1, np.nan)
        # cotes équitables (pour la CLV)
        df[[f"fair_{name}_H", f"fair_{name}_D", f"fair_{name}_A"]] = 1 / p
    for name, cols in {"ou_p": ("P>2.5", "P<2.5"), "ou_pc": ("PC>2.5", "PC<2.5"),
                       "ou_avg": ("Avg>2.5", "Avg<2.5"), "ou_avgc": ("AvgC>2.5", "AvgC<2.5")}.items():
        if not all(c in df for c in cols):
            continue
        o = df[list(cols)].values
        ok = ~np.isnan(o).any(axis=1)
        p = np.full(o.shape, np.nan)
        if ok.any():
            p[ok] = devig(o[ok], method)
        df[[f"mk_{name}_over", f"mk_{name}_under"]] = p
        df[[f"fair_{name}_O", f"fair_{name}_U"]] = 1 / p
    return df


def team_form(df: pd.DataFrame, spans=(5, 20)) -> pd.DataFrame:
    """Moyennes mobiles exponentielles (EWMA) par équipe, décalées d'un match."""
    stats_home = {"gf": "FTHG", "ga": "FTAG", "sf": "HS", "sa": "AS", "stf": "HST",
                  "sta": "AST", "cf": "HC", "ca": "AC"}
    stats_away = {"gf": "FTAG", "ga": "FTHG", "sf": "AS", "sa": "HS", "stf": "AST",
                  "sta": "HST", "cf": "AC", "ca": "HC"}
    h = pd.DataFrame({"idx": df.index, "Date": df["Date"].values,
                      "team": (df["Country"] + "|" + df["HomeTeam"]).values, "is_home": 1})
    a = pd.DataFrame({"idx": df.index, "Date": df["Date"].values,
                      "team": (df["Country"] + "|" + df["AwayTeam"]).values, "is_home": 0})
    for k, c in stats_home.items():
        h[k] = df[c].values if c in df else np.nan
    for k, c in stats_away.items():
        a[k] = df[c].values if c in df else np.nan
    pts_h = np.select([df["FTHG"] > df["FTAG"], df["FTHG"] == df["FTAG"]], [3, 1], 0)
    h["pts"] = pts_h
    a["pts"] = np.select([df["FTAG"] > df["FTHG"], df["FTHG"] == df["FTAG"]], [3, 1], 0)
    long = pd.concat([h, a], ignore_index=True).sort_values(["team", "Date", "is_home"],
                                                           kind="stable").reset_index(drop=True)
    cols = ["gf", "ga", "sf", "sa", "stf", "sta", "cf", "ca", "pts"]
    g = long.groupby("team", sort=False)
    feats = {}
    for span in spans:
        sh = g[cols].shift(1)
        ew = sh.groupby(long["team"]).transform(lambda s: s.ewm(span=span, min_periods=3).mean())
        for c in cols:
            feats[f"{c}_ew{span}"] = ew[c].values
    long["n_played"] = g.cumcount()
    long["rest_days"] = g["Date"].diff().dt.days.values
    F = pd.DataFrame(feats, index=long.index)
    F["n_played"] = long["n_played"].values
    F["rest_days"] = long["rest_days"].values
    F["idx"] = long["idx"].values
    F["is_home"] = long["is_home"].values
    Fh = F[F["is_home"] == 1].set_index("idx").drop(columns="is_home").add_prefix("h_")
    Fa = F[F["is_home"] == 0].set_index("idx").drop(columns="is_home").add_prefix("a_")
    return Fh.join(Fa)

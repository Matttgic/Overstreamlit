"""Elo générique pour sports à deux issues (NBA, NHL, NFL, MLB, tennis, MMA…).

- avantage du terrain `hfa` (points Elo) sauf si la colonne `neutral` vaut 1 ;
- K fixe ou dynamique (FiveThirtyEight : K = 250 / (n + 5)^0.4, utile au tennis/MMA où
  le nombre de matchs par joueur varie énormément) ;
- multiplicateur de marge optionnel (538 NBA/NFL) ;
- régression vers la moyenne entre saisons (`regress`, ex. 0.25 en NBA/NFL).
- Elo par surface pour le tennis (`surface_col`), mélangé à l'Elo global.

La note utilisée pour un match est toujours celle d'AVANT le match.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd


def two_outcome_elo(df: pd.DataFrame, k: float = 20.0, hfa: float = 0.0, regress: float = 0.0,
                    dynamic_k: bool = False, margin_col: str | None = None,
                    surface_col: str | None = None, init: float = 1500.0) -> pd.DataFrame:
    r = defaultdict(lambda: init)
    n = defaultdict(int)
    rs = defaultdict(lambda: init)
    ns = defaultdict(int)
    last_season = {}
    H, A = df["home"].values, df["away"].values
    W = df["home_win"].values.astype(bool)
    S = df["season"].values
    NEU = df["neutral"].values if "neutral" in df else np.zeros(len(df))
    M = df[margin_col].values if margin_col else None
    SF = df[surface_col].values if surface_col else None
    out = np.full((len(df), 4), np.nan)
    order = np.argsort(df["date"].values, kind="stable")

    def kf(cnt):
        return 250.0 / (cnt + 5) ** 0.4 if dynamic_k else k

    for i in order:
        h, a = H[i], A[i]
        for t in (h, a):
            if regress and last_season.get(t) is not None and last_season[t] != S[i]:
                r[t] = r[t] * (1 - regress) + init * regress
            last_season[t] = S[i]
        adv = 0.0 if NEU[i] else hfa
        d = r[h] + adv - r[a]
        e = 1.0 / (1.0 + 10 ** (-d / 400.0))
        out[i, 0], out[i, 1] = d, e
        mult = 1.0
        if M is not None and not np.isnan(M[i]):
            mov = abs(M[i])
            # 538 : ln(MOV+1) * 2.2 / (0.001 * écart_elo_vainqueur + 2.2)
            dw = d if W[i] else -d
            mult = np.log(mov + 1) * 2.2 / (0.001 * dw + 2.2)
        res = 1.0 if W[i] else 0.0
        r[h] += kf(n[h]) * mult * (res - e)
        r[a] -= kf(n[a]) * mult * (res - e)
        n[h] += 1
        n[a] += 1
        if SF is not None:
            s = SF[i]
            ds = rs[(h, s)] - rs[(a, s)]
            es = 1.0 / (1.0 + 10 ** (-ds / 400.0))
            out[i, 2], out[i, 3] = ds, es
            rs[(h, s)] += kf(ns[(h, s)]) * (res - es)
            rs[(a, s)] -= kf(ns[(a, s)]) * (res - es)
            ns[(h, s)] += 1
            ns[(a, s)] += 1
    res = pd.DataFrame(out, index=df.index, columns=["elo_diff", "elo_p", "elo_surf_diff", "elo_surf_p"])
    res["n_home"] = 0
    if SF is None:
        res = res.drop(columns=["elo_surf_diff", "elo_surf_p"])
    return res.drop(columns="n_home")

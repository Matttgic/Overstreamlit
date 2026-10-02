"""Systèmes de notation Elo (génériques, multi-sports).

Football : variante « World Football Elo » (eloratings.net) avec avantage du terrain
et multiplicateur selon l'écart de buts, cf. Hvattum & Arntzen (2010), IJF 26(3).
Tennis / sports sans nul : Elo classique avec K dynamique (FiveThirtyEight :
K = 250 / (n_matchs + 5)^0.4), cf. Kovalchik (2016), JQAS.

Toutes les notes sont calculées en un seul passage chronologique : la note utilisée
pour prédire un match est TOUJOURS celle d'avant le match (pas de fuite d'information).
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd


def goal_multiplier(gd: np.ndarray | int) -> np.ndarray:
    gd = np.abs(np.asarray(gd))
    return np.where(gd <= 1, 1.0, np.where(gd == 2, 1.5, (11.0 + gd) / 8.0))


def football_elo(df: pd.DataFrame, k: float = 20.0, hfa: float = 65.0,
                 init: float = 1500.0, group_col: str | None = "Country",
                 new_team_quantile: float = 0.2, season_regress: float = 0.0,
                 home="HomeTeam", away="AwayTeam", hg="FTHG", ag="FTAG",
                 date="Date") -> pd.DataFrame:
    """Calcule les notes Elo avant-match pour chaque match.

    Retourne un DataFrame (même index que df) : elo_h, elo_a, elo_diff (incl. avantage
    terrain), elo_raw_ph (proba Elo brute de victoire domicile, nul compté 0.5).
    Les nouvelles équipes démarrent au quantile `new_team_quantile` des notes de leur
    groupe (ex. pays), ce qui modélise l'arrivée d'un promu.
    """
    order = df.sort_values(date, kind="stable").index
    ratings: dict = {}
    group_ratings = defaultdict(dict)
    last_season: dict = {}
    eh = np.empty(len(df))
    ea = np.empty(len(df))
    pos = {ix: i for i, ix in enumerate(df.index)}
    H = df[home].values
    A = df[away].values
    G = df[group_col].values if group_col else np.zeros(len(df))
    S = df["Season"].values if "Season" in df else np.zeros(len(df))
    GH = df[hg].values
    GA = df[ag].values

    def get(team, grp, season):
        key = (grp, team)
        if key not in ratings:
            pool = list(group_ratings[grp].values())
            ratings[key] = float(np.quantile(pool, new_team_quantile)) if len(pool) >= 10 else init
            group_ratings[grp][team] = ratings[key]
        if season_regress and last_season.get(key) not in (None, season):
            pool = np.mean(list(group_ratings[grp].values()))
            ratings[key] = ratings[key] * (1 - season_regress) + pool * season_regress
        last_season[key] = season
        return ratings[key]

    for ix in order:
        i = pos[ix]
        g = G[i]
        rh = get(H[i], g, S[i])
        ra = get(A[i], g, S[i])
        eh[i], ea[i] = rh, ra
        exp_h = 1.0 / (1.0 + 10 ** (-(rh + hfa - ra) / 400.0))
        gd = GH[i] - GA[i]
        res = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)
        delta = k * goal_multiplier(gd) * (res - exp_h)
        ratings[(g, H[i])] = rh + delta
        ratings[(g, A[i])] = ra - delta
        group_ratings[g][H[i]] = rh + delta
        group_ratings[g][A[i]] = ra - delta

    out = pd.DataFrame(index=df.index)
    out["elo_h"] = eh
    out["elo_a"] = ea
    out["elo_diff"] = eh + hfa - ea
    out["elo_raw_ph"] = 1.0 / (1.0 + 10 ** (-out["elo_diff"] / 400.0))
    return out


def binary_elo(df: pd.DataFrame, p1="winner", p2="loser", date="date",
               k_mode: str = "538", k: float = 32.0, init: float = 1500.0,
               surface_col: str | None = None, surface_weight: float = 0.5) -> pd.DataFrame:
    """Elo pour sports sans match nul (tennis, NBA, NHL en temps réglementaire non, MMA...).

    `p1` est le vainqueur, `p2` le perdant (format des bases tennis). Retourne pour
    chaque ligne les notes avant-match et la probabilité que p1 gagne.
    Si `surface_col` est fourni, calcule aussi un Elo par surface et une note mixte
    (Angelini et al. 2022 / Tennis Abstract).
    """
    order = df.sort_values(date, kind="stable").index
    r = defaultdict(lambda: init)
    n = defaultdict(int)
    rs = defaultdict(lambda: init)
    ns = defaultdict(int)
    out = np.zeros((len(df), 4))
    pos = {ix: i for i, ix in enumerate(df.index)}
    W = df[p1].values
    L = df[p2].values
    SF = df[surface_col].values if surface_col else None

    def kf(cnt):
        return 250.0 / (cnt + 5) ** 0.4 if k_mode == "538" else k

    for ix in order:
        i = pos[ix]
        w, l = W[i], L[i]
        rw, rl = r[w], r[l]
        ew = 1.0 / (1.0 + 10 ** ((rl - rw) / 400.0))
        out[i, 0], out[i, 1], out[i, 2] = rw, rl, ew
        r[w] = rw + kf(n[w]) * (1 - ew)
        r[l] = rl - kf(n[l]) * (1 - ew)
        n[w] += 1
        n[l] += 1
        if SF is not None:
            s = SF[i]
            sw, sl = rs[(w, s)], rs[(l, s)]
            mw = (1 - surface_weight) * rw + surface_weight * sw
            ml = (1 - surface_weight) * rl + surface_weight * sl
            out[i, 3] = 1.0 / (1.0 + 10 ** ((ml - mw) / 400.0))
            es = 1.0 / (1.0 + 10 ** ((sl - sw) / 400.0))
            rs[(w, s)] = sw + kf(ns[(w, s)]) * (1 - es)
            rs[(l, s)] = sl - kf(ns[(l, s)]) * (1 - es)
            ns[(w, s)] += 1
            ns[(l, s)] += 1
    res = pd.DataFrame(out, index=df.index, columns=["elo_w", "elo_l", "p_elo", "p_elo_surface"])
    if SF is None:
        res = res.drop(columns="p_elo_surface")
    return res

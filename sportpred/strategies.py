"""Catalogue de stratégies de paris testables (football 1N2 et Over/Under 2.5).

Chaque stratégie est une fonction qui reçoit le DataFrame de prédictions et renvoie
un DataFrame de paris candidats SÉLECTIONNÉS (colonnes : date, match, league,
selection, p, odds, won, ev, clv…). La simulation de bankroll est faite ensuite par
`sportpred.backtest.engine.simulate`.

Familles :
- « biais »      : aucun modèle, on parie systématiquement une catégorie (favori, nul…)
- « modèle »     : value betting avec les probabilités d'un modèle statistique
- « sharp »      : value betting avec les probabilités du marché « sharp » (Pinnacle,
                   Betfair Exchange) contre les cotes d'un bookmaker « soft »
- « consensus »  : Kaunitz, Zhong & Kreiner (2017) — moyenne du marché vs meilleure cote
- « hybride »    : mélange modèle / marché (rétrécissement vers le marché)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .backtest.engine import candidate_bets

OUT = ["H", "D", "A"]


def odds_cols(book: str) -> list[str]:
    """book : 'Avg', 'Max', 'PS', 'B365', 'BW', 'AvgC', 'MaxC', 'PSC', 'BFE'…"""
    return [f"{book}{o}" for o in OUT]


def candidates_1x2(df: pd.DataFrame, prob_prefix: str, book: str,
                   close_ref: str = "psc") -> pd.DataFrame:
    """Paris candidats 1N2 : proba `prob_prefix`_ph/pd/pa contre les cotes `book`."""
    pcols = [f"{prob_prefix}_ph", f"{prob_prefix}_pd", f"{prob_prefix}_pa"]
    ocols = odds_cols(book)
    if not all(c in df for c in pcols + ocols):
        return pd.DataFrame()
    fair = [f"fair_{close_ref}_{o}" for o in OUT]
    fair = fair if all(c in df for c in fair) else None
    c = candidate_bets(df, pcols, ocols, ["won_H", "won_D", "won_A"], fair, OUT)
    c["season"] = df.loc[c.index, "SeasonKey"].values
    return c


def candidates_ou(df: pd.DataFrame, prob_col: str, book: str, close_ref: str = "ou_pc"):
    """Paris candidats Over/Under 2.5. book : 'Avg', 'Max', 'P', 'B365', 'AvgC'…"""
    if prob_col not in df or f"{book}>2.5" not in df:
        return pd.DataFrame()
    d = df.assign(_p_over=df[prob_col], _p_under=1 - df[prob_col])
    fair = [f"fair_{close_ref}_O", f"fair_{close_ref}_U"]
    fair = fair if all(c in df for c in fair) else None
    c = candidate_bets(d, ["_p_over", "_p_under"], [f"{book}>2.5", f"{book}<2.5"],
                       ["won_O", "won_U"], fair, ["Over2.5", "Under2.5"])
    c["season"] = df.loc[c.index, "SeasonKey"].values
    return c


def select_value(c: pd.DataFrame, min_ev: float = 0.03, max_ev: float = 1.0,
                 min_odds: float = 1.01, max_odds: float = 100.0,
                 selections: list[str] | None = None) -> pd.DataFrame:
    if c.empty:
        return c
    m = (c["ev"] >= min_ev) & (c["ev"] <= max_ev) & (c["odds"] >= min_odds) & (c["odds"] <= max_odds)
    if selections:
        m &= c["selection"].isin(selections)
    return c[m]


def blend(df: pd.DataFrame, model: str, market: str, w: float, name: str) -> pd.DataFrame:
    """p = w·p_modèle + (1-w)·p_marché (rétrécissement vers le marché)."""
    df = df.copy()
    for s in ("ph", "pd", "pa"):
        df[f"{name}_{s}"] = w * df[f"{model}_{s}"] + (1 - w) * df[f"mk_{market}_{s}"]
    return df


def logit_blend(df: pd.DataFrame, model: str, market: str, w: float, name: str) -> pd.DataFrame:
    """Mélange en espace log (pool logarithmique) : p ∝ p_mod^w · p_mkt^(1-w)."""
    df = df.copy()
    pm = df[[f"{model}_{s}" for s in ("ph", "pd", "pa")]].values
    pk = df[[f"mk_{market}_{s}" for s in ("ph", "pd", "pa")]].values
    lp = w * np.log(np.clip(pm, 1e-9, 1)) + (1 - w) * np.log(np.clip(pk, 1e-9, 1))
    p = np.exp(lp)
    p /= p.sum(axis=1, keepdims=True)
    df[[f"{name}_ph", f"{name}_pd", f"{name}_pa"]] = p
    return df


def kaunitz_probs(df: pd.DataFrame, alpha: float = 0.034, book: str = "Avg",
                  name: str = "kz") -> pd.DataFrame:
    """Consensus de Kaunitz et al. (2017) : p = 1/cote_moyenne - α."""
    df = df.copy()
    for o, s in zip(OUT, ("ph", "pd", "pa")):
        df[f"{name}_{s}"] = 1.0 / df[f"{book}{o}"] - alpha
    return df

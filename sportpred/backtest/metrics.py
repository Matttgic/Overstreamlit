"""Métriques d'évaluation des prédictions et des stratégies de paris.

Précision probabiliste :
- RPS (Ranked Probability Score) — Constantinou & Fenton (2012) : score propre et
  sensible à l'ordre (domicile < nul < extérieur), standard pour le football.
- Log-loss (entropie croisée), Brier multi-classes, calibration.

Rentabilité :
- ROI, profit, drawdown, intervalle de confiance bootstrap du ROI,
- p-value (H0 : ROI = -marge, i.e. pas de compétence) par bootstrap,
- CLV (Closing Line Value) : rapport cote prise / cote de clôture équitable (Pinnacle),
  meilleur indicateur de compétence à court terme (beaucoup moins bruité que le ROI).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rps(probs: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    """RPS par match. probs (n, K) ordonnées ; outcome entier 0..K-1."""
    probs = np.asarray(probs, float)
    k = probs.shape[1]
    obs = np.zeros_like(probs)
    obs[np.arange(len(outcome)), np.asarray(outcome, int)] = 1.0
    cp = np.cumsum(probs, axis=1)[:, :-1]
    co = np.cumsum(obs, axis=1)[:, :-1]
    return np.sum((cp - co) ** 2, axis=1) / (k - 1)


def log_loss(probs: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    probs = np.asarray(probs, float)
    return -np.log(np.clip(probs[np.arange(len(outcome)), np.asarray(outcome, int)], 1e-15, 1))


def brier(probs: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    probs = np.asarray(probs, float)
    obs = np.zeros_like(probs)
    obs[np.arange(len(outcome)), np.asarray(outcome, int)] = 1.0
    return np.sum((probs - obs) ** 2, axis=1)


def score_table(pred: dict[str, np.ndarray], outcome: np.ndarray) -> pd.DataFrame:
    """Compare plusieurs jeux de probabilités sur les mêmes matchs."""
    rows = []
    for name, p in pred.items():
        m = ~np.isnan(p).any(axis=1)
        rows.append({"modèle": name, "n": int(m.sum()),
                     "RPS": rps(p[m], outcome[m]).mean(),
                     "log-loss": log_loss(p[m], outcome[m]).mean(),
                     "Brier": brier(p[m], outcome[m]).mean(),
                     "accuracy": (p[m].argmax(1) == outcome[m]).mean()})
    return pd.DataFrame(rows).set_index("modèle")


def calibration_table(p: np.ndarray, y: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """Calibration d'une probabilité binaire : fréquence observée par tranche."""
    edges = np.linspace(0, 1, bins + 1)
    b = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    df = pd.DataFrame({"p": p, "y": y, "b": b})
    return df.groupby("b").agg(p_moy=("p", "mean"), freq=("y", "mean"), n=("y", "size"))


# ------------------------------------------------------------------ paris
def bet_returns(stakes, odds, won) -> np.ndarray:
    stakes = np.asarray(stakes, float)
    return np.where(np.asarray(won, bool), stakes * (np.asarray(odds, float) - 1), -stakes)


def bootstrap_roi(stakes, pnl, n_boot: int = 2000, seed: int = 0, block: int | None = None):
    """IC 95 % du ROI par bootstrap (option : blocs pour la dépendance temporelle)."""
    stakes = np.asarray(stakes, float)
    pnl = np.asarray(pnl, float)
    n = len(pnl)
    if n == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    rois = np.empty(n_boot)
    for i in range(n_boot):
        if block:
            starts = rng.integers(0, max(n - block, 1), size=n // block + 1)
            idx = (starts[:, None] + np.arange(block)).ravel()[:n]
        else:
            idx = rng.integers(0, n, n)
        rois[i] = pnl[idx].sum() / stakes[idx].sum()
    return np.percentile(rois, 2.5), np.percentile(rois, 97.5), np.mean(rois <= 0)


def max_drawdown(equity: np.ndarray) -> float:
    equity = np.asarray(equity, float)
    if len(equity) == 0:
        return 0.0
    peak = np.maximum.accumulate(equity)
    return float(np.max((peak - equity) / peak))


def summarize_bets(bets: pd.DataFrame, bankroll0: float = 1000.0) -> dict:
    """bets : colonnes stake, odds, won, (optionnel) clv, date."""
    if len(bets) == 0:
        return {"n_paris": 0}
    pnl = bet_returns(bets["stake"], bets["odds"], bets["won"])
    lo, hi, p_le0 = bootstrap_roi(bets["stake"].values, pnl)
    res = {
        "n_paris": len(bets),
        "mise_tot": float(bets["stake"].sum()),
        "profit": float(pnl.sum()),
        "ROI": float(pnl.sum() / bets["stake"].sum()),
        "ROI_IC95_bas": float(lo), "ROI_IC95_haut": float(hi),
        "p(ROI<=0)": float(p_le0),
        "taux_reussite": float(np.mean(bets["won"])),
        "cote_moy": float(bets["odds"].mean()),
    }
    if "clv" in bets and bets["clv"].notna().any():
        res["CLV_moy"] = float(bets["clv"].mean())
        res["%_CLV>0"] = float((bets["clv"] > 0).mean())
    if "bankroll" in bets:
        res["bankroll_finale"] = float(bets["bankroll"].iloc[-1])
        res["max_drawdown"] = max_drawdown(np.r_[bankroll0, bets["bankroll"].values])
    return res

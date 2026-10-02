"""Gestion de bankroll : Kelly, Kelly fractionné, mise fixe, et Kelly simultané.

Références :
- Kelly (1956), « A New Interpretation of Information Rate ».
- Thorp (2006), « The Kelly criterion in blackjack, sports betting and the stock market ».
- Baker & McHale (2013), « Optimal betting under parameter uncertainty: improving the
  Kelly criterion », Decision Analysis — justifie un Kelly « rétréci » (fractionné).
- Uhrín, Šourek, Hubáček & Železný (2021), « Optimal sports betting strategies in
  practice: an experimental review », IMA J. Management Mathematics.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize


def kelly_fraction(p, odds) -> np.ndarray:
    """Fraction de bankroll optimale f* = (p*o - 1) / (o - 1), bornée à 0."""
    p = np.asarray(p, dtype=float)
    o = np.asarray(odds, dtype=float)
    f = (p * o - 1.0) / (o - 1.0)
    return np.clip(f, 0.0, None)


def stake(p, odds, bankroll: float, method: str = "kelly", fraction: float = 0.25,
          cap: float = 0.05, flat: float = 0.01) -> np.ndarray:
    """Mise en euros selon la méthode choisie.

    - "flat"  : mise fixe = flat * bankroll (indépendante de l'edge)
    - "kelly" : fraction * Kelly, plafonné à cap * bankroll
    - "prop"  : mise proportionnelle à l'edge (p*o-1), plafonnée
    """
    p = np.asarray(p, dtype=float)
    o = np.asarray(odds, dtype=float)
    if method == "flat":
        return np.full_like(p, flat * bankroll)
    if method == "kelly":
        return np.minimum(fraction * kelly_fraction(p, o), cap) * bankroll
    if method == "prop":
        return np.minimum(np.clip(p * o - 1, 0, None) * fraction, cap) * bankroll
    raise ValueError(method)


def simultaneous_kelly(p: np.ndarray, odds: np.ndarray, fraction: float = 1.0,
                       max_total: float = 0.5) -> np.ndarray:
    """Kelly pour plusieurs paris INDÉPENDANTS simultanés (maximise E[log W]).

    Résolution numérique exacte pour n <= 12 (2^n scénarios) ; au-delà on retombe
    sur Kelly individuel normalisé pour respecter max_total.
    """
    p = np.asarray(p, float)
    o = np.asarray(odds, float)
    n = len(p)
    if n == 0:
        return np.array([])
    single = kelly_fraction(p, o)
    if n > 12:
        f = single * fraction
        tot = f.sum()
        return f * (max_total / tot) if tot > max_total else f
    outcomes = np.array(np.meshgrid(*[[0, 1]] * n)).T.reshape(-1, n)
    probs = np.prod(np.where(outcomes == 1, p, 1 - p), axis=1)

    def neg_growth(f):
        w = 1 - f.sum() + np.sum(np.where(outcomes == 1, f * o, 0.0), axis=1)
        return -np.sum(probs * np.log(np.maximum(w, 1e-12)))

    cons = [{"type": "ineq", "fun": lambda f: max_total - f.sum()}]
    res = minimize(neg_growth, x0=np.minimum(single, max_total / n), bounds=[(0, 1)] * n,
                   constraints=cons, method="SLSQP")
    return np.clip(res.x, 0, None) * fraction

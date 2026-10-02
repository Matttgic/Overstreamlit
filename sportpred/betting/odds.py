"""Conversion cotes -> probabilités et suppression de la marge du bookmaker.

Références :
- Štrumbelj (2014), « On determining probability forecasts from betting odds », IJF.
- Clarke, Kovalchik & Ingram (2017), « Adjusting bookmaker's odds to allow for
  overround », American Journal of Sports Science.
- Shin (1993), « Measuring the incidence of insider trading in a market for
  state-contingent claims », Economic Journal.
- Package R `implied` (opisthokonta) : méthodes basic, additive, power, shin, odds_ratio.

Toutes les fonctions acceptent un tableau (n_matchs, n_issues) de cotes décimales et
retournent des probabilités qui somment à 1 par ligne. Les lignes contenant un NaN
renvoient des NaN.
"""
from __future__ import annotations

import numpy as np


def _as2d(odds) -> np.ndarray:
    o = np.asarray(odds, dtype=float)
    return o[None, :] if o.ndim == 1 else o


def overround(odds) -> np.ndarray:
    """Somme des probabilités implicites (1.05 = marge de 5 %)."""
    return np.nansum(1.0 / _as2d(odds), axis=1)


def margin(odds) -> np.ndarray:
    return overround(odds) - 1.0


def devig_multiplicative(odds) -> np.ndarray:
    """Normalisation proportionnelle (méthode « basique »)."""
    inv = 1.0 / _as2d(odds)
    return inv / inv.sum(axis=1, keepdims=True)


def devig_additive(odds) -> np.ndarray:
    """Retire la même quantité à chaque issue (peut donner des proba négatives -> clip)."""
    inv = 1.0 / _as2d(odds)
    k = inv.shape[1]
    p = inv - (inv.sum(axis=1, keepdims=True) - 1.0) / k
    p = np.clip(p, 1e-6, None)
    return p / p.sum(axis=1, keepdims=True)


def devig_power(odds) -> np.ndarray:
    """p_i = (1/o_i)^k avec k tel que la somme vaut 1 (corrige le biais favori/outsider).

    Résolution vectorisée par la méthode de Newton (f convexe décroissante en k).
    """
    inv = 1.0 / _as2d(odds)
    out = np.full_like(inv, np.nan)
    ok = ~np.isnan(inv).any(axis=1)
    x = inv[ok]
    if len(x) == 0:
        return out
    k = np.ones(len(x))
    for _ in range(100):
        xk = x ** k[:, None]
        f = xk.sum(axis=1) - 1.0
        fp = (xk * np.log(x)).sum(axis=1)
        step = f / fp
        k = np.clip(k - step, 0.2, 5.0)
        if np.max(np.abs(step)) < 1e-12:
            break
    p = x ** k[:, None]
    out[ok] = p / p.sum(axis=1, keepdims=True)
    return out


def devig_shin(odds) -> np.ndarray:
    """Méthode de Shin (1993) — modélise une proportion z de parieurs initiés.

    p_i(z) = [sqrt(z^2 + 4(1-z) pi_i^2 / S) - z] / [2(1-z)], z tel que sum p_i = 1
    (Jullien & Salanié 1994 ; Štrumbelj 2014). Bissection vectorisée sur z.
    """
    inv = 1.0 / _as2d(odds)
    out = np.full_like(inv, np.nan)
    ok = ~np.isnan(inv).any(axis=1)
    pi = inv[ok]
    if len(pi) == 0:
        return out
    s = pi.sum(axis=1, keepdims=True)

    def probs(z):
        z = z[:, None]
        return (np.sqrt(z ** 2 + 4 * (1 - z) * pi ** 2 / s) - z) / (2 * (1 - z))

    lo = np.zeros(len(pi))
    hi = np.full(len(pi), 0.99)
    for _ in range(80):
        mid = (lo + hi) / 2
        g = probs(mid).sum(axis=1) - 1.0   # décroissant en z
        lo = np.where(g > 0, mid, lo)
        hi = np.where(g > 0, hi, mid)
    p = probs((lo + hi) / 2)
    p = np.where(s <= 1.0, pi / s, p)
    out[ok] = p / p.sum(axis=1, keepdims=True)
    return out


def devig_odds_ratio(odds) -> np.ndarray:
    """Méthode « odds ratio » (Cheung 2015) : odds(p_i) = odds(1/o_i) / c. Bissection vectorisée."""
    inv = 1.0 / _as2d(odds)
    out = np.full_like(inv, np.nan)
    ok = ~np.isnan(inv).any(axis=1)
    x = inv[ok]
    if len(x) == 0:
        return out
    lo = np.full(len(x), 0.2)
    hi = np.full(len(x), 10.0)
    for _ in range(80):
        c = (lo + hi) / 2
        g = (x / (c[:, None] + x - c[:, None] * x)).sum(axis=1) - 1.0  # décroissant en c
        lo = np.where(g > 0, c, lo)
        hi = np.where(g > 0, hi, c)
    c = ((lo + hi) / 2)[:, None]
    p = x / (c + x - c * x)
    out[ok] = p / p.sum(axis=1, keepdims=True)
    return out


DEVIG = {
    "multiplicative": devig_multiplicative,
    "additive": devig_additive,
    "power": devig_power,
    "shin": devig_shin,
    "odds_ratio": devig_odds_ratio,
}


def devig(odds, method: str = "power") -> np.ndarray:
    return DEVIG[method](odds)


def fair_odds(odds, method: str = "power") -> np.ndarray:
    return 1.0 / devig(odds, method)


def expected_value(prob, odds) -> np.ndarray:
    """Espérance de gain pour 1 € misé : p * o - 1."""
    return np.asarray(prob) * np.asarray(odds) - 1.0

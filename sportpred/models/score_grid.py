"""Grille des scores d'un match de football, calée sur les cotes sans marge de Pinnacle.

Sert à donner une probabilité juste à n'importe quel pari fondé sur le score final
(victoire, nul, écart, total, les deux équipes marquent, combinés « X gagne et plus de 2,5
buts »…) et, avec le modèle buteurs, aux combinés avec un joueur (« X gagne et Y marque »).

Grille : deux lois de Poisson (λ_dom, λ_ext) avec la correction de Dixon-Coles (ρ) sur les
petits scores, ajustées pour reproduire exactement P(dom), P(nul) et P(plus de 2,5 buts).
Joueurs : sachant que l'équipe marque k buts, chaque but est un but « de joueur » avec
probabilité 1 − c.s.c., attribué au joueur i avec probabilité s_i (modèle buteurs) ; donc
P(aucun des joueurs J ne marque | k) = (1 − (1 − og)·Σ_{i∈J} s_i)^k.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import poisson

MAXG = 11


def dc_grid(lh: float, la: float, rho: float = 0.0, maxg: int = MAXG) -> np.ndarray:
    k = np.arange(maxg)
    g = np.outer(poisson.pmf(k, lh), poisson.pmf(k, la))
    if rho:
        g[0, 0] *= 1 - lh * la * rho
        g[0, 1] *= 1 + lh * rho
        g[1, 0] *= 1 + la * rho
        g[1, 1] *= 1 - rho
    g = np.clip(g, 0, None)
    return g / g.sum()


def outcome_probs(g: np.ndarray) -> tuple[float, float, float]:
    return float(np.tril(g, -1).sum()), float(np.trace(g)), float(np.triu(g, 1).sum())


def p_over(g: np.ndarray, line: float) -> float:
    n = g.shape[0]
    tot = np.add.outer(np.arange(n), np.arange(n))
    k = np.floor(line)
    if line == k:                                        # ligne entière : remboursé si égal
        return float(g[tot > k].sum() / max(1 - g[tot == k].sum(), 1e-12))
    return float(g[tot > line].sum())


def fit_grid(p_home: float, p_draw: float, p_over25: float | None = None,
             total_lines: dict[float, float] | None = None) -> tuple[np.ndarray, dict]:
    """Grille qui reproduit au mieux P(dom), P(nul) et les P(plus de x) connues."""
    lines = dict(total_lines or {})
    if p_over25 is not None:
        lines.setdefault(2.5, p_over25)
    if not lines:
        lines = {2.5: 0.5}

    def res(x):
        lh, la, rho = np.exp(x[0]), np.exp(x[1]), x[2]
        g = dc_grid(lh, la, rho)
        h, d, _ = outcome_probs(g)
        r = [h - p_home, d - p_draw]
        r += [0.7 * (p_over(g, ln) - po) for ln, po in lines.items()]
        return r

    sol = least_squares(res, x0=[np.log(1.4), np.log(1.1), -0.05], bounds=([-3, -3, -0.3], [2, 2, 0.3]))
    lh, la, rho = float(np.exp(sol.x[0])), float(np.exp(sol.x[1])), float(sol.x[2])
    return dc_grid(lh, la, rho), {"lam_h": lh, "lam_a": la, "rho": rho, "err": float(np.abs(sol.fun).max())}


# ------------------------------------------------------------------ événements sur le score
def ev_prob(g: np.ndarray, cond) -> float:
    """Probabilité d'un événement `cond(h, a) -> bool` (tableaux numpy)."""
    n = g.shape[0]
    h, a = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    return float(g[cond(h, a)].sum())


def players_prob(g: np.ndarray, legs: list[tuple[str, float, int]], og: float = 0.028, cond=None) -> float:
    """P(score vérifie `cond` ET chaque joueur marque au moins `k` buts).

    legs : (équipe 'h' ou 'a', part s_i du joueur dans son équipe, k buts minimum (1 ou 2)).
    Joueurs d'une même équipe : attribution multinomiale exacte (inclusion-exclusion) pour
    k = 1 ; « 2 buts ou plus » traité seul par équipe (approximation au-delà)."""
    n = g.shape[0]
    h, a = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    mask = cond(h, a) if cond is not None else np.ones_like(g, dtype=bool)
    tot = np.ones_like(g)
    for side in ("h", "a"):
        k_team = h if side == "h" else a
        ls = [(s, k) for t, s, k in legs if t == side]
        if not ls:
            continue
        if all(k == 1 for _, k in ls):
            q = [(1 - og) * s for s, _ in ls]
            p = np.zeros_like(g)                    # P(tous marquent | k) par inclusion-exclusion
            for r in range(len(q) + 1):
                for sub in combinations(q, r):
                    p += (-1) ** r * (1 - sum(sub)) ** k_team
            tot *= p
        else:
            for s, k in ls:
                q = (1 - og) * s
                p0 = (1 - q) ** k_team
                p1 = k_team * q * (1 - q) ** np.maximum(k_team - 1, 0)
                tot *= 1 - p0 - (p1 if k >= 2 else 0)
    return float((g * tot * mask).sum())

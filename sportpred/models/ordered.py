"""Régression logistique ordonnée : transforme un score de force (différence d'Elo,
différence de buts attendue...) en probabilités 1N2.

P(extérieur) = σ(c1 - β·x)
P(nul)       = σ(c2 - β·x) - σ(c1 - β·x)
P(domicile)  = 1 - σ(c2 - β·x)

Utilisé par Hvattum & Arntzen (2010) pour les notes Elo et par Constantinou & Fenton
(2013) pour les pi-ratings. Ajustement par maximum de vraisemblance (scipy).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit


class OrderedLogit:
    def __init__(self):
        self.beta = 1.0
        self.c1 = -0.5
        self.c2 = 0.5

    @staticmethod
    def _probs(params, x):
        beta, c1, d = params
        c2 = c1 + np.exp(d)
        pa = expit(c1 - beta * x)
        pd_ = expit(c2 - beta * x) - pa
        ph = 1.0 - pa - pd_
        return np.column_stack([ph, pd_, pa])

    def fit(self, x, y, w=None):
        """x : score (n,), y : 0=domicile, 1=nul, 2=extérieur."""
        x = np.asarray(x, float)
        y = np.asarray(y, int)
        w = np.ones_like(x) if w is None else np.asarray(w, float)
        m = ~np.isnan(x)
        x, y, w = x[m], y[m], w[m]
        scale = np.nanstd(x) or 1.0

        def nll(params):
            p = self._probs(params, x)
            return -np.sum(w * np.log(np.clip(p[np.arange(len(y)), y], 1e-12, None)))

        res = minimize(nll, x0=[1.0 / scale, -0.8, 0.0], method="L-BFGS-B")
        self.beta, self.c1, d = res.x
        self.c2 = self.c1 + np.exp(d)
        self._params = res.x
        return self

    def predict_proba(self, x):
        return self._probs(self._params, np.asarray(x, float))
